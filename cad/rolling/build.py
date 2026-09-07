"""Build integral printed axles, servo clips and bearing press-fit wheels.

Run with Blender --background --python-exit-code 1 --python cad/rolling/build.py.
Append -- --skip-renders to export and validate without rendering.
The compact revision is an explicit input and is never overwritten.
"""
import bpy
import bmesh
import json
import math
import struct
import sys
from pathlib import Path
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(OUT))
from mesh_checks import validate_stl
P = json.loads((OUT/'parameters.json').read_text())
BASE = json.loads((OUT.parent/'compact/parameters.json').read_text())
BE, A, MT, W, CL = (P[k] for k in ('bearing', 'axle', 'mount', 'wheel', 'servo_clips'))
bpy.ops.wm.open_mainfile(filepath=str((OUT/P['base_model']).resolve()))
scene = bpy.context.scene
COL = {}
for name in ('PRINT • rolling parts', 'REFERENCE • wheel hardware', 'DETAIL • wheel context', 'FIT • coupon'):
    COL[name] = bpy.data.collections.new(name)
    scene.collection.children.link(COL[name])
PRINT, HW, DETAIL, FIT = COL.keys()


def material(name, rgb, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = .35 if metal else .48
    return m


mats = {
    'chassis': bpy.data.materials['Printed bracket / orange'],
    'wheel': material('Passive wheels / teal', (.035, .35, .32)),
    'metal': material('Bearings / steel', (.55, .62, .69), .8),
    'shield': material('Bearing shield detail', (.16, .21, .25), .65),
    'drive': material('Powered wheel / envelope only', (.07, .10, .14)),
    'label': material('Plan annotations', (.84, .92, .96)),
}


def put(o, name, collection=PRINT, mat=None):
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL[collection].objects.link(o)
    if mat:
        o.data.materials.clear()
        o.data.materials.append(mats[mat])
    return o


def box(name, loc, dim, collection=PRINT, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = put(bpy.context.object, name, collection, mat)
    o.dimensions = dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def cyl(name, loc, radius, depth, collection=PRINT, mat=None, vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = put(bpy.context.object, name, collection, mat)
    o.rotation_euler[1] = math.pi/2
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def boolean(o, cutter, op='DIFFERENCE', remove=True):
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new(op, 'BOOLEAN')
    mod.operation, mod.solver, mod.object = op, 'EXACT', cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if o.name=='rolling_chassis':
        clean(o)
    if o.name=='rolling_chassis' and '--debug' in sys.argv:
        bm=bmesh.new();bm.from_mesh(o.data)
        print('BOOLEAN_AUDIT',cutter.name,round(bm.calc_volume(signed=True),3),sum(not e.is_manifold for e in bm.edges))
        bm.free()
    if remove:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return o


def ring(name, loc, outside_d, inside_d, length, collection=PRINT, mat=None):
    o = cyl(name, loc, outside_d/2, length, collection, mat)
    boolean(o, cyl('Bore tool', loc, inside_d/2, length+2))
    return o


def single_material(o, name):
    o.data.materials.clear()
    o.data.materials.append(mats[name])
    for polygon in o.data.polygons:
        polygon.material_index = 0


def clean(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00001)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(o.data)
    bm.free()


def cone(name, start_x, end_x, y, z, start_d, end_d, side=1):
    # Local cone Z becomes world +/-X. The first radius is the root.
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=start_d/2, radius2=end_d/2,
                                   depth=end_x-start_x, location=(side*(start_x+end_x)/2,y,z))
    o=put(bpy.context.object,name)
    o.rotation_euler[1]=side*math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o


def add_integral_axle(base, side, y, z, root_x, journal_diameter):
    abut_end=root_x+A['abutment_length']
    journal_end=abut_end+A['journal_length']
    # The wide root provides the inner-ring abutment without a separate spacer.
    boolean(base,cyl('Integral root shoulder',(side*(root_x-.04+abut_end)/2,y,z),
                     A['abutment_diameter']/2,A['abutment_length']+.04),'UNION')
    boolean(base,cyl('Integral bearing journal',(side*(abut_end+journal_end)/2,y,z),
                     journal_diameter/2,A['journal_length']+.04),'UNION')
    boolean(base,cone('Integral lead-in',journal_end-.02,journal_end+A['lead_in_length'],y,z,
                      journal_diameter,A['tip_diameter'],side),'UNION')


def hook(side,y):
    # Prism with a flat retaining underside and a sloping insertion ramp.
    inner=CL['hook_inner_x']; outer=CL['stem_inner_x']+CL['stem_thickness']
    profile=[(inner,CL['hook_under_z']), (outer,CL['hook_under_z']),
             (outer,CL['top_z']), (CL['stem_inner_x'],CL['top_z']), (inner,CL['tip_top_z'])]
    points=[(side*x,yy,z) for yy in (y-CL['width_y']/2,y+CL['width_y']/2) for x,z in profile]
    n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new('Integral clip hook');mesh.from_pydata(points,[],faces);mesh.update()
    o=bpy.data.objects.new('Integral clip hook',mesh);COL[PRINT].objects.link(o)
    clean(o)
    return o


chassis=bpy.data.objects['servo_pair_bracket'];chassis.name='rolling_chassis'
all_prints=[chassis]
all_hardware=[o for c in bpy.data.collections if c.name.startswith('REFERENCE • servo') for o in c.objects if o.type=='MESH']
export_parts=[(chassis,'rolling-chassis.stl',False)]
passive_groups=[];wheel_records=[]
inner_x=W['inner_face_x'];outer_x=inner_x+W['width']
bearing_start=outer_x-W['bearing_seat_depth'];bearing_end=bearing_start+BE['width']
axle_z=BASE['bracket']['floor_thickness']+BASE['servo']['body_width']/2
axle_y=BASE['bracket']['lane_spacing']/2+BASE['servo']['spindle_offset']
assert abs(MT['outer_face_x']+A['abutment_length']-bearing_start)<.0001
assert A['journal_length']>=BE['width']
assert W['through_bore']>A['abutment_diameter']
assert W['diameter']<2*axle_y
for letter,sign in (('A',1),('B',-1)):
    shaft=bpy.data.objects['Servo '+letter+' • assumed output shaft']
    assert abs(shaft.location.y-sign*axle_y)<.001 and abs(shaft.location.z-axle_z)<.001,'Rebuild compact input'

# Remove all four old screw posts, keeping the original floor and locating rails.
for side,lane in ((-1,1),(1,-1)):
    cy=lane*BASE['bracket']['lane_spacing']/2
    old_x=side*(BASE['servo']['ear_axial_offset']+BASE['servo']['ear_thickness']/2+
                BASE['bracket']['ear_to_post_gap']+BASE['bracket']['post_axial_thickness']/2)
    for end in (-1,1):
        yy=cy+end*BASE['servo']['ear_hole_pitch']/2
        boolean(chassis,box('Remove old screw support',(old_x,yy,12.4),
                            (BASE['bracket']['post_axial_thickness']+.02,BASE['bracket']['post_width']+.02,20)))
        low=BASE['bracket']['floor_thickness']-.1
        high=CL['top_z']
        stem=box('Integral servo clip stem',(side*(CL['stem_inner_x']+CL['stem_thickness']/2),yy,(low+high)/2),
                 (CL['stem_thickness'],CL['width_y'],high-low))
        boolean(chassis,stem,'UNION');boolean(chassis,hook(side,yy),'UNION')
        outer=CL['stem_inner_x']+CL['stem_thickness'];r=CL['root_radius']
        floor_z=BASE['bracket']['floor_thickness']
        reinforcement=box('Clip root fillet',(side*(outer+r/2-.025),yy,floor_z+r/2-.05),
                          (r+.05,CL['width_y'],r+.1))
        cutter=cyl('Fillet tool',(side*(outer+r),yy,floor_z+r),r,CL['width_y']+2)
        cutter.rotation_euler[2]=math.pi/2
        bpy.context.view_layer.objects.active=cutter
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        boolean(reinforcement,cutter);boolean(chassis,reinforcement,'UNION')
        extension=CL['release_tab_extension']
        boolean(chassis,box('Integral clip release tab',(side*(outer+extension/2-.1),yy,CL['top_z']-.2),
                            (extension+.2,CL['width_y']-.4,.6)),'UNION')

for side in (1,-1):
    y=side*axle_y;tag='front-right' if side==1 else 'rear-left'
    start_objects=set(bpy.data.objects)
    block=box('Integral axle support',(side*(MT['inner_face_x']+MT['outer_face_x'])/2,y,MT['top_z']/2),
              (MT['outer_face_x']-MT['inner_face_x'],MT['width_y'],MT['top_z']))
    boolean(chassis,block,'UNION')
    add_integral_axle(chassis,side,y,axle_z,MT['outer_face_x'],A['journal_diameter'])
    wheel=ring('Passive press-fit wheel '+tag,(side*(inner_x+W['width']/2),y,axle_z),
               W['diameter'],W['through_bore'],W['width'],mat='wheel')
    boolean(wheel,cyl('Bearing friction seat',(side*(bearing_start+outer_x+.05)/2,y,axle_z),
                      W['bearing_seat_diameter']/2,W['bearing_seat_depth']+.05))
    bearing=ring('MR83ZZ '+tag+' • nominal 3x8x3',(side*(bearing_start+BE['width']/2),y,axle_z),
                 BE['outside_diameter'],BE['bore'],BE['width'],HW,'metal')
    for xx in (bearing_start-.02,bearing_end+.02):
        ring('Bearing shield • illustrative',(side*xx,y,axle_z),7.1,4.3,.02,DETAIL,'shield')
    all_hardware.append(bearing);all_prints.append(wheel)
    single_material(wheel,'wheel')
    if side==1:export_parts.append((wheel,'passive-wheel.stl',True))
    passive_groups.append((side,[o for o in set(bpy.data.objects)-start_objects if o.type=='MESH']))
    wheel_records.append({'corner':tag,'center_xyz':[side*(inner_x+W['width']/2),y,axle_z],'axis':'X','type':'passive'})
    drive=ring('Powered wheel '+('front-left' if side==1 else 'rear-right')+' • CONTEXT ONLY',
               (-side*(inner_x+W['width']/2),y,axle_z),W['diameter'],5,W['width'],DETAIL,'drive')
    all_hardware.append(drive)
    shaft_tip=BASE['servo']['body_axial_height']/2+BASE['servo']['boss_height']+BASE['servo']['shaft_height']
    ring('Powered horn interface • UNDESIGNED ENVELOPE',(-side*(shaft_tip+inner_x)/2,y,axle_z),
         8,4.8,inner_x-shaft_tip,DETAIL,'drive')
    wheel_records.append({'corner':'front-left' if side==1 else 'rear-right',
                          'center_xyz':[-side*(inner_x+W['width']/2),y,axle_z],'axis':'X','type':'powered envelope'})

single_material(chassis, 'chassis')
for part in all_prints:
    clean(part)
    bm=bmesh.new();bm.from_mesh(part.data)
    print('SOLID_AUDIT',part.name,round(bm.calc_volume(signed=True),3),sum(not e.is_manifold for e in bm.edges))
    bm.free()
bpy.context.view_layer.update()


def bounds(o):
    points = [o.matrix_world@Vector(v) for v in o.bound_box]
    return [min(v[i] for v in points) for i in range(3)], [max(v[i] for v in points) for i in range(3)]


def intersects(a, b):
    low_a, high_a = bounds(a)
    low_b, high_b = bounds(b)
    if any(min(high_a[i], high_b[i])-max(low_a[i], low_b[i]) <= .001 for i in range(3)):
        return 0
    dup = a.copy()
    dup.data = a.data.copy()
    scene.collection.objects.link(dup)
    boolean(dup, b, 'INTERSECT', remove=False)
    bm = bmesh.new()
    bm.from_mesh(dup.data)
    vol = abs(bm.calc_volume(signed=True))
    bm.free()
    mesh = dup.data
    bpy.data.objects.remove(dup, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return vol


collisions = []
intentional_fit_intersections = []
for index, a in enumerate(all_prints):
    for b in all_prints[index+1:]+all_hardware:
        vol = intersects(a, b)
        if vol > .01:
            item={'a': a.name, 'b': b.name, 'volume_mm3': round(vol, 4)}
            allowed=0
            if b.name.startswith('MR83ZZ'):
                if a==chassis:
                    allowed=math.pi/4*max(0,A['journal_diameter']**2-BE['bore']**2)*BE['width']
                elif a.name.startswith('Passive press-fit wheel'):
                    allowed=math.pi/4*max(0,BE['outside_diameter']**2-W['bearing_seat_diameter']**2)*BE['width']
            if allowed>0 and vol<=allowed+.02:
                intentional_fit_intersections.append(item)
            else:
                collisions.append(item)
assert not collisions, collisions

# A separate three-pocket coupon makes the bearing fit printable before the wheels.
coupon = box('Bearing fit coupon • 7.9 / 8.0 / 8.1 from notch', (70, 0, 2.5), (40, 14, 5), FIT, 'chassis')
boolean(coupon, box('Coupon orientation notch', (50, 0, 2.5), (2, 3, 7)))
for offset, diameter in zip((-12, 0, 12), P['coupon_seat_diameters']):
    cutter = cyl('Coupon seat', (70+offset, 0, 5-W['bearing_seat_depth']/2+.025), diameter/2, W['bearing_seat_depth']+.05)
    cutter.rotation_euler[1] = math.pi/2
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    boolean(coupon, cutter)
    cutter = cyl('Coupon ejection hole', (70+offset, 0, 2.5), W['through_bore']/2, 7)
    cutter.rotation_euler[1] = math.pi/2
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    boolean(coupon, cutter)
single_material(coupon, 'chassis')
export_parts.append((coupon, 'bearing-fit-coupon.stl', False))
COL[FIT].hide_render = True
coupon.hide_set(True)
axle_coupon=box('Axle fit coupon • 2.9 / 3.0 / 3.1 from notch',(100,0,MT['top_z']/2),(8,38,MT['top_z']),FIT,'chassis')
boolean(axle_coupon,box('Coupon orientation notch',(100,-19,MT['top_z']/2),(3,2,MT['top_z']+2)))
for yy,diameter in zip((-12,0,12),P['coupon_axle_diameters']):
    add_integral_axle(axle_coupon,1,yy,axle_z,104,diameter)
clean(axle_coupon);single_material(axle_coupon,'chassis')
export_parts.append((axle_coupon,'axle-fit-coupon.stl',False));axle_coupon.hide_set(True)


def export(o, filename, turn):
    mesh = o.data.copy()
    mesh.transform(o.matrix_world)
    if turn:
        mesh.transform(Matrix.Rotation(-math.pi/2, 4, 'Y'))
    points = [v.co for v in mesh.vertices]
    low = [min(v[i] for v in points) for i in range(3)]
    high = [max(v[i] for v in points) for i in range(3)]
    translation = Vector((-(low[0]+high[0])/2, -(low[1]+high[1])/2, -low[2]))
    for v in mesh.vertices:
        v.co += translation
        v.co = Vector(tuple(round(value,5) for value in v.co))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00001)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bm.to_mesh(mesh)
    bm.free()
    mesh.calc_loop_triangles()
    path = OUT/filename
    with path.open('wb') as f:
        f.write(b'Diagonal car passive wheel prototype / mm'.ljust(80, b'\0'))
        f.write(struct.pack('<I', len(mesh.loop_triangles)))
        for triangle in mesh.loop_triangles:
            v = [mesh.vertices[i].co for i in triangle.vertices]
            n = (v[1]-v[0]).cross(v[2]-v[0]).normalized()
            f.write(struct.pack('<12fH', *n, *v[0], *v[1], *v[2], 0))
    bpy.data.meshes.remove(mesh)
    result = validate_stl(path)
    result['file'] = filename
    return result


reports = [export(*part) for part in export_parts]
assert all(r['valid'] for r in reports), reports
report = {'revision': P['revision'], 'units': 'mm', 'wheel_axes': wheel_records,
          'axial_retention': 'Friction at both bearing fits; no separate lock or cap',
          'integral_journal_diameter': A['journal_diameter'],
          'servo_clip_to_ear_top_clearance': CL['hook_under_z']-(axle_z+BASE['servo']['body_width']/2),
          'bearing_seat_diametral_clearance': W['bearing_seat_diameter']-BE['outside_diameter'],
          'printed_vs_nominal_hardware_intersections': collisions, 'stl': reports,
          'intentional_fit_intersections': intentional_fit_intersections,
          'scope': 'Nominal static fit only. Friction retention, clip insertion/fatigue, supported axle print accuracy, bearing internals and powered horn interfaces remain unvalidated.'}
(OUT/'validation.json').write_text(json.dumps(report, indent=2)+'\n')

# Studio and saved viewport, using the same reference servo arrangement.
floor = bpy.data.objects['Studio floor']
floor.location.z = axle_z-W['diameter']/2-.7
hero = bpy.data.objects['Pair perspective']
hero.location = (-95, -120, 110)
target = Vector((0, 0, 6))
hero.rotation_euler = (target-hero.location).to_track_quat('-Z', 'Y').to_euler()
hero.data.ortho_scale = 118
top = bpy.data.objects['Pair top view']
top.data.ortho_scale = 110
scene.camera = hero
scene.render.resolution_x = 1500
scene.render.resolution_y = 1100
scene.cycles.samples = 48
scene['design_status'] = 'Integral printed axles and servo clips. Friction-fit prototype; powered wheels are envelopes.'
scene['reference_source'] = P['base_model']
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_distance = 125
        area.spaces.active.region_3d.view_location = target
        area.spaces.active.region_3d.view_rotation = hero.rotation_euler.to_quaternion()
bpy.ops.object.select_all(action='DESELECT')
chassis.select_set(True)
bpy.context.view_layer.objects.active = chassis
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rolling-chassis.blend'), compress=True)
if '--skip-renders' not in sys.argv:
    for camera, filename in ((hero, 'assembly.png'), (top, 'top.png')):
        scene.camera = camera
        scene.render.filepath = str(OUT/filename)
        bpy.ops.render.render(write_still=True)
    hidden=[]
    for obj in bpy.data.objects:
        if obj.type in ('MESH','CURVE','FONT') and obj not in (chassis,floor):
            hidden.append((obj,obj.hide_render));obj.hide_render=True
    prior_floor=floor.location.z;floor.location.z=-.7
    scene.camera=hero
    scene.render.filepath=str(OUT/'chassis-only.png')
    bpy.ops.render.render(write_still=True)
    floor.location.z=prior_floor
    for obj,was_hidden in hidden:obj.hide_render=was_hidden
    # Only the wheel and bearing move in this exploded view; the axle stays integral.
    for side, group in passive_groups:
        if side != -1:
            continue
        for obj in group:
            if obj.name.startswith('Passive wheel'):
                obj.location.x += side*9
            elif obj.name.startswith('MR83ZZ') or obj.name.startswith('Bearing shield'):
                obj.location.x += side*16
    scene.camera = hero
    hero.data.ortho_scale = 130
    hero.rotation_euler = (Vector((-14, 0, 6))-hero.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT/'exploded.png')
    bpy.ops.render.render(write_still=True)
print('ROLLING_BUILD_OK', json.dumps(report))
