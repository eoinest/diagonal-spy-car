"""Original parametric Blender CAD; mm coordinates. Run with Blender --background --python cad/build.py.
Nominal component envelopes, explicitly NOT metrology-grade purchased-part replicas.
"""
import bpy, math, json, os, sys, struct
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT/'cad/parameters.json').read_text())
S=P['servo']; W=P['wheel']; B=P['battery']; C=P['chassis']; E=P['s2_mini']; R=P['regulator']; K=P['camera']
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=.001
scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='CYCLES'; scene.cycles.samples=40
scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.world.color=(.19,.19,.19)
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
COL={}
for name in ['PRINTED • prototype','HARDWARE • nominal reference','DETAIL • illustrative','STUDIO']:
    COL[name]=bpy.data.collections.new(name); scene.collection.children.link(COL[name])

def mat(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    return m
M={
'body':mat('Graphite PETG',(.065,.10,.12)), 'accent':mat('Safety amber PETG',(.95,.35,.035)),
'blue':mat('Servo case — illustrative',(.025,.07,.23)), 'pcb':mat('Violet S2 board',(.28,.055,.49)),
'reg':mat('Blue regulator board',(.015,.15,.38)), 'gold':mat('Brass',(.64,.43,.12),.75),
'silver':mat('Brushed metal',(.55,.61,.68),.8), 'black':mat('Rubber / IC',(.012,.018,.021)),
'white':mat('Markings',(.87,.92,.93)), 'battery':mat('Battery wrap',(.08,.08,.09)),
'red':mat('Positive lead',(.64,.025,.02)), 'glass':mat('Camera glass',(.015,.10,.14),.5,.12),
'floor':mat('Studio surface',(.17,.20,.22))}

def put(o,name,m='body',col='DETAIL • illustrative'):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    COL[col].objects.link(o)
    if m: o.data.materials.append(M[m])
    return o

def box(name,loc,dim,m='body',col='DETAIL • illustrative',bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=put(bpy.context.object,name,m,col); o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Edge radius','BEVEL'); mod.width=bevel; mod.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def cyl(name,loc,r,depth,m='body',axis='Z',col='DETAIL • illustrative',verts=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    o=put(bpy.context.object,name,m,col)
    if axis=='X': o.rotation_euler[1]=math.pi/2
    elif axis=='Y': o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def boolop(obj,tool,op='DIFFERENCE'):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new(op,'BOOLEAN'); mod.operation=op; mod.solver='EXACT'; mod.object=tool
    bpy.ops.object.modifier_apply(modifier=mod.name); bpy.data.objects.remove(tool,do_unlink=True)
    return obj

def cutbox(o,loc,dim): return boolop(o,box('cutter',loc,dim,None))
def hole(o,loc,r,dep,axis='Z'): return boolop(o,cyl('drill',loc,r,dep,None,axis))
def unite(o,loc,dim): return boolop(o,box('union',loc,dim,None),'UNION')
def roundplate(name,loc,dim,r,m='body',col='PRINTED • prototype'):
    # Planar rounded rectangle extruded with truly flat top/bottom.
    w,l,t=dim; v=[]
    for cx,cy,start in [(w/2-r,l/2-r,0),(-w/2+r,l/2-r,90),(-w/2+r,-l/2+r,180),(w/2-r,-l/2+r,270)]:
        for i in range(9):
            a=math.radians(start+i*90/8); v.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    n=len(v); verts=[(x+loc[0],y+loc[1],z+loc[2]) for z in [-t/2,t/2] for x,y in v]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); COL[col].objects.link(o); o.data.materials.append(M[m]); return o

def label(txt,loc,size=2.2,rotation=(0,0,0),m='white'):
    bpy.ops.object.text_add(location=loc,rotation=rotation); o=put(bpy.context.object,txt,m)
    o.data.body=txt; o.data.size=size; o.data.align_x='CENTER'; o.data.extrude=.005
    return o

def wire(name,pts,m,r=.55):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=3
    s=cu.splines.new('BEZIER'); s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts): p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu); COL['DETAIL • illustrative'].objects.link(o); o.data.materials.append(M[m]); return o

# Models are built first. Component library can be inspected without the chassis.
HW='HARDWARE • nominal reference'; PR='PRINTED • prototype'
servo_objects=[]
for side,y in [(-1,27),(1,-27)]:
    # Local height maps to lateral X; nominal overall28.5 includes boss+shaft.
    x=side*29; body_y=y-5.5
    o=box(('FL' if side<0 else 'RR')+' MG90S case ASSUMED 23mm', (x,body_y,17),(S['body_height_assumed'],S['body_length'],S['body_width']),'blue',HW,.6); servo_objects.append(o)
    for xx in [x-side*8.5,x+side*8]: box('Case seam',(xx,body_y,17),(.35,22.9,12.3),'black')
    ear=box('Servo mounting flange — assumed',(x+side*6,body_y,17),(2,32.5,12.2),'blue',HW)
    for yy in [body_y-13.8,body_y+13.8]: hole(ear,(x+side*6,yy,17),1.1,5,'X')
    cyl('Output boss — assumed',(side*42, y,17),5.7,3,'blue','X',HW)
    cyl('Output shaft — assumed',(side*44.75,y,17),2.3,2.5,'gold','X',HW)
    # Retain purchased horn; do not print a spline.
    horn=cyl('Purchased horn — representative',(side*46.6,y,17),10,1.2,'white','X',HW)
    hole(horn,(side*46.6,y,17),1,4,'X')
    for rr in [6,9]:
        for a in [0,math.pi/2,math.pi,3*math.pi/2]: hole(horn,(side*46.6,y+rr*math.cos(a),17+rr*math.sin(a)),.75,4,'X')
    for sy in [-1,1]:
        for sz in [-1,1]: cyl('Case screw',(x-side*11.55,body_y+sy*8.5,17+sz*4.1),.8,.4,'silver','X')

battery=box('Tattu 2S 450mAh — nominal 61x16x15',(0,0,19),(B['width'],B['length'],B['height']),'battery',HW,1.3)
box('Battery label',(0,0,26.56),(15,39,.12),'white')
label('2S / 450', (0,-1,26.7),3,m='black')
# S2: published outline. Feature placements cosmetic unless documented.
s2=roundplate('WEMOS S2 mini — 34.3x25.4',(0,10,38.8),(E['width'],E['length'],E['pcb_thickness_assumed']),1,'pcb',HW)
for x in [-10.16,-7.62,7.62,10.16]:
    for i in range(8):
        yy=10-8.89+i*2.54; pad=cyl('2.54mm header pad',(x,yy,39.64),.82,.1,'gold'); hole(pad,(x,yy,39.64),.43,.6)
box('ESP32-S2 package cosmetic',(0,12,40.7),(7,7,2.2),'black')
box('USB C shell cosmetic',(0,-6.3,40.7),(8.8,7.1,3.2),'silver',HW,.6)
box('USB opening',(0,-9.86,40.7),(6.8,.2,1.8),'black')
for x in [-6,6]: box('Reset / boot cosmetic',(x,-1,40.2),(3,3,1.4),'black')
for i in range(5): box('PCB antenna decorative',(-4+i*2,23.3,39.65),(.6,5,.1),'gold')
label('S2 MINI',(0,6,39.8),1.7)
reg=box('Pololu 4872 — nominal board',(0,-23.5,40.7),(R['width'],R['length'],1.3),'reg',HW,.5)
box('Regulator underside allowance',(0,-23.5,39),(13,23,2),'black',HW)
box('Buck inductor illustrative',(0,-22,43.2),(7,7,4),'black')
for x in [-4,4]:
    box('Adjustment potentiometer',(x,-30.5,43.2),(3.5,5,5),'gold')
    cyl('Adjustment screw',(x,-30.5,45.8),1.2,.4,'silver')
for i in range(6): cyl('Regulator pad',(-6.35+i*2.54,-12.5,41.41),.8,.1,'gold')
# Provisional camera visualization, replace parameters after hardware selection.
cam=box('FPV AIO camera — PROVISIONAL ENVELOPE',(0,42,50),(K['width_envelope'],K['depth_envelope']-10,K['height_envelope']),'black',HW,1)
box('Camera PCB illustrative',(0,35.4,50),(19,1.2,19),'reg')
cyl('Camera lens barrel',(0,54,50),5.6,10,'black','Y',HW)
cyl('Camera glass',(0,59.1,50),4.6,.3,'glass','Y')
wire('FPV antenna indicative',[(7,37,57),(11,36,64),(12,36,72)],'black',.65)

# Auxiliary purchased hardware and explicitly provisional hand-wired envelope.
cyl('Panasonic EEUFR1A102 nominal body',(28,20,21.5),5,16,'black','Z',HW)
for xx in [25.5,30.5]: cyl('Bulk capacitor insulated lead',(xx,20,12),.45,3,'silver','Z',HW)
label('1000uF',(28,20,29.6),1.7)
cyl('Logic capacitor provisional',(22,38,18),3.2,12,'black','Z',HW)
box('Switched voltage sense perfboard envelope',( -28,-13,15.5),(20,25,8),'reg',HW,.3)
box('Fuse + insulation envelope — verify selected part',(29,-1,16),(10,22,10),'black',HW,.8)
box('XT30 mating pair envelope',(0,-44,23),(11,16,8),'accent',HW,1)
box('JST XH balance connector envelope',(-21,-43,17),(13,9,7),'white',HW,.7)

# Save hardware-only inspectable library, keeping coordinates shared with assembly.
scene['fidelity']='Published nominal envelopes + explicitly assumed exterior detail. No physical measurements.'
scene['front']='+Y'; scene['units']='mm'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cad/components.blend'),compress=True)

# Printed lower tray. Flat plate plus integral servo stops and battery guides.
base=roundplate('01_chassis',(0,0,9),(C['width'],C['length'],C['floor_thickness']),C['corner_radius'])
# Battery rails / stop; clearance:20x66, soft padding below.
for x in [-11,11]: unite(base,(x,0,14.5),(2,66,8.2))
for y in [-34,34]: unite(base,(0,y,13),(24,2,5.2))
# Slots for battery strap, two ties running transverse.
for yy in [-18,18]:
    for xx in [-15,15]: cutbox(base,(xx,yy,9),(3.5,6,8))
# Servo body is supported by plate; zip ties route over body through base slots.
for side,yy in [(-1,27),(1,-27)]:
    xx=side*29; cy=yy-5.5
    for y in [cy-12.9,cy+12.9]: unite(base,(xx,y,12.5),(23,1.8,4.2))
    for y in [cy-12.9,cy+12.9]: cutbox(base,(xx+side*6,y,14.5),(3.2,4,8))
    # two independent ties run in YZ planes, away from assumed ear plane
    for dx in [-6,1]:
        for y in [cy-15.5,cy+15.5]: cutbox(base,(xx+side*dx,y,9),(3.2,3.2,8))
# Standoffs integrated in base, end at deck bottom34.5.
for x in [-14,14]:
    for y in [-30,30]:
        boolop(base,cyl('Post',(x,y,22.4),2.8,24.2,None),'UNION')
        hole(base,(x,y,31.5),.85,8)
# Skid mount / wire exits / service tie points
for x,y in [(31,38),(-31,-38)]: hole(base,(x,y,9),1.2,8)
for x,y in [(-32,-12),(32,12),(-29,42),(29,-42)]: cutbox(base,(x,y,9),(6,3,8))
# Extra tie slots for sense board, fuse, capacitor and rear connectors.
for x,y in [(-39,-13),(-16,-13),(22,-1),(36,-1),(20,20),(36,20),(-29,-44),(-12,-44),(-9,-42),(9,-42)]:
    cutbox(base,(x,y,9),(2.5,5,8))
# Upper electronics deck. Posts overlap the battery footprint neither in X nor Z.
deck=roundplate('02_electronics_deck',(0,0,35.75),(44,72,2.5),4,'accent')
for x in [-14,14]:
    for y in [-30,30]: hole(deck,(x,y,35.75),1.2,7)
# Strap board edges, no guessed PCB mounting hole usage.
for y in [-22,8,20]:
    for x in [-16.5,16.5]: cutbox(deck,(x,y,35.75),(2.4,4,7))
# Heat opening below regulator; saddle border for insulation spacers.
cutbox(deck,(0,-23.5,35.75),(10,17,7))
for x in [-7.3,7.3]: unite(deck,(x,-23.5,38.5),(1.0,25,3.1))
# S2 board edge support rails and antenna clearance (no metal above antenna).
for x in [-12,12]: unite(deck,(x,10,37.45),(1.4,32,1.1))
# Camera cradle attached via two M2 screws into deck nose extension.
unite(deck,(0,37.8,35.75),(30,7,2.5))
for x in [-11,11]: hole(deck,(x,38,35.75),1.2,8)
# U cradle separate, open top for velcro retention; camera envelope20mm wide.
cradle=box('03_camera_cradle',(0,42,38.25),(26,22,2.5),'accent',PR)
for x in [-12,12]: unite(cradle,(x,42,45.8),(2,22,16))
unite(cradle,(0,32,44),(26,2,12.8))
for x in [-11,11]: hole(cradle,(x,38,38.25),.85,3)
# Camera retention strap windows through side walls.
for x in [-12,12]: cutbox(cradle,(x,44,49),(5,5,2.5))
# Detachable smooth-floor skid feet, optional PTFE tape on convex contact.
for i,(x,y) in enumerate([(31,38),(-31,-38)]):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=5,location=(x,y,5)); foot=put(bpy.context.object,f'0{4+i}_skid_foot','black',PR)
    boolop(foot,cyl('Skid flange',(x,y,6.4),6,2.2,None),'UNION')
    cutbox(foot,(x,y,17.5),(30,30,20))
    hole(foot,(x,y,6),.8,5)
# Wheels: flat outer face with radial slots accepting actual horn holes.
for idx,(side,y) in enumerate([(-1,27),(1,-27)]):
    x=side*W['center_x']
    wheel=cyl(f'0{6+idx}_drive_wheel',(x,y,17),W['diameter']/2,W['width'],'accent','X',PR,96)
    hole(wheel,(x,y,17),2.5,12,'X')
    # recess on inboard side encloses the horn, leaving 3mm outer web
    hole(wheel,(x-side*2.4,y,17),10.7,3,'X')
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:
        # connected slot circles and center rectangle, 5..11 radial centers
        for rr in [5,11]: hole(wheel,(x,y+rr*math.cos(a),17+rr*math.sin(a)),1.1,12,'X')
        if abs(math.cos(a))>.5: cutbox(wheel,(x,y+8*math.cos(a),17),(12,6,2.2))
        else: cutbox(wheel,(x,y,17+8*math.sin(a)),(12,2.2,6))
    # Two shallow circumferential grooves to accept optional elastic grip bands.
    for dx in [-2,2]:
        outer=cyl('Groove tool',(x+dx,y,17),18,.8,None,'X',verts=96)
        hole(outer,(x+dx,y,17),16.4,2,'X'); boolop(wheel,outer)
# Print fit coupon with servo width gauge and M2 clearances.
coupon=roundplate('08_fit_coupon',(78,0,1.5),(35,46,3),3,'accent')
cutbox(coupon,(78,-8,2),(13.4,24,8))
for i,d in enumerate([1.6,1.8,2.0,2.2,2.4]): hole(coupon,(66+i*6,17,1.5),d/2,8)
# Keep coupon hidden in hero render, still exported.
coupon.hide_render=True
# Indicative routed leads; electrical netlist lives in electronics/wiring.md.
wire('Battery + illustrative',[(4,-30,20),(7,-38,27),(12,-36,34),(9,-22,43)],'red')
wire('Battery - illustrative',[(-4,-30,20),(-8,-38,27),(-12,-35,33),(-9,-22,43)],'black')
for s,y in [(-1,27),(1,-27)]:
    wire('Servo harness indicative',[(s*19,y-9,19),(s*17,y-14,27),(s*22,-3,31),(s*10,-10,40)],'black',.85)
# Retention ties shown schematically; actual fit uses purchased ties.
for y in [-18,18]:
    wire('Battery tie indicative',[(-15,y,9),(-13,y,22),(-9,y,28),(9,y,28),(13,y,22),(15,y,9)],'black',.7)
# Assembly fasteners
for x in [-14,14]:
    for y in [-30,30]: cyl('M2 deck screw',(x,y,37.4),1.8,.8,'silver')
for x,y in [(31,38),(-31,-38)]: cyl('M2 skid screw',(x,y,10.8),1.8,.6,'silver')
label('DIAGONAL / 01',(0,-44,10.6),2.5)

# Deterministic binary STL exporter: transforms coordinates, normalizes each print to build plate.
def export_stl(obj):
    mesh=obj.data.copy(); mesh.transform(obj.matrix_world)
    # wheels print outboard-face down, skids flange-down; base/deck/cradle/coupon as built.
    from mathutils import Matrix
    if 'drive_wheel' in obj.name: mesh.transform(Matrix.Rotation((-1 if obj.name.startswith('06') else 1)*math.pi/2,4,'Y'))
    if 'skid_foot' in obj.name: mesh.transform(Matrix.Rotation(math.pi,4,'X'))
    mins=[min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maxs=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
    offset=Vector((-(mins[0]+maxs[0])/2,-(mins[1]+maxs[1])/2,-mins[2]))
    for v in mesh.vertices: v.co+=offset
    import bmesh
    clean=bmesh.new(); clean.from_mesh(mesh)
    bmesh.ops.remove_doubles(clean,verts=list(clean.verts),dist=0.00002)
    bmesh.ops.dissolve_degenerate(clean,edges=list(clean.edges),dist=0.00002)
    bmesh.ops.recalc_face_normals(clean,faces=list(clean.faces))
    clean.to_mesh(mesh); clean.free()
    mesh.calc_loop_triangles()
    path=ROOT/'stl'/f'{obj.name}.stl'
    with path.open('wb') as f:
        f.write(b'Diagonal Spy Car mm prototype'.ljust(80,b'\0')); f.write(struct.pack('<I',len(mesh.loop_triangles)))
        for t in mesh.loop_triangles:
            vs=[mesh.vertices[i].co for i in t.vertices]; n=(vs[1]-vs[0]).cross(vs[2]-vs[0]).normalized()
            f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
    # topology audit independent of render appearance
    import bmesh
    bm=bmesh.new(); bm.from_mesh(mesh)
    report={'file':str(path.relative_to(ROOT)), 'triangles':len(mesh.loop_triangles),
            'size_mm':[round(maxs[i]-mins[i],3) for i in range(3)],
            'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
            'volume_mm3':round(abs(bm.calc_volume(signed=True)),2)}
    bm.free(); bpy.data.meshes.remove(mesh); return report
reports=[export_stl(o) for o in COL[PR].objects if o.type=='MESH']
(ROOT/'cad/mesh-report.json').write_text(json.dumps(reports,indent=2)+'\n')
assert all(r['non_manifold_edges']==0 and r['volume_mm3']>0 for r in reports),reports
# studio camera and lights
floor=box('Studio floor',(0,0,-2),(2000,2000,3.8),'floor','STUDIO')
def point(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def cam_at(name,loc,target,scale):
    bpy.ops.object.camera_add(location=loc); o=put(bpy.context.object,name,None,'STUDIO'); point(o,target); o.data.type='ORTHO'; o.data.ortho_scale=scale; return o
hero=cam_at('Assembly camera',(-150,180,145),(0,2,26),165)
top=cam_at('Plan camera',(0,3.6,260),(0,3.6,0),165)
for name,loc,energy,size in [('Key',(-80,50,180),450000,140),('Fill',(120,10,90),300000,110),('Rim',(0,-120,100),350000,90)]:
    bpy.ops.object.light_add(type='AREA',location=loc); o=put(bpy.context.object,name,None,'STUDIO'); o.data.energy=energy; o.data.shape='DISK'; o.data.size=size; point(o,(0,0,20))
scene.camera=hero
# Default viewport is useful on opening.
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=190
        area.spaces.active.region_3d.view_location=Vector((0,0,25))
        area.spaces.active.clip_end=5000
scene['design_status']='Unbuilt fit prototype. See docs/measurement-checklist.md before printing.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'cad/diagonal-spy-car.blend'),compress=True)
scene.render.filepath=str(ROOT/'images/assembly.png'); bpy.ops.render.render(write_still=True)
scene.camera=top; scene.render.filepath=str(ROOT/'images/top.png'); bpy.ops.render.render(write_still=True)
# Exploded image offsets upper deck group visually, without modifying saved assembly.
for o in list(COL[PR].objects)+list(COL[HW].objects)+list(COL['DETAIL • illustrative'].objects):
    if o==coupon: continue
    if o.type=='MESH':
        z=sum((o.matrix_world@v.co).z for v in o.data.vertices)/max(1,len(o.data.vertices))
    else: z=60 if o.name=='FPV antenna indicative' else o.location.z
    if z>33: o.location.z+=35
scene.camera=hero; hero.data.ortho_scale=185; point(hero,(0,3,42))
scene.render.filepath=str(ROOT/'images/exploded.png'); bpy.ops.render.render(write_still=True)
print('BUILD_OK',json.dumps(reports))
