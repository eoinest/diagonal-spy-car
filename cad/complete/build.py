"""Complete camera-free assembly. Blender 5.x, millimetre coordinates.

blender --background --python-exit-code 1 --python cad/complete/build.py
Use -- --skip-renders for mesh/fit validation and .blend output only.
"""
import bpy, bmesh, json, math, struct, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
P=json.loads((OUT/'parameters.json').read_text())
sys.path.insert(0,str(OUT));sys.path.insert(0,str(OUT.parent/'rolling'))
from mesh_checks import validate_stl
from electronics_models import build as build_electronics
from battery_views import build as build_battery_views
base_path=(OUT/P['base_model']).resolve()
if '--base-model' in sys.argv:
    base_path=Path(sys.argv[sys.argv.index('--base-model')+1]).resolve()
base_sha256=hashlib.sha256(base_path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(base_path))
scene=bpy.context.scene;scene.name='01 ASSEMBLED'
for o in list(bpy.data.objects):
    if o.type in ('FONT','CAMERA','LIGHT') or o.name=='Studio floor' or 'CONTEXT ONLY' in o.name or 'UNDESIGNED' in o.name or 'fit coupon' in o.name.lower():
        bpy.data.objects.remove(o,do_unlink=True)
for co in list(bpy.data.collections):
    if not len(co.objects):bpy.data.collections.remove(co)
COL={}
for n in ['PRINT - electronics deck','PRINT - battery bands','PRINT - powered wheels','REFERENCE - factory horns','REFERENCE - harness and small parts','STUDIO']:
    co=bpy.data.collections.new(n);scene.collection.children.link(co);COL[n]=co
PRINT='PRINT - electronics deck';PART='REFERENCE - harness and small parts'
def mat(n,rgb,metal=0):
    m=bpy.data.materials.new(n);m.diffuse_color=(*rgb,1);m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*rgb,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=.42
    return m
M={'deck':mat('Printed deck - warm orange',(.84,.19,.035)), 'band':mat('Printed TPU retention bands',(.025,.16,.15)),
   'wheel':mat('Printed drive wheels - graphite',(.045,.075,.10)), 'horn':mat('Factory nylon horn',(.75,.78,.76)),
   'red':mat('Positive wire',(.66,.012,.025)), 'black':mat('Ground wire',(.013,.018,.022)),
   'orange':mat('GPIO16 left signal',(.95,.42,.015)), 'blue':mat('GPIO18 right signal',(.015,.28,.8)),
   'green':mat('Battery sensing signal',(.02,.5,.22)), 'white':mat('Silkscreen',(.92,.96,.93)),
   'metal':mat('Connector contacts and leads',(.55,.63,.68),.8), 'gold':mat('Gold contacts',(.75,.48,.07),.7),
   'yellow':mat('XT30 plastic',(.98,.56,.015)), 'pcb':mat('Sensing perfboard',(.15,.34,.22)),
   'tan':mat('Resistor ceramic',(.59,.52,.35)), 'pad':mat('Battery protective foam',(.025,.035,.04))}
groups={'base':[], 'deck':[], 'battery_band':[], 'drive_left':[], 'drive_right':[], 'harness':[]}
def put(o,name,col=PRINT,material='deck',group=None):
    o.name=name
    for co in list(o.users_collection):co.objects.unlink(o)
    COL[col].objects.link(o)
    if material:o.data.materials.clear();o.data.materials.append(M[material])
    if group:groups.setdefault(group,[]).append(o);o['assembly_group']=group
    return o
def clean(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
    isolated=[f for f in bm.faces if all(len(e.link_faces)==1 for e in f.edges)]
    if isolated:bmesh.ops.delete(bm,geom=isolated,context='FACES')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()
def box(n,loc,dims,col=PRINT,material='deck',bevel=0,group=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=put(bpy.context.object,n,col,material,group);o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mo=o.modifiers.new('Rounded edges','BEVEL');mo.width=bevel;mo.segments=3;bpy.ops.object.modifier_apply(modifier=mo.name)
    return o
def cyl(n,loc,r,depth,col=PRINT,material='deck',axis='Z',group=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=depth,location=loc);o=put(bpy.context.object,n,col,material,group)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    elif axis=='Y':o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def boolean(o,t,op='DIFFERENCE',remove=True):
    bpy.context.view_layer.objects.active=o;mo=o.modifiers.new(op,'BOOLEAN');mo.operation=op;mo.solver='EXACT';mo.object=t
    bpy.ops.object.modifier_apply(modifier=mo.name)
    if remove:bpy.data.objects.remove(t,do_unlink=True)
    clean(o);return o
def union(o,t):return boolean(o,t,'UNION')
def label(n,body,loc,size,group='harness'):
    cu=bpy.data.curves.new(n,'FONT');cu.body=body;cu.size=size;cu.extrude=.005;cu.align_x='CENTER';cu.align_y='CENTER'
    o=bpy.data.objects.new(n,cu);COL[PART].objects.link(o);o.location=loc;cu.materials.append(M['white']);o['assembly_group']=group;groups.setdefault(group,[]).append(o);return o
def wire(n,pts,color='red',radius=.55,group='harness'):
    cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=radius;cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for b,p in zip(sp.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(n,cu);COL[PART].objects.link(o);cu.materials.append(M[color]);o['assembly_group']=group;o['geometry_status']='Illustrative service-loop routing; validate bend radii and solder clearances';groups.setdefault(group,[]).append(o);return o
def bounds(o):
    p=[o.matrix_world@Vector(v) for v in o.bound_box];return [min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]
def overlap(a,b):
    aa,ab=bounds(a);ba,bb=bounds(b)
    if any(min(ab[i],bb[i])-max(aa[i],ba[i])<=.001 for i in range(3)):return 0
    dup=a.copy();dup.data=a.data.copy();scene.collection.objects.link(dup);boolean(dup,b,'INTERSECT',False)
    bm=bmesh.new();bm.from_mesh(dup.data);v=abs(bm.calc_volume(signed=True));bm.free();mesh=dup.data;bpy.data.objects.remove(dup,do_unlink=True);bpy.data.meshes.remove(mesh);return v

# Preserve the existing one-piece chassis, servo clips and printed bearing axles.
for o in list(scene.objects):
    if o.type in ('MESH','CURVE','FONT'):
        o['assembly_group']='base';groups['base'].append(o)
chassis=bpy.data.objects['rolling_chassis']
deck=box('Electronics deck - removable four-finger carrier',(0,0,26.1),(52,76,2.2),bevel=.5,group='deck')
# Four independent compliant end fingers, bearing seats and underside hooks.
for x in (-11.5,11.5):
    for side in (-1,1):
        union(deck,box('End spring finger',(x,side*34.2,13.1),(4,1.6,28.2)))
        union(deck,box('Base-top seating ledge',(x,side*32.8,3),(4,3.0,1.2)))
        union(deck,box('Under-base retaining hook',(x,side*32.9,-.6),(4,2.6,.8)))
# Side stops at the ends only; they avoid axle blocks and do not tie the spring fingers together.
for sx in (-1,1):
    for sy in (-1,1):union(deck,box('End-local lateral locator',(sx*15.8,sy*32.2,14.8),(1.2,3.0,24.8)))
# Wheel-side ventilation / lightweighting slots between retaining structures.
for x in (-20,20):
    for y in (-8,2):boolean(deck,box('Deck vent slot',(x,y,26.1),(2,5,5),bevel=.4))
# PCB rails: controlled vertical gap, slip-fit reference, no reliance on unknown hole centers.
def pcb_rails(cx,cy,length,width,bottom,name,antenna=False):
    for sy in (-1,1):
        yy=cy+sy*(width/2+.9)
        # Antenna half remains over an open cutout, not a wide plastic shelf.
        xx=cx-3 if antenna else cx
        ll=length-11 if antenna else length-3
        union(deck,box(name+' lower edge seat',(xx,cy+sy*(width/2-.25),(27.1+bottom)/2),(ll,2.5,bottom-27.1)))
        union(deck,box(name+' side guide',(xx,yy,(27.1+bottom+2.7)/2),(ll,1.2,bottom+2.7-27.1)))
        union(deck,box(name+' upper retention rail',(xx,cy+sy*(width/2+.25),bottom+2.25),(ll,2.5,.9)))
    # Far-end stop, at the short PCB edge and only outside the component zone.
    for sy in (-1,1):union(deck,box(name+' end stop',(cx+length/2+.5,cy+sy*(width/2-.7),(27.1+bottom+2.55)/2),(1.0,2.2,bottom+2.55-27.1)))
pcb_rails(0,-25,43,21,29.2,'Buck')
pcb_rails(0,23,34.3,25.4,29.2,'S2',True)
# Open antenna end of board (after -90 rotation antenna points +X).
boolean(deck,box('Antenna free-space window',(19,23,26.1),(18,21,5)))
# Battery cradle: nominal pouch plus 0.6 mm per side and padding, no sharp clamp on the pouch.
for sy in (-1,1):union(deck,box('Battery long-side low fence',(0,-2.5+sy*9.7,28.0),(49.2,1.2,1.8)))
for sx in (-1,1):
    for sy in (-1,1):union(deck,box('Battery padded end stop',(sx*25,-2.5+sy*5.5,28.0),(1.2,4,1.8)))
foam=box('Battery insulating foam - 0.8 mm',(0,-2.5,27.6),(48,17,.8),PART,'pad',bevel=.15,group='battery')
# Two separate printable TPU loops; loose envelope, not a high-force pouch clamp.
bands=[]
for x in (-7.5,7.5):
    band=box('TPU battery keeper '+str(x),(x,-2.5,33.1),(4,21.0,18.2),'PRINT - battery bands','band',bevel=.5,group='battery_band')
    boolean(band,box('Band cavity',(x,-2.5,33.1),(6,19.0,16.2),bevel=.5))
    # Ring cavity spansZ25..41.2; the loop passes below the deck and above the battery.
    bands.append(band)
    for yy in (-12.5,7.5):boolean(deck,box('Keeper band slot',(x,yy,26.5),(4.6,1.7,6),bevel=.3))

# Powered wheel with conditional, keyed factory horn pocket and integrated retaining lips.
drive_prints=[];horn_objects=[]
for side,y,grp in [(-1,20,'drive_left'),(1,-20,'drive_right')]:
    wc='PRINT - powered wheels';hc='REFERENCE - factory horns'
    wheel=cyl('Powered wheel '+grp,(side*22,y,8.5),15,5,wc,'wheel','X',grp)
    boolean(wheel,cyl('Screwdriver access',(side*22,y,8.5),2.4,8,axis='X'))
    # The hub joins the inner face; factory horn is captive behind the tread.
    hub=box('Keyed horn pocket outer',(side*18.5,y,8.5),(3.0,23,8),wc,'wheel',bevel=.6)
    union(wheel,hub)
    pocket=box('Assumed 20x5 horn pocket',(side*18.15,y,8.5),(2.5,20.5,5.5),bevel=.25)
    boolean(wheel,pocket)
    boolean(wheel,cyl('Horn hub relief',(side*17.4,y,8.5),3.75,3.8,axis='X'))
    # Relieved 8 mm tongues: axial deflection space behind each arm and separate free-end gaps.
    for s in (-1,1):
        boolean(wheel,box('Horn tongue back relief',(side*18.9,y+s*6.4,12.0),(2.6,7.8,2.0)))
        boolean(wheel,box('Horn tongue free-end relief',(side*18.1,y+s*10.5,12.0),(4.4,.8,2.0)))
        union(wheel,box('Horn retaining tongue',(side*17.0,y+s*6.0,11.8),(1.2,8.0,1.0)))
        union(wheel,box('Horn retaining lip',(side*16.6,y+s*8.7,11.0),(.6,2.0,1.0),bevel=.15))
    # Small flat axial grooves add grip without increasing wheel diameter.
    for angle in range(0,360,30):
        a=math.radians(angle);tool=box('Tread groove',(side*22,y+15*math.sin(a),8.5+15*math.cos(a)),(7,1.0,.7))
        tool.rotation_euler[0]=-a;boolean(wheel,tool)
    wheel.data.materials.clear();wheel.data.materials.append(M['wheel'])
    for face in wheel.data.polygons:face.material_index=0
    drive_prints.append(wheel)
    h=box('Owned factory horn - unmeasured double arm',(side*18.1,y,8.5),(2.0,20,5),hc,'horn',bevel=.2,group=grp);horn_objects.append(h)
    # No guessed spline teeth: this volume identifies the original fitted hub only.
    h=cyl('Factory horn hub - spline not modeled',(side*16.8,y,8.5),3.5,2.6,hc,'horn','X',grp);horn_objects.append(h)
    screw=cyl('Servo supplied center screw - reference only',(side*19.35,y,8.5),1.9,.4,hc,'metal','X',grp)
    screw['geometry_status']='Factory hardware belonging to the owned servo; dimensions unmeasured'

# Manufacturer/photograph informed models, transformed into single-layer packing.
E=build_electronics(P)
egroups=E.get('groups',E)
terminals=E.get('terminals',{})
for name in ('battery','buck','s2'):
    g=egroups[name];center=P[name].get('center_xy',P[name].get('center'))[:2]
    T=Matrix.Translation(Vector((*center,0)))@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(Vector((-center[0],-center[1],0)))
    for o in g:o.matrix_world=T@o.matrix_world;o['assembly_group']=name
    groups.setdefault(name,[]).extend(g)
    if name in terminals:
        terminals[name]={k:list(T@Vector(v)) for k,v in terminals[name].items()}

# Clearance pockets for solder on the lower PCB pads; board-edge rails avoid electrical contacts.
bpy.context.view_layer.update()
for group in ('buck','s2'):
    for o in groups[group]:
        if o.type!='MESH':continue
        lo,hi=bounds(o)
        if ('through-pad' in o.name or 'solder pad' in o.name) and lo[2]<29.2:
            boolean(deck,cyl('Underside solder clearance',((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,28.6),1.15,1.5))
        if 'switch body' in o.name or 'side actuator' in o.name:
            boolean(deck,box('Accessible S2 button relief',tuple((lo[i]+hi[i])/2 for i in range(3)),tuple(hi[i]-lo[i]+.7 for i in range(3))))

# Connector packaging references: battery unplug remains accessible over the pouch.
connector=box('XT30 battery connector - reference envelope',(0,-3.8,42.7),(10.2,12.4,5.2),PART,'yellow',bevel=.55,group='harness')
mate=box('XT30 harness mate - reference envelope',(0,6.4,42.7),(10.2,8,5.2),PART,'yellow',bevel=.4,group='harness')
for xx in (-2.5,2.5):
    cyl('XT30 contact',(xx,2.4,42.7),1.0,2,PART,'gold','Y',group='harness')
label('Unplug label','UNPLUG',(0,-3,45.35),1.6)
balance=box('3-pin balance plug - XH reference',(-18,4.6,44),(9.8,5.7,7.75),PART,'white',bevel=.3,group='harness')
for xx in (-20.5,-18,-15.5):
    boolean(balance,box('Balance socket opening',(xx,2.0,44.6),(1.4,2.0,3),PART,None))
wire('Battery positive lead',[terminals['battery']['positive'],(-25,-5,40),(-15,-8,44),(-2.5,-10,42.7)],'red',.75)
wire('Battery negative lead',[terminals['battery']['negative'],(-25,1,40),(-15,-7,44),(2.5,-10,42.7)],'black',.75)
for idx,col in enumerate(('black','white','red')):wire('Balance cell tap '+str(idx),[terminals['battery']['balance_lead_exit'],(-25,2+idx,38),(-20,6+idx*.3,44),(-18+(idx-1)*2.5,2.0,44.6)],col,.35)
# Bulk capacitor and fuse occupy separate underdeck cradles, away from the pouch.
bulk=cyl('220uF 10V external bulk capacitor',(15,0,21.5),3.25,9,PART,'black','Y',group='harness')
cyl('Bulk capacitor metal lid',(15,4.52,21.5),3.1,.1,PART,'metal','Y',group='harness')
cradle=cyl('Bulk capacitor C cradle',(15,0,21.5),4.15,7.8,axis='Y')
boolean(cradle,cyl('Bulk cavity',(15,0,21.5),3.55,10,axis='Y'))
boolean(cradle,box('Bulk insertion opening',(15,0,17.5),(3.8,11,5)))
union(deck,cradle)
for yy in (-4.85,4.85):union(deck,box('Bulk axial stop',(15,yy,24.5),(4,.6,1.8)))
for loc,name in [((15,-5.7,21),'100nF bus bypass')]:box(name,loc,(2,1,2),PART,'tan',bevel=.15,group='harness')
fuse=box('Input fuse - unselected small leaded package',(-15,0,21),(3.5,8,4),PART,'green',bevel=.4,group='harness')
for xx in (-17.35,-12.65):union(deck,box('Fuse holder side',(xx,0,21.9),(1,9,6.6)))
for yy in (-4.65,4.65):union(deck,box('Fuse holder end stop',(-15,yy,22.2),(5.7,1.0,6.0)))
for xx in (-16.5,-13.5):union(deck,box('Fuse retaining lip',(xx,0,18.5),(1.7,8,.6)))
jp=box('J_PWR removable logic feed',(0,8,34),(5,4,3),PART,'black',bevel=.3,group='harness')
# Routed named nets use exact modeled terminal positions where supplied.
def terminal(group,key,fallback):return terminals.get(group,{}).get(key,fallback)
bp=terminal('buck','IN+',[ -19.5,-17.0,30.85]);bn=terminal('buck','IN-',[ -19.5,-33.0,30.85])
bo=terminal('buck','OUT+',[19.5,-17,30.85]);bg=terminal('buck','OUT-',[19.5,-33,30.85])
wire('VBAT positive through inline fuse',[(-2.5,10.4,42.7),(17,-9,39),(-17,-10,31),(-15,0,21),(-19,-11,28),bp],'red',.65)
wire('VBAT negative to buck',[(2.5,10.4,42.7),(20,-7,42),(24,-25,35),bn],'black',.65)
starplus=(21,-10.5,30.8);starminus=(23,-10.5,30.8)
wire('Buck OUT+ to star',[bo,(22,-15,32),starplus],'red',.65)
wire('Buck OUT- to star',[bg,(24,-26,33),starminus],'black',.65)
wire('Bulk positive to distribution',[(14,-4.5,21.5),(17,-6,24),starplus],'red',.4)
wire('Bulk negative to distribution',[(16,-4.5,21.5),(18,-6,24),starminus],'black',.4)
sv=terminal('s2','VBUS',[-9.7,10.57,30.85]);sg=terminal('s2','GND',[-7.16,10.57,30.85])
wire('5V bus through removable J_PWR',[starplus,(15,7.8,33),(0,8,34),sv],'red',.45)
wire('Common logic ground',[starminus,(16,9,32),sg],'black',.45)
for side,y,pin,color in [(-1,20,'GPIO16','orange'),(1,-20,'GPIO18','blue')]:
    # Cable exits near the opposite motor end; wire routes are schematic service loops.
    exitpt=(side*8,y-10*(1 if y>0 else -1),9)
    target=terminal('s2',pin,[-4.62 if pin=='GPIO16' else -2.08,10.57,30.85])
    lane=16*side
    wire(pin+' signal to servo',[target,(lane,7,34),(lane,4,20),exitpt],color,.35)
    wire('5V servo '+pin,[starplus,(17,0,31),(lane,0,20),(exitpt[0],exitpt[1]+1,exitpt[2])],'red',.45)
    wire('GND servo '+pin,[starminus,(18,1,31),(lane+1,0,20),(exitpt[0],exitpt[1]+2,exitpt[2])],'black',.45)
# Final loop clearances also pass through later-added underside walls and PCB fences.
for x in (-7.5,7.5):
    tool=box('TPU loop clearance outer',(x,-2.5,33.1),(4.64,21.6,18.8),bevel=.5)
    boolean(tool,box('TPU loop clearance cavity',(x,-2.5,33.1),(6,18.4,15.6),bevel=.5))
    boolean(deck,tool)

clean(deck)
# Printable exports. Nominal mating features remain conditional on physical fit.
def export(o,filename,axis=None):
    mesh=o.data.copy();mesh.transform(o.matrix_world)
    if axis=='X':mesh.transform(Matrix.Rotation(math.pi/2,4,'Y'))
    verts=[v.co for v in mesh.vertices];lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
    shift=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for v in mesh.vertices:v.co=Vector(tuple(round(a,5) for a in v.co+shift))
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.calc_loop_triangles()
    path=OUT/filename
    with path.open('wb') as f:
        f.write(b'Diagonal spy car v0.6 / mm / assumed fit'.ljust(80,b'\0'));f.write(struct.pack('<I',len(mesh.loop_triangles)))
        for t in mesh.loop_triangles:
            vs=[mesh.vertices[i].co for i in t.vertices];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]).normalized();f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
    bpy.data.meshes.remove(mesh);result=validate_stl(path);result['file']=filename;return result
prints=[(deck,'electronics-deck.stl',None),(bands[0],'battery-band-tpu.stl','X'),(drive_prints[0],'powered-wheel-left.stl','X'),(drive_prints[1],'powered-wheel-right.stl','X')]
report={'revision':P['revision'],'units':'mm','scope':'Nominal rigid-part fit. No insertion, strength, thermal or routed-wire collision validation.'}
report['base_model_sha256']=base_sha256
report['stl']=[export(*x) for x in prints]
assert all(x['valid'] for x in report['stl']),report['stl']
bpy.context.view_layer.update()
# Check complete new rigid printed deck against all inherited rigid hardware.
collisions=[]
for a in [deck]+bands+drive_prints:
    for b in groups['base']+groups.get('battery',[])+groups.get('buck',[])+groups.get('s2',[])+horn_objects:
        if b.type!='MESH':continue
        vol=overlap(a,b)
        if vol>.03:collisions.append({'a':a.name,'b':b.name,'volume_mm3':round(vol,4)})
# New printed parts against one another and rigid accessory packages.
newprints=[deck]+bands+drive_prints
for i,a in enumerate(newprints):
    for b in newprints[i+1:]:
        vol=overlap(a,b)
        if vol>.03:collisions.append({'a':a.name,'b':b.name,'volume_mm3':round(vol,4)})
rigid_aux=[o for o in groups['harness'] if o.type=='MESH' and any(t in o.name for t in ('external bulk','Input fuse','100nF','J_PWR','XT30 battery','XT30 harness','balance plug'))]
for a in rigid_aux:
    for b in newprints+groups['base']+groups['battery']+groups['buck']+groups['s2']:
        if b.type!='MESH':continue
        vol=overlap(a,b)
        if vol>.03:collisions.append({'a':a.name,'b':b.name,'volume_mm3':round(vol,4)})
report['rigid_mount_collisions']=collisions
report['nominal_clearances_mm']={'deck_to_wheel_top':1.5,'underhook_to_base_bottom':.2,'pcb_to_deck_top':2.0,'band_bottom_to_wheel_top':.5}
# Measure the finished battery geometry in world coordinates, excluding foam,
# external leads and connectors. Check full-size placement and holder clearance.
pack=[o for o in groups['battery'] if o.name.startswith('Battery •')]
pack_lo=[min(bounds(o)[0][i] for o in pack) for i in range(3)]
pack_hi=[max(bounds(o)[1][i] for o in pack) for i in range(3)]
pack_size=[pack_hi[i]-pack_lo[i] for i in range(3)]
expected=[P['battery'][k] for k in ('length','width','height')]
assert all(abs(a-b)<.01 for a,b in zip(pack_size,expected)),(pack_size,expected)
report['battery_geometry']={'finished_pack_xyz_mm':pack_size,'expected_xyz_mm':expected,
    'min':pack_lo,'max':pack_hi,'tolerance_mm':.01,
    'source':'https://www.lumenier.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30',
    'excludes':'Foam, leads and connectors; nominal supplier size, not physical metrology',
    'foam_top_gap_mm':pack_lo[2]-bounds(foam)[1][2],
    'band_inner_top_gap_mm':41.2-pack_hi[2],
    'band_side_gap_per_side_mm':(19-pack_size[1])/2,
    'end_stop_gap_per_side_mm':(48.8-pack_size[0])/2}
report['terminals']=terminals
report['unverified']=['Owned buck dimensions and IC','Servo geometry and supplied horn','Clip insertion and fatigue','PCB underside parts and solder clearance','Friction retention of PCB rails and bearing fits','Wire service loops and small-package part selection']
report['component_inventory']={k:len(v) for k,v in groups.items()}
allparts=[o for o in scene.objects if o.type in ('MESH','CURVE','FONT') and not o.hide_render]
lo=[min(bounds(o)[0][i] for o in allparts) for i in range(3)];hi=[max(bounds(o)[1][i] for o in allparts) for i in range(3)]
report['assembly_bounds_mm']={'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
assert not collisions,collisions

# Studio: assembled, top and side cameras, plus a separate exploded scene.
floor=box('Studio floor',(0,0,-7.1),(2000,2000,1),col='STUDIO',material='pad')
for old in list(scene.world.node_tree.nodes) if scene.world and scene.world.use_nodes else []:pass
scene.world.color=(.22,.22,.22)
def camera(n,loc,target,scale):
    data=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,data);COL['STUDIO'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;return o
hero=camera('Camera - assembly',(-70,-165,150),(0,0,20),128)
top=camera('Camera - plan',(0,0,190),(0,0,0),105)
sidecam=camera('Camera - side',(-180,0,36),(0,0,20),112)
for n,loc,power,size in [('Key',(-70,-90,150),260000,95),('Fill',(90,-10,100),150000,80),('Rim',(0,110,110),220000,70)]:
    d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(n,d);COL['STUDIO'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,15))-o.location).to_track_quat('-Z','Y').to_euler()
scene.camera=hero;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene['design_status']='Complete nominal packaging prototype. Published outlines plus explicitly assumed clone and fit details.'
scene['source_parameters']='cad/complete/parameters.json'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=135;area.spaces.active.region_3d.view_location=Vector((0,0,20));area.spaces.active.region_3d.view_rotation=hero.rotation_euler.to_quaternion()
bpy.ops.object.select_all(action='DESELECT');deck.select_set(True);bpy.context.view_layer.objects.active=deck
# Separate exploded scene keeps the assembled file usable without moving objects back.
bpy.ops.scene.new(type='FULL_COPY');exploded=bpy.context.scene;exploded.name='02 EXPLODED'
offsets={'deck':(0,0,30),'battery':(-30,0,52),'battery_band':(-30,0,60),'buck':(32,-6,48),'s2':(25,20,72),'harness':(0,0,25),'drive_left':(-14,0,0),'drive_right':(14,0,0)}
for o in exploded.objects:
    g=o.get('assembly_group')
    if g in offsets:
        off=offsets[g]
        if g=='harness' and any(t in o.name for t in ('XT30','balance','Balance','Unplug','J_PWR')):off=(-32,30,70)
        o.location+=Vector(off)
    if g=='harness' and o.type=='CURVE':o.hide_render=True;o.hide_set(True)
exploded.camera.data.ortho_scale=210;exploded.camera.location=(-150,-185,185);exploded.camera.rotation_euler=(Vector((0,0,52))-exploded.camera.location).to_track_quat('-Z','Y').to_euler()
battery_scene,battery_camera=build_battery_views(scene)
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'complete-spy-car.blend'),compress=True)
if '--skip-renders' not in sys.argv:
    for cam,file in [(hero,'assembly.png'),(top,'top.png'),(sidecam,'side.png')]:
        scene.camera=cam;scene.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=exploded;exploded.render.filepath=str(OUT/'exploded.png');bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=battery_scene;battery_scene.render.filepath=str(OUT/'battery-dimensions.png');bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=scene;scene.camera=hero
print('COMPLETE_BUILD_OK',json.dumps(report))
