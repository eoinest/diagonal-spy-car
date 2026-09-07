"""Add aligned bearing-supported passive wheels to the saved compact servo pair.

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
BE, A, MT, W, SP = (P[k] for k in ('bearing', 'axle', 'mount', 'wheel', 'spacers'))
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
    'metal': material('Bearing and axle / steel', (.55, .62, .69), .8),
    'shield': material('Bearing shield detail', (.16, .21, .25), .65),
    'spacer': material('Inner-ring spacer', (.8, .68, .38), .3),
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
    bm.to_mesh(o.data)
    bm.free()


chassis = bpy.data.objects['servo_pair_bracket']
chassis.name = 'rolling_chassis'
all_prints = [chassis]
all_hardware = [o for c in bpy.data.collections if c.name.startswith('REFERENCE • servo') for o in c.objects if o.type == 'MESH']
export_parts = [(chassis, 'rolling-chassis.stl', False)]
passive_groups = []
wheel_records = []
inner_x = W['inner_face_x']
outer_x = inner_x+W['width']
bearing_start = outer_x-W['bearing_seat_depth']
bearing_end = bearing_start+BE['width']
shoulder_start = MT['outer_face_x']-MT['shoulder_recess_depth']
head_start = shoulder_start+A['shoulder_length']
cap_end = outer_x+W['cap_thickness']
axle_z = BASE['bracket']['floor_thickness']+BASE['servo']['body_width']/2
axle_y = BASE['bracket']['lane_spacing']/2+BASE['servo']['spindle_offset']
assert abs(MT['outer_face_x']+SP['inner_length']-bearing_start) < .0001
endplay = head_start-(bearing_end+SP['outer_length'])
assert endplay >= .15, 'Axial stack must leave clearance, not preload the bearing.'
assert W['through_bore'] > A['head_diameter'], 'Retainer must clear the stationary screw head.'
assert W['diameter'] < 2*axle_y, 'Front and rear wheels overlap.'
for letter, sign in (('A', 1), ('B', -1)):
    saved_shaft = bpy.data.objects['Servo '+letter+' • assumed output shaft']
    assert abs(saved_shaft.location.y-sign*axle_y) < .001 and abs(saved_shaft.location.z-axle_z) < .001, 'Rebuild compact model after changing its parameters.'

for side in (1, -1):
    y = side*axle_y
    tag = 'front-right' if side == 1 else 'rear-left'
    start_objects = set(bpy.data.objects)
    # A short fixed support sits outside the non-output end of the opposite servo.
    block = box('Stub axle support', (side*(MT['inner_face_x']+MT['outer_face_x'])/2, y, MT['top_z']/2),
                (MT['outer_face_x']-MT['inner_face_x'], MT['width_y'], MT['top_z']))
    boolean(chassis, block, 'UNION')
    boolean(chassis, cyl('Axle thread passage', (side*(MT['inner_face_x']+MT['outer_face_x'])/2, y, axle_z),
                        MT['thread_clearance']/2, MT['outer_face_x']-MT['inner_face_x']+4))
    recess_depth = MT['shoulder_recess_depth']
    boolean(chassis, cyl('Smooth shoulder socket', (side*(MT['outer_face_x']-recess_depth/2+.01), y, axle_z),
                        MT['shoulder_bore']/2, recess_depth+.02))
    # Nut drops into a top-access channel; no inaccessible nut against the servo case.
    slot = cyl('M2 nut hex pocket', (side*MT['nut_center_x'], y, axle_z),
               MT['nut_across_flats_clearance']/math.sqrt(3), MT['nut_slot_width_x'], vertices=6)
    boolean(chassis, slot)
    boolean(chassis, box('Nut top access', (side*MT['nut_center_x'], y, (axle_z+MT['top_z']+1)/2),
                        (MT['nut_slot_width_x'], MT['nut_across_flats_clearance'], MT['top_z']+1-axle_z)))

    wheel = ring('Passive wheel '+tag, (side*(inner_x+W['width']/2), y, axle_z), W['diameter'], W['through_bore'], W['width'], mat='wheel')
    boolean(wheel, cyl('Bearing counterbore', (side*(bearing_start+outer_x+.05)/2, y, axle_z),
                      W['bearing_seat_diameter']/2, W['bearing_seat_depth']+.05))
    cap = ring('Bearing retainer '+tag, (side*(outer_x+W['cap_thickness']/2), y, axle_z),
               W['cap_diameter'], W['through_bore'], W['cap_thickness'], mat='wheel')
    # Three replaceable cap screws retain the outer race; their threads bite the wheel only.
    for angle in (0, 2*math.pi/3, 4*math.pi/3):
        yy = y+W['cap_screw_radius']*math.cos(angle)
        zz = axle_z+W['cap_screw_radius']*math.sin(angle)
        boolean(wheel, cyl('Cap screw pilot', (side*(inner_x+W['width']/2), yy, zz), W['cap_screw_pilot']/2, W['width']+2))
        boolean(cap, cyl('Cap screw clearance', (side*(outer_x+W['cap_thickness']/2), yy, zz), W['cap_screw_clearance']/2, W['cap_thickness']+2))
        head = cyl('M2 cap screw head • envelope', (side*(cap_end+.8), yy, zz), 1.8, 1.6, HW, 'metal')
        shank = cyl('M2 cap screw thread • illustrative', (side*(cap_end-W['cap_screw_length']/2), yy, zz),
                    1, W['cap_screw_length'], DETAIL, 'metal')
        all_hardware.append(head)
    bearing = ring('MR83ZZ '+tag+' • nominal 3x8x3', (side*(bearing_start+BE['width']/2), y, axle_z),
                   BE['outside_diameter'], BE['bore'], BE['width'], HW, 'metal')
    # Shield faces are only illustrative; envelope alone establishes nominal bearing fit.
    for xx in (bearing_start-.02, bearing_end+.02):
        ring('Bearing shield • illustrative', (side*xx, y, axle_z), 7.1, 4.3, .02, DETAIL, 'shield')
    in_spacer = ring('Inner spacer '+tag, (side*(MT['outer_face_x']+SP['inner_length']/2), y, axle_z),
                     SP['outside_diameter'], SP['bore'], SP['inner_length'], mat='spacer')
    out_spacer = ring('Outer spacer '+tag, (side*(bearing_end+SP['outer_length']/2), y, axle_z),
                      SP['outside_diameter'], SP['bore'], SP['outer_length'], mat='spacer')
    axle = cyl('3mm smooth shoulder '+tag, (side*(shoulder_start+A['shoulder_length']/2), y, axle_z),
               A['shoulder_diameter']/2, A['shoulder_length'], HW, 'metal')
    thread = cyl('M2 axle thread '+tag+' • envelope', (side*(shoulder_start-A['thread_length']/2), y, axle_z),
                 A['thread_diameter']/2, A['thread_length'], HW, 'metal')
    axle_head = cyl('Axle head '+tag, (side*(head_start+A['head_height']/2), y, axle_z),
                    A['head_diameter']/2, A['head_height'], HW, 'metal')
    boolean(axle_head, cyl('2mm hex socket', (side*(head_start+A['head_height']-.55), y, axle_z),
                          A['socket_across_flats']/math.sqrt(3), 1.3, vertices=6))
    nut = cyl('M2 captured nut '+tag+' • nominal envelope', (side*MT['nut_center_x'], y, axle_z), 4/math.sqrt(3), 1.6, HW, 'metal', vertices=6)
    boolean(nut, cyl('Nut thread envelope', (side*MT['nut_center_x'], y, axle_z), 1.1, 3))
    all_hardware += [bearing, axle, thread, axle_head, nut]
    parts = [wheel, cap, in_spacer, out_spacer]
    all_prints += parts
    for obj in parts:
        single_material(obj, 'wheel' if obj in (wheel, cap) else 'spacer')
    if side == 1:
        export_parts += [(wheel, 'passive-wheel.stl', True), (cap, 'bearing-retainer.stl', True),
                         (in_spacer, 'inner-spacer-2p8.stl', True), (out_spacer, 'outer-spacer-1p0.stl', True)]
    group = [o for o in set(bpy.data.objects)-start_objects if o.type == 'MESH']
    passive_groups.append((side, group))
    wheel_records.append({'corner': tag, 'center_xyz': [side*(inner_x+W['width']/2), y, axle_z], 'axis': 'X', 'type': 'passive'})

    # Opposite powered wheel is a dimensioned context envelope, not a finished horn mount.
    drive = ring('Powered wheel '+('front-left' if side == 1 else 'rear-right')+' • CONTEXT ONLY',
                 (-side*(inner_x+W['width']/2), y, axle_z), W['diameter'], 5, W['width'], DETAIL, 'drive')
    all_hardware.append(drive)
    shaft_tip = BASE['servo']['body_axial_height']/2+BASE['servo']['boss_height']+BASE['servo']['shaft_height']
    ring('Powered horn interface • UNDESIGNED ENVELOPE', (-side*(shaft_tip+inner_x)/2, y, axle_z),
         8, 4.8, inner_x-shaft_tip, DETAIL, 'drive')
    wheel_records.append({'corner': 'front-left' if side == 1 else 'rear-right',
                          'center_xyz': [-side*(inner_x+W['width']/2), y, axle_z], 'axis': 'X', 'type': 'powered envelope'})

single_material(chassis, 'chassis')
for part in all_prints:
    clean(part)
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
for index, a in enumerate(all_prints):
    for b in all_prints[index+1:]+all_hardware:
        vol = intersects(a, b)
        if vol > .01:
            collisions.append({'a': a.name, 'b': b.name, 'volume_mm3': round(vol, 4)})
assert not collisions, collisions

# A separate three-pocket coupon makes the bearing fit printable before the wheels.
coupon = box('Bearing fit coupon • 8.0 / 8.1 / 8.2 left to right', (70, 0, 2.5), (40, 14, 5), FIT, 'chassis')
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
          'nominal_axial_endplay': round(endplay, 3),
          'bearing_outer_race_retainer_gap': round(outer_x-bearing_end, 3),
          'bearing_seat_diametral_clearance': W['bearing_seat_diameter']-BE['outside_diameter'],
          'printed_vs_nominal_hardware_intersections': collisions, 'stl': reports,
          'scope': 'Nominal solids only. Cap screw threads intentionally engage printed pilots and are excluded. Bearing internals, powered horn mounts, wiring, tolerances and loaded driving behavior remain unvalidated.'}
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
scene['design_status'] = 'Aligned passive bearing wheel prototype. Powered wheels are envelopes; no powered hub STL.'
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
    # Explode the near passive hub axially to expose its bearing, spacers and fixed axle.
    for side, group in passive_groups:
        if side != -1:
            continue
        for obj in group:
            if obj.name.startswith('Passive wheel'):
                obj.location.x += side*9
            elif obj.name.startswith('MR83ZZ') or obj.name.startswith('Bearing shield'):
                obj.location.x += side*16
            elif obj.name.startswith('Bearing retainer'):
                obj.location.x += side*23
            elif obj.name.startswith('Outer spacer'):
                obj.location.x += side*28
            elif obj.name.startswith('Axle head') or obj.name.startswith('3mm smooth') or obj.name.startswith('M2 axle thread'):
                obj.location.x += side*36
            elif obj.name.startswith('M2 cap screw'):
                obj.location.x += side*30
    scene.camera = hero
    hero.data.ortho_scale = 150
    hero.rotation_euler = (Vector((-14, 0, 6))-hero.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT/'exploded.png')
    bpy.ops.render.render(write_still=True)
print('ROLLING_BUILD_OK', json.dumps(report))
