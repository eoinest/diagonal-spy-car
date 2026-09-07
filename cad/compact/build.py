"""Build the adjacent, opposing servo pair and a one-piece mounting bracket.

Blender 5.x: blender --background --python-exit-code 1 --python cad/compact/build.py
Add -- --skip-renders to regenerate geometry and validation without PNGs.
Coordinates are millimetres; purchased-part details are nominal/assumed.
"""
import bpy
import bmesh
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
P = json.loads((OUT / 'parameters.json').read_text())
S, B = P['servo'], P['bracket']
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .001
scene.unit_settings.length_unit = 'MILLIMETERS'
collections = {}
for name in ('PRINT • bracket', 'REFERENCE • servo A', 'REFERENCE • servo B', 'DETAIL • labels', 'STUDIO'):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    collections[name] = collection


def material(name, rgb, metal=0, rough=.4):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    return m


mats = {
    'print': material('Printed bracket / orange', (.95, .25, .025)),
    'servo': material('Nominal servo case / deep blue', (.035, .10, .25)),
    'gold': material('Nominal output shaft / brass', (.65, .43, .13), .7),
    'white': material('Reference label', (.85, .92, .97)),
    'floor': material('Studio', (.13, .16, .20)),
}


def move(o, name, collection, material_name=None):
    o.name = name
    for old in list(o.users_collection):
        old.objects.unlink(o)
    collections[collection].objects.link(o)
    if material_name:
        o.data.materials.append(mats[material_name])
    return o


def box(name, location, dimensions, collection='PRINT • bracket', material_name=None, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    o = move(bpy.context.object, name, collection, material_name)
    o.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Soft case corners', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o


def cylinder(name, location, radius, depth, collection='PRINT • bracket', material_name=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=location)
    o = move(bpy.context.object, name, collection, material_name)
    o.rotation_euler[1] = math.pi / 2
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def boolean(o, tool, operation='DIFFERENCE', remove=True):
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new(operation, 'BOOLEAN')
    mod.operation, mod.solver, mod.object = operation, 'EXACT', tool
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if remove:
        bpy.data.objects.remove(tool, do_unlink=True)
    return o


def plate():
    w, length, r, height = (B[k] for k in ('base_width', 'base_length', 'corner_radius', 'floor_thickness'))
    xy = []
    for x, y, start in ((w/2-r, length/2-r, 0), (-w/2+r, length/2-r, 90),
                        (-w/2+r, -length/2+r, 180), (w/2-r, -length/2+r, 270)):
        for i in range(9):
            a = math.radians(start + i * 90 / 8)
            xy.append((x+r*math.cos(a), y+r*math.sin(a)))
    n = len(xy)
    vertices = [(x, y, z) for z in (0, height) for x, y in xy]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new('Bracket solid')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    o = bpy.data.objects.new('servo_pair_bracket', mesh)
    collections['PRINT • bracket'].objects.link(o)
    o.data.materials.append(mats['print'])
    return o


axle_z = B['floor_thickness'] + S['body_width']/2
half_axial = S['body_axial_height']/2
hardware = []
servo_groups = []
flange_clearance = B['lane_spacing'] - (S['ear_span']+S['body_length'])/2
assert flange_clearance > 0, 'Mounting ears intersect the neighboring case; increase lane_spacing.'
assert B['base_length']/2 > B['lane_spacing']/2 + S['ear_span']/2, 'Base is too short.'
bracket = plate()
hole_centers = []
shaft_centers = []

for letter, side, lane in (('A', -1, 1), ('B', 1, -1)):
    collection = 'REFERENCE • servo ' + letter
    center_y = lane * B['lane_spacing']/2
    spindle_y = center_y + lane*S['spindle_offset']
    case = box('Servo '+letter+' • assumed body', (0, center_y, axle_z),
               (S['body_axial_height'], S['body_length'], S['body_width']), collection, 'servo', .35)
    flange = box('Servo '+letter+' • assumed mounting ears', (side*S['ear_axial_offset'], center_y, axle_z),
                 (S['ear_thickness'], S['ear_span'], S['body_width']), collection, 'servo')
    boss = cylinder('Servo '+letter+' • assumed output boss',
                    (side*(half_axial+S['boss_height']/2), spindle_y, axle_z),
                    S['boss_diameter']/2, S['boss_height'], collection, 'servo')
    shaft = cylinder('Servo '+letter+' • assumed output shaft',
                     (side*(half_axial+S['boss_height']+S['shaft_height']/2), spindle_y, axle_z),
                     S['shaft_diameter']/2, S['shaft_height'], collection, 'gold')
    shaft_centers.append([side*(half_axial+S['boss_height']+S['shaft_height']), spindle_y, axle_z])

    # Two short locating rails. The output-side rail has a boss/cable clearance window.
    for rail_side in (-1, 1):
        rail_x = rail_side*(half_axial+B['body_side_clearance']+B['rail_thickness']/2)
        rail = box('Locating rail', (rail_x, center_y, B['floor_thickness']+B['rail_height']/2-.1),
                   (B['rail_thickness'], S['body_length'], B['rail_height']+.2))
        if rail_side == side:
            boolean(rail, box('Output clearance tool', (rail_x, spindle_y, axle_z),
                              (B['rail_thickness']+2, B['output_window_width'], 30)))
        boolean(bracket, rail, 'UNION')

    # Horizontal mounting screws pass through printed posts and the retained servo ears.
    post_x = side*(S['ear_axial_offset']+S['ear_thickness']/2+B['ear_to_post_gap']+B['post_axial_thickness']/2)
    for end in (-1, 1):
        hole_y = center_y + end*S['ear_hole_pitch']/2
        boolean(flange, cylinder('Ear hole', (side*S['ear_axial_offset'], hole_y, axle_z),
                                 S['ear_hole_diameter']/2, S['ear_thickness']+2))
        post_top = axle_z+B['post_above_axle']
        post_bottom = B['floor_thickness']-.2
        post = box('Ear screw support', (post_x, hole_y, (post_top+post_bottom)/2),
                   (B['post_axial_thickness'], B['post_width'], post_top-post_bottom))
        boolean(bracket, post, 'UNION')
        boolean(bracket, cylinder('Mounting screw clearance', (post_x, hole_y, axle_z),
                                  B['screw_clearance_diameter']/2, B['post_axial_thickness']+2))
        hole_centers.append([post_x, hole_y, axle_z])

    # Unite the nominal ears and case to remove coplanar display surfaces.
    boolean(case, flange, 'UNION')
    hardware += [case, boss, shaft]
    servo_groups.append([case, boss, shaft])

    # Labels belong to the reference collection, never to exported print geometry.
    bpy.ops.object.text_add(location=(0, center_y, axle_z+S['body_width']/2+.02))
    text = move(bpy.context.object, 'SERVO '+letter, 'DETAIL • labels', 'white')
    text.data.body, text.data.size = 'SERVO '+letter, 2.1
    text.data.align_x, text.data.align_y = 'CENTER', 'CENTER'


def clean(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00001)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()


clean(bracket.data)
bracket.data.materials.clear()
bracket.data.materials.append(mats['print'])
for polygon in bracket.data.polygons:
    polygon.material_index = 0
bpy.context.view_layer.update()


def intersection_volume(a, b):
    copy = a.copy()
    copy.data = a.data.copy()
    scene.collection.objects.link(copy)
    boolean(copy, b, 'INTERSECT', remove=False)
    bm = bmesh.new()
    bm.from_mesh(copy.data)
    volume = abs(bm.calc_volume(signed=True))
    bm.free()
    mesh = copy.data
    bpy.data.objects.remove(copy, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return volume


collisions = []
for part in hardware:
    volume = intersection_volume(bracket, part)
    if volume > .01:
        collisions.append({'a': bracket.name, 'b': part.name, 'mm3': round(volume, 4)})
for a in servo_groups[0]:
    for b in servo_groups[1]:
        volume = intersection_volume(a, b)
        if volume > .01:
            collisions.append({'a': a.name, 'b': b.name, 'mm3': round(volume, 4)})

bm = bmesh.new()
bm.from_mesh(bracket.data)
non_manifold = sum(not e.is_manifold for e in bm.edges)
remaining = set(bm.verts)
islands = 0
while remaining:
    islands += 1
    stack = [remaining.pop()]
    while stack:
        vertex = stack.pop()
        for edge in vertex.link_edges:
            other = edge.other_vert(vertex)
            if other in remaining:
                remaining.remove(other)
                stack.append(other)
volume = bm.calc_volume(signed=True)
bm.free()
vertices = [bracket.matrix_world@v.co for v in bracket.data.vertices]
dimensions = [round(max(v[i] for v in vertices)-min(v[i] for v in vertices), 3) for i in range(3)]
report = {
    'revision': P['revision'], 'units': 'mm',
    'bracket_size': dimensions, 'bracket_volume_mm3': round(volume, 2),
    'non_manifold_edges': non_manifold, 'connected_components': islands,
    'hardware_intersections': collisions,
    'ear_tip_to_neighbor_case_clearance': round(flange_clearance, 3),
    'rail_to_body_clearance': B['body_side_clearance'],
    'mount_screw_centers_xyz': hole_centers,
    'shaft_tip_centers_xyz': shaft_centers,
    'scope': 'Nominal solid fit/topology only. Hardware dimensions, printer tolerances, screw/nut access, cable exits and mechanical loading require physical validation.'
}
assert non_manifold == 0 and islands == 1 and volume > 0, report
assert not collisions, report

# Export only the single printable object. STL units are mm; base already lies at Z=0.
mesh = bracket.data.copy()
mesh.transform(bracket.matrix_world)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='EAR_CLIP')
bm.to_mesh(mesh)
bm.free()
mesh.calc_loop_triangles()
with (OUT/'servo-pair-bracket.stl').open('wb') as f:
    f.write(b'Adjacent opposing servo bracket; nominal fit prototype; mm'.ljust(80, b'\0'))
    f.write(struct.pack('<I', len(mesh.loop_triangles)))
    for tri in mesh.loop_triangles:
        vs = [mesh.vertices[i].co for i in tri.vertices]
        normal = (vs[1]-vs[0]).cross(vs[2]-vs[0]).normalized()
        f.write(struct.pack('<12fH', *normal, *vs[0], *vs[1], *vs[2], 0))
bpy.data.meshes.remove(mesh)

# Audit the actual float32 STL after serialization, not only Blender's polygon mesh.
data = (OUT/'servo-pair-bracket.stl').read_bytes()
triangle_count = struct.unpack_from('<I', data, 80)[0]
assert len(data) == 84 + 50*triangle_count
edges, signed_edges = Counter(), Counter()
stl_vertices, stl_faces = {}, []
degenerate = 0
for index in range(triangle_count):
    values = struct.unpack_from('<12fH', data, 84+50*index)
    coords = [tuple(values[start:start+3]) for start in (3, 6, 9)]
    ids = [stl_vertices.setdefault(v, len(stl_vertices)) for v in coords]
    stl_faces.append(ids)
    area2 = (Vector(coords[1])-Vector(coords[0])).cross(Vector(coords[2])-Vector(coords[0])).length
    degenerate += int(len(set(ids)) < 3 or area2 < .000001)
    for a, b in zip(ids, ids[1:]+ids[:1]):
        edge = tuple(sorted((a, b)))
        edges[edge] += 1
        signed_edges[edge] += 1 if a < b else -1
neighbors = {i: set() for i in stl_vertices.values()}
for a, b in edges:
    neighbors[a].add(b)
    neighbors[b].add(a)
unvisited, stl_islands = set(neighbors), 0
while unvisited:
    stl_islands += 1
    stack = [unvisited.pop()]
    while stack:
        for neighbor in neighbors[stack.pop()]:
            if neighbor in unvisited:
                unvisited.remove(neighbor)
                stack.append(neighbor)
stl_report = {
    'triangles': triangle_count,
    'non_manifold_edges': sum(count != 2 for count in edges.values()),
    'inconsistent_edge_winding': sum(count != 0 for count in signed_edges.values()),
    'degenerate_triangles': degenerate,
    'connected_components': stl_islands,
}
report['serialized_stl'] = stl_report
(OUT/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
assert stl_report['non_manifold_edges'] == 0 and stl_report['inconsistent_edge_winding'] == 0, stl_report
assert degenerate == 0 and stl_islands == 1, stl_report

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'AgX'
box('Studio floor', (0, 0, -.7), (1000, 1000, 1.2), 'STUDIO', 'floor')


def aim(o, target):
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()


def camera(name, location, target, scale):
    bpy.ops.object.camera_add(location=location)
    o = move(bpy.context.object, name, 'STUDIO')
    o.data.type, o.data.ortho_scale = 'ORTHO', scale
    aim(o, target)
    return o


hero = camera('Pair perspective', (-85, -105, 110), (0, 0, 6), 100)
top = camera('Pair top view', (0, 0, 150), (0, 0, 0), 94)
for name, location, energy, size in (
    ('Key', (-60, 30, 100), 150000, 75),
    ('Fill', (70, -20, 80), 110000, 60),
    ('Rim', (0, 80, 80), 120000, 60),
):
    bpy.ops.object.light_add(type='AREA', location=location)
    o = move(bpy.context.object, name, 'STUDIO')
    o.data.energy, o.data.size = energy, size
    aim(o, (0, 0, 5))
scene.camera = hero
scene['design_status'] = 'First compact servo bracket. Nominal/assumed geometry, not physically fit-tested.'
scene['front'] = '+Y; output shafts -X at +Y and +X at -Y'
scene['source_parameters'] = 'cad/compact/parameters.json'
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.region_3d.view_distance = 110
        space.region_3d.view_location = Vector((0, 0, 7))
        space.region_3d.view_rotation = hero.rotation_euler.to_quaternion()
        space.clip_end = 5000
        space.overlay.show_floor = False
bpy.ops.object.select_all(action='DESELECT')
bracket.select_set(True)
bpy.context.view_layer.objects.active = bracket
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'servo-pair.blend'), compress=True)
if '--skip-renders' not in sys.argv:
    for cam, filename in ((hero, 'assembly.png'), (top, 'top.png')):
        scene.camera = cam
        scene.render.filepath = str(OUT/filename)
        bpy.ops.render.render(write_still=True)
    for collection_name in ('REFERENCE • servo A', 'REFERENCE • servo B', 'DETAIL • labels'):
        collections[collection_name].hide_render = True
    scene.camera = hero
    scene.render.filepath = str(OUT/'bracket.png')
    bpy.ops.render.render(write_still=True)
print('COMPACT_BUILD_OK', json.dumps(report))
