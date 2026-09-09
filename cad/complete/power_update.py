"""Apply the power/service accuracy revision to the saved assembly without rebuilding its mechanics.
Run after build.py, or directly on the current .blend. Original printed geometry is preserved.
"""
import bpy, bmesh, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from fuse_geometry import epoxy_body, formed_lead_points
MODEL = OUT / 'complete-spy-car.blend'
SOURCE = Path(sys.argv[sys.argv.index('--source')+1]) if '--source' in sys.argv else MODEL
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.data.scenes['01 ASSEMBLED']
bpy.context.window.scene = scene

def signature(o):
    return hashlib.sha256(repr((list(o.matrix_world), [tuple(v.co) for v in o.data.vertices],
        [tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
protected = {o.name: signature(o) for o in scene.objects if o.type == 'MESH' and o.get('assembly_group') in
             ('base','deck','battery','battery_band','buck','s2','drive_left','drive_right')}
# Remove only objects owned by this update on repeat runs; retain user scenes and mechanics.
for scene_name in ('04 POWER SERVICE','05 CONNECTOR DETAILS'):
    if bpy.data.scenes.get(scene_name):
        old = bpy.data.scenes[scene_name]
        for o in list(old.objects):
            if len(o.users_scene) == 1: bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.scenes.remove(old)
for o in list(bpy.data.objects):
    if o.name.startswith('PW |'): bpy.data.objects.remove(o, do_unlink=True)
old_names = ['Input fuse - unselected small leaded package','J_PWR removable logic feed',
             'VBAT positive through inline fuse','5V bus through removable J_PWR']
for o in list(bpy.data.objects):
    if any(o.name == n or o.name.startswith(n+'.') for n in old_names): bpy.data.objects.remove(o,do_unlink=True)
for old_col in list(bpy.data.collections):
    if old_col.name.startswith('REFERENCE - power service revision') and not old_col.objects:
        bpy.data.collections.remove(old_col)
col = bpy.data.collections.new('REFERENCE - power service revision')
scene.collection.children.link(col)
created = []

def material(name, color, metal=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1);m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Metallic'].default_value=metal;shader.inputs['Roughness'].default_value=.45
    return m
mats={'red':material('PW positive insulation',(.62,.012,.02)),
      'black':material('PW black insulation',(.015,.02,.025)),
      'green':material('PW epoxy fuse body',(.06,.27,.13)),
      'metal':material('PW tin contacts',(.5,.56,.6),.8),
      'tan':material('PW ceramic',(.55,.41,.19))}

def register(o,name,color):
    o.name='PW | '+name
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.data.materials.clear();o.data.materials.append(mats[color]);o['assembly_group']='harness'
    o['dimension_status']='Nominal routing/package illustration; verify purchased parts and service clearances'
    created.append(o);return o

def box(name,loc,size,color,bevel=.15):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=register(bpy.context.object,name,color);o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Rounded insulation','BEVEL');mod.width=bevel;mod.segments=3
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def cyl(name,loc,radius,length,color,axis='Y'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=length,location=loc)
    o=register(bpy.context.object,name,color)
    if axis=='Y':o.rotation_euler.x=math.pi/2
    if axis=='X':o.rotation_euler.y=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o

def wire(name,points,color='red',radius=.45,net=''):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3;data.resolution_u=16
    data.use_fill_caps=True
    spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for p,co in zip(spline.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=register(bpy.data.objects.new(name,data),name,color);o['net']=net;o['route_status']='Illustrative service loop, not a cut-length or wire-clearance certification'
    return o

# Published fuse body and wire diameter; trimmed/bent lead lengths are assembly assumptions.
fuse=epoxy_body(register)
fuse['source']='https://www.littelfuse.com/assetdocs/littelfuse_fuse_251_253_datasheet.pdf?assetguid=f47a0bb7-8ede-4679-9646-7114c3787688'
fuse['rating_status']='4 A fuse selection remains provisional pending load tests'
# Formed leads exit axially through the revised holder before bending down.
for sign,net in [(-1,'VBAT_RAW'),(1,'VBAT_SW')]:
    lead=wire('F_IN '+net+' lead',formed_lead_points(sign),'metal',.32,net)
    lead.data.splines.clear();sp=lead.data.splines.new('POLY')
    pts=formed_lead_points(sign);sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    lead['bend_radius_mm']=1.0
    lead['route_status']='Forming allowance; support lead during bending and verify delivered part'
    # The sleeve overlaps both tin lead and wire insulation at the solder joint.
    cyl('F_IN '+net+' joint insulation',(-15,sign*8.5,17),.8,3.0,'red')
wire('Battery harness to F_IN',[(-2.5,10.4,42.7),(-12,11,43),(-27,8,36),(-27,-3,22),(-15,-3,16),(-15,-9,17)],net='VBAT_RAW',radius=.65)
wire('F_IN to buck IN+',[(-15,9,17),(-15,3,16),(-27,3,20),(-28,-13,28),(-23,-16.1,33),(-19.9,-16.1,30.86)],net='VBAT_SW',radius=.65)
# A real separation in the positive-only logic feed, rather than a wire through a solid block.
# Connector family not selected: these two housings are explicitly a packaging allowance.
for name,x in [('bus-side insulated socket',2.4),('S2-side insulated plug',-2.4)]:
    o=box('J_PWR '+name,(x,8,34),(4.6,2.8,3),'black')
    o['electrical_role']='Positive 5V feed only; mating halves connect 5V_BUS to S2_VBUS. No ground pole.'
    o['dimension_status']='9.4 x 2.8 x 3 mm mated allowance, illustrative only; choose and measure an insulated connector'
cyl('J_PWR recessed mating contact',(0,8,34),.3,1.2,'metal','X')
plus=(20,-13,33.5);minus=(23,-13,33.5)
for name,pt,color in [('5V_BUS insulated star splice',plus,'red'),('GND insulated star splice',minus,'black')]:
    o=cyl(name,pt,.75,2.4,color);o['electrical_role']=name
wire('5V_BUS to J_PWR socket',[plus,(24,-12,35),(26,7,35),(12,8,34),(4.7,8,34)],net='5V_BUS')
wire('J_PWR plug to S2 VBUS',[(-4.7,8,34),(-8.9,8,34),(-8.89,11.57,30.86)],net='S2_VBUS')
# Replace obsolete virtual star points inside the battery with explicit insulated junctions.
star_old=[Vector((21,-10.5,30.8)),Vector((23,-10.5,30.8))]
for o in scene.objects:
    if o.type!='CURVE' or o.name.startswith('PW |'):continue
    for sp in o.data.splines:
        for p in sp.bezier_points:
            for before,after in zip(star_old,[plus,minus]):
                if (p.co-before).length<.02:p.co=after
            # Keep power service loops outside the battery's occupied volume.
            if any(tag in o.name for tag in ('servo GPIO','Common logic')) and 28<p.co.z<40 and -11<=p.co.y<=6 and abs(p.co.x)<24.8:
                p.co.x=27 if p.co.x>=0 else -27
# Use explicit outside-deck descent lanes, then cross below the deck.
# Merely moving a control point outside the pouch can still leave the curve through it.
def route_existing(name, points):
    obj=scene.objects.get(name)
    if not obj:return
    obj.data.splines.clear()
    spline=obj.data.splines.new('POLY')
    # Small sampled corner fillets remain within the waypoint polygon.
    sampled=[Vector(points[0])]
    for i in range(1,len(points)-1):
        a,b,c=map(Vector,points[i-1:i+2]);u=a-b;v=c-b
        trim=min(1.0,u.length/3,v.length/3)
        entry=b+u.normalized()*trim;exit=b+v.normalized()*trim
        for j in range(9):
            t=j/8;sampled.append((1-t)**2*entry+2*(1-t)*t*b+t*t*exit)
    sampled.append(Vector(points[-1]));spline.points.add(len(sampled)-1)
    for p,co in zip(spline.points,sampled):p.co=(*co,1)
    obj.data.use_fill_caps=True
    obj['route_status']='Nominal outside-pouch route with illustrative 1 mm corner allowance; physical bends and chassis clearances unverified'
def curve_end(obj,index):
    sp=obj.data.splines[0];points=sp.bezier_points if sp.type=='BEZIER' else sp.points
    return tuple(points[index].co[:3])
for pin,side in [('GPIO16',-1),('GPIO18',1)]:
    for prefix,junction,y in [('5V servo ',plus,-1),('GND servo ',minus,1)]:
        name=prefix+pin;obj=scene.objects[name];end=curve_end(obj,-1)
        route_existing(name,[junction,(28 if prefix.startswith('GND') else 27,-13,34),
            (28 if prefix.startswith('GND') else 27,y,34),(28 if prefix.startswith('GND') else 27,y,17),
            (side*15,y,17),(side*15,end[1],17),end])
    name=pin+' signal to servo';obj=scene.objects[name]
    start=curve_end(obj,0);end=curve_end(obj,-1)
    route_existing(name,[start,(side*27,9,34),(side*27,3,34),(side*27,3,17),
        (side*14,3,17),(side*14,end[1],17),end])
route_existing('Common logic ground',[minus,(28,-13,34),(28,9,34),(-6.35,11.57,30.86)])
route_existing('PW | 5V_BUS to J_PWR socket',[plus,(27,-13,35),(27,8,35),(12,8,34),(4.7,8,34)])
# Fix main negative route so it goes around, rather than across, buck components.
negative=scene.objects.get('VBAT negative to buck')
if negative:
    pts=[(2.5,10.4,42.7),(-12,12,43),(-27,11,40),(-29,-12,33),(-27,-35,33),(-19.9,-33.9,30.86)]
    negative.data.splines.clear();sp=negative.data.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
# Small capacitors now have visible lead connections. The bypass follows J_PWR at the MCU.
bypass=scene.objects.get('100nF bus bypass')
if bypass:
    bypass.location=(-8.0,14.3,33.3)
    bypass['electrical_role']='100 nF between S2_VBUS after J_PWR and GND, close to the board pads'
wire('100nF bypass positive lead',[(-8.8,14.3,32.3),(-8.89,12.8,32),(-8.89,11.57,30.86)],'metal',.16,'S2_VBUS')
wire('100nF bypass ground lead',[(-7.2,14.3,32.3),(-6.35,12.8,32),(-6.35,11.57,30.86)],'metal',.16,'GND')
# Synchronize changed harness routes and packages into the existing exploded view.
exploded=bpy.data.scenes['02 EXPLODED']
for original in scene.objects:
    if original.get('assembly_group')!='harness':continue
    if original.name.startswith('PW |'):
        copy=original.copy();copy.data=original.data.copy();exploded.collection.objects.link(copy)
    else:
        copies=[o for o in exploded.objects if o.name.startswith(original.name+'.') and o.get('assembly_group')=='harness']
        if not copies:continue
        copy=copies[0]
        if original.type=='CURVE':copy.data=original.data.copy()
        copy.location=original.location
    offset=Vector((-32,30,70)) if any(t in original.name for t in ('XT30','balance','Balance','Unplug','J_PWR')) else Vector((0,0,25))
    copy.location+=offset
    if copy.type=='CURVE':copy.hide_render=True
bpy.context.view_layer.update()
assert all(signature(scene.objects[name])==digest for name,digest in protected.items()), 'Unexpected change to protected mechanical/component geometry'
def bounds(o):
    points=[o.matrix_world@Vector(p) for p in o.bound_box]
    return ([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
def overlap(a,b):
    al,ah=bounds(a);bl,bh=bounds(b)
    if any(ah[i]<=bl[i] or bh[i]<=al[i] for i in range(3)):return 0
    obj=a.copy();obj.data=a.data.copy();scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Temporary collision check','BOOLEAN');mod.operation='INTERSECT';mod.solver='EXACT';mod.object=b
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bm=bmesh.new();bm.from_mesh(obj.data);vol=abs(bm.calc_volume());bm.free();data=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(data)
    return vol
rigid=[fuse]+[o for o in created if 'J_PWR' in o.name and o.type=='MESH']+([bypass] if bypass else [])
collisions=[]
for a in rigid:
    for name in protected:
        b=scene.objects[name]
        vol=overlap(a,b)
        if vol>.03:collisions.append({'a':a.name,'b':name,'volume_mm3':vol})
# Validate actual swept lead geometry through the printed end-stop bores.
lead_checks=[]
for lead in [o for o in created if o.name.startswith('PW | F_IN VBAT_') and o.name.endswith(' lead')]:
    evaluated=lead.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=bpy.data.meshes.new_from_object(evaluated)
    probe=bpy.data.objects.new('Temporary fuse lead validation',mesh);scene.collection.objects.link(probe)
    probe.matrix_world=lead.matrix_world.copy();bpy.context.view_layer.update()
    for name in protected:
        volume=overlap(probe,scene.objects[name])
        if volume>.03:collisions.append({'a':lead.name,'b':name,'volume_mm3':volume})
    lead_checks.append(lead.name)
    bpy.data.objects.remove(probe,do_unlink=True);bpy.data.meshes.remove(mesh)
assert not collisions, collisions
fl,fh=bounds(fuse);fuse_measured=[fh[i]-fl[i] for i in range(3)]
assert all(abs(v-e)<.001 for v,e in zip(fuse_measured,[2.8,7.11,2.8])),fuse_measured
report={'revision':'0.6.2-no-external-bulk','source_sha256':source_hash,'preserved_meshes':len(protected),
 'protected_geometry_unchanged':True,'rigid_package_collisions':collisions,
 'fuse_body_mm':{'length':7.11,'diameter_max':2.8,'lead_diameter':.64},
 'fuse_shape':'Rounded tapered epoxy with shallow waist; contour inferred from family photo',
 'fuse_measured_xyz_mm':fuse_measured,
 'formed_leads_collision_checked':lead_checks,
 'fuse_leads':'Straight axial exits through 1.5 mm holder bores; 1 mm centerline-radius bends',
 'J_PWR':'Two insulated mating halves in positive lead only; connector envelope remains provisional',
 'bypass':'100 nF at S2 VBUS/GND, after J_PWR',
 'battery_monitoring':'Manual per-cell multimeter checks; no sensing board or automatic low-voltage stop',
 'limitations':['Routing illustrates nets; complete wire collision and bend-radius validation is not performed.',
 'Fuse holder has axial lead-clearance bores; retention, insulation, strain relief and lead-forming allowances need physical checks.',
 'Home-Wi-Fi-first OTA is planned; current firmware creates SpyCar-Update.',
 'Published nominal components do not replace measurements of owned hardware.']}
allparts=[o for o in scene.objects if o.type in ('MESH','CURVE','FONT') and o.get('assembly_group') and not o.hide_render]
lo=[min(bounds(o)[0][i] for o in allparts) for i in range(3)];hi=[max(bounds(o)[1][i] for o in allparts) for i in range(3)]
report['assembly_bounds_mm']={'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
(OUT/'power-validation.json').write_text(json.dumps(report,indent=2)+'\n')
scene['power_revision']='0.6.2: no external bulk capacitor or sensing board; rounded fuse with axial lead exits'
scene['network_status']='Home Wi-Fi browser driving supported; OTA currently uses own AP. Home-network OTA is planned.'
# Expose hidden power parts in a separate service scene; normal assembly remains complete.
bpy.ops.scene.new(type='FULL_COPY');service=bpy.context.scene;service.name='04 POWER SERVICE'
for o in service.objects:
    if o.get('assembly_group') in ('base','deck','battery','battery_band','drive_left','drive_right'):
        o.hide_render=True;o.hide_set(True)
service['view_note']='Pouch, printed carrier and running gear hidden to expose service wiring. Not an alternate assembly.'
service.camera.data.ortho_scale=104
service.camera.location=(-70,-110,155)
service.camera.rotation_euler=(Vector((0,0,28))-service.camera.location).to_track_quat('-Z','Y').to_euler()
# Separate enlarged view explains the two service parts without hiding them under the pouch.
details=bpy.data.scenes.new('05 CONNECTOR DETAILS');details.world=scene.world.copy()
details.render.engine='CYCLES';details.cycles.samples=32;details.cycles.use_denoising=True
details.view_settings.view_transform='AgX';details.render.image_settings.file_format='PNG'
for original in created:
    is_fuse=original==fuse or original.name.startswith('PW | F_IN VBAT_')
    is_connector='J_PWR' in original.name and original.type=='MESH'
    if not is_fuse and not is_connector:continue
    if original.type not in ('MESH','CURVE'):continue
    copy=original.copy();copy.data=original.data.copy();details.collection.objects.link(copy)
    if 'F_IN' in original.name:copy.location+=Vector((3,0,-17.2))
    else:
        separation=3 if 'socket' in original.name else -3
        copy.location+=Vector((10+separation,-8,-31))
    copy.hide_render=False
# Studio objects are copied, not shared, so the original view and lighting are preserved.
for original in scene.objects:
    if original.type=='LIGHT':
        copy=original.copy();copy.data=original.data.copy();details.collection.objects.link(copy)
camdata=bpy.data.cameras.new('PW detail camera');cam=bpy.data.objects.new('PW detail camera',camdata);details.collection.objects.link(cam)
cam.location=(0,0,100);cam.rotation_euler=(0,0,0);camdata.type='ORTHO';camdata.ortho_scale=48;details.camera=cam
for text,x,y,size in [('F_IN: AXIAL FUSE',-12,13,1.2),('7.11 mm x 2.80 mm max',-12,-12, .8),('Rounded contour: photo approximation',-12,-14,.65),
                       ('J_PWR: UNPLUGGED',10,13,1.2),('Positive 5 V lead only',10,-8,.9),
                       ('Connector shape is provisional',10,-10,.75)]:
    data=bpy.data.curves.new('PW detail label','FONT');data.body=text;data.size=size;data.align_x='CENTER'
    obj=bpy.data.objects.new('PW detail label',data);details.collection.objects.link(obj);obj.location=(x,y,5)
    data.materials.append(bpy.data.materials['Silkscreen'])
details['view_note']='Enlarged service parts, moved apart for inspection. J_PWR shown unplugged; dimensions are a provisional package allowance.'
# Return to the original assembly for opening the .blend.
bpy.context.window.scene=scene
scene.camera=scene.objects['Camera - assembly']
for s in (scene,exploded,service,details):
    s.cycles.samples=32
    s.render.resolution_x=1600;s.render.resolution_y=1250;s.render.resolution_percentage=100
assert not [o.name for o in bpy.data.objects if any(t in o.name.lower() for t in ('220uf','bulk capacitor','bulk positive','bulk negative','perfboard','sense resistor','sense gpio','sense ground','sense fused','adc filter','bs250p','2n3904','adc carrier','adc spring','adc retaining','adc fixed'))], 'Unexpected sensing component remains'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
if '--skip-renders' not in sys.argv:
    for s,cam,name in [(scene,'Camera - assembly','assembly.png'),(scene,'Camera - plan','top.png'),
                       (scene,'Camera - side','side.png'),(exploded,None,'exploded.png'),(service,None,'power-service.png'),(details,None,'power-details.png')]:
        bpy.context.window.scene=s
        if cam:s.camera=s.objects[cam]
        s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=scene;scene.camera=scene.objects['Camera - assembly']
print('POWER_UPDATE_OK',json.dumps(report))
