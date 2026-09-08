"""Same-scale orthographic battery reference; build() never saves or renders."""

import math

import bpy
from mathutils import Matrix, Vector


def build(assembled):
    """Return (scene, camera), copying only battery objects from assembled.

    The assembled pack's long axis must be world X, width Y and height Z.
    Dimension labels describe the published nominal envelope, not measured fit.
    """
    name = '03 BATTERY DIMENSIONS'
    old = bpy.data.scenes.get(name)
    if old:
        bpy.data.scenes.remove(old)
    source = [o for o in assembled.objects if o.name.startswith('Battery •')]
    wrap = next((o for o in source if '2S wrap' in o.name), None)
    if wrap is None:
        raise ValueError('Battery view requires the assembled Lumenier wrap object')
    # Include the raised label and all finished-pack surfaces when centering.
    # The wrap alone is slightly shorter than the nominal finished pack height.
    corners = [o.matrix_world @ Vector(p) for o in source for p in o.bound_box]
    center = Vector(tuple((min(p[i] for p in corners) + max(p[i] for p in corners))/2
                          for i in range(3)))
    size = tuple(max(p[i] for p in corners)-min(p[i] for p in corners)
                 for i in range(3))
    if abs(size[0]-48) > .05 or abs(size[1]-17) > .05:
        raise ValueError('Battery dimensions view expects world-X 48 mm / world-Y 17 mm')

    scene = bpy.data.scenes.new(name)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = .001
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene['source'] = 'https://www.lumenier.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30'
    scene['dimension_basis'] = 'Published nominal 48 x 17 x 12 mm; leads/connectors excluded'
    scene['copied_finished_pack_bounds_mm'] = list(size)
    scene['projection'] = 'Top and side orthographic; identical scale; no geometry rescaling'
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.render.filepath = '//battery-dimensions.png'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    world = bpy.data.worlds.new(name + ' world')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.85, .9, 1, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
    scene.world = world

    def emission(label, color):
        material = bpy.data.materials.new('Battery drawing / ' + label)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial')
        shader = nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = (*color, 1)
        shader.inputs['Strength'].default_value = 1
        material.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
        return material

    ink = emission('ink', (.035, .055, .085))
    gray = emission('secondary', (.23, .29, .35))
    white = emission('paper', (1, 1, 1))

    def link(obj):
        scene.collection.objects.link(obj)
        return obj

    def label(text, x, y, size=2.1, align='CENTER', rotation=0, material=ink):
        data = bpy.data.curves.new('Dimension text / ' + text, 'FONT')
        data.body = text
        data.size = size
        data.align_x = align
        data.align_y = 'CENTER'
        data.materials.append(material)
        obj = link(bpy.data.objects.new('Dimension / ' + text, data))
        obj.location = (x, y, 15)
        obj.rotation_euler.z = rotation
        return obj

    def line(points, material=gray, thickness=.08):
        data = bpy.data.curves.new('Dimension stroke', 'CURVE')
        data.dimensions = '3D'
        data.bevel_depth = thickness/2
        data.bevel_resolution = 0
        spline = data.splines.new('POLY')
        spline.points.add(len(points)-1)
        for p, (x, y) in zip(spline.points, points):
            p.co = (x, y, 14, 1)
        data.materials.append(material)
        return link(bpy.data.objects.new('Dimension stroke', data))

    def arrow(x, y, dx, dy):
        # Open arrow, with its tip touching the extension line.
        length, half_width = 1.25, .38
        line([(x+dx*length-dy*half_width, y+dy*length+dx*half_width),
              (x, y),
              (x+dx*length+dy*half_width, y+dy*length-dx*half_width)], ink, .11)

    def horizontal(y_edge, y_dim, label_y):
        left, right = -27, 21
        sign = 1 if y_dim > y_edge else -1
        for x in (left, right):
            line([(x, y_edge+sign*.7), (x, y_dim+sign*.7)])
        line([(left, y_dim), (right, y_dim)])
        arrow(left, y_dim, 1, 0)
        arrow(right, y_dim, -1, 0)
        label('48 mm', -3, label_y)

    def vertical(y_bottom, y_top, text):
        x_edge, x_dim = 21, 29
        for y in (y_bottom, y_top):
            line([(x_edge+.7, y), (x_dim+.7, y)])
        line([(x_dim, y_bottom), (x_dim, y_top)])
        arrow(x_dim, y_bottom, 0, 1)
        arrow(x_dim, y_top, 0, -1)
        label(text, x_dim+2.7, (y_bottom+y_top)/2, rotation=math.pi/2)

    for view, destination, rotation in [
            ('TOP', Vector((-3, 12, 0)), Matrix.Identity(4)),
            ('SIDE', Vector((-3, -16, 0)), Matrix.Rotation(-math.pi/2, 4, 'X'))]:
        # For side projection, +Z becomes page +Y. Viewing is from world -Y.
        transform = Matrix.Translation(destination) @ rotation @ Matrix.Translation(-center)
        collection = bpy.data.collections.new('Battery drawing / ' + view)
        scene.collection.children.link(collection)
        for original in source:
            obj = original.copy()
            obj.name = view + ' reference / ' + original.name
            obj.parent = None
            obj.matrix_world = transform @ original.matrix_world
            obj.hide_render = False
            obj.hide_viewport = False
            collection.objects.link(obj)

    label('LUMENIER 300 mAh 2S - NOMINAL PACK DIMENSIONS', 0, 35, 2.5)
    label('Same-scale orthographic views  |  millimetres  |  pouch and wrap only', 0, 30.7, 1.7, material=gray)
    label('TOP', -49, 12, 2.2)
    label('SIDE', -49, -16, 2.2)
    horizontal(20.5, 24.5, 26.4)
    vertical(3.5, 20.5, '17 mm')
    horizontal(-22, -26, -28.1)
    vertical(-22, -10, '12 mm')
    label('Source: Lumenier.com product listing, SKU 10188; published nominal dimensions.', 0, -34, 1.45, material=gray)
    label('Leads and connectors excluded. Wrap details approximate; measure the actual pack before print fit.', 0, -37, 1.45, material=gray)

    mesh = bpy.data.meshes.new('Battery drawing paper')
    mesh.from_pydata([(-90, -60, -24), (90, -60, -24), (90, 60, -24), (-90, 60, -24)], [], [(0, 1, 2, 3)])
    mesh.materials.append(white)
    link(bpy.data.objects.new('Battery drawing paper', mesh))
    for name_suffix, position, energy, size in [('key', (-30, 15, 65), 100000, 65),
                                                 ('fill', (35, -5, 50), 55000, 55)]:
        data = bpy.data.lights.new('Battery drawing ' + name_suffix, 'AREA')
        data.energy = energy
        data.shape = 'DISK'
        data.size = size
        light = link(bpy.data.objects.new(data.name, data))
        light.location = position
        light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data = bpy.data.cameras.new('Battery dimensions orthographic')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 128
    camera_data.clip_start = .1
    camera_data.clip_end = 500
    camera = link(bpy.data.objects.new('Battery dimensions orthographic', camera_data))
    camera.location = (0, 0, 150)
    scene.camera = camera
    return scene, camera
