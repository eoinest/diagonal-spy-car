"""Detailed nominal electronics references for the complete Blender assembly.

build(P) preserves the caller's scene and creates only reference collections.
Coordinates are millimetres. Long board axes are +Y; S2 antenna +Y / USB -Y.
Published envelopes do not establish measured fit of the user's parts. Feature
positions without a mechanical drawing are explicitly marked as assumptions.
"""
import math
import bpy

WEMOS = 'https://docs.wemos.cc/en/latest/s2/s2_mini.html'
WEMOS_DIM = 'https://docs.wemos.cc/en/latest/_static/files/dim_s2_mini_v1.0.0.pdf'
ESP_PACKAGE = 'https://documentation.espressif.com/esp32-s2_datasheet_en.pdf#page=58'
KICAD = 'https://gitlab.com/kicad/libraries/kicad-footprints/-/merge_requests/2904'
BATTERY_SOURCE = 'https://www.racedayquads.com/products/lumenier-300mah-2s-75c-lipo-battery-xt-30'
BUCK_SOURCE = 'User photograph: electronics/guide-assets/owned-buck.jpg; board size and feature dimensions provisional'


def build(P):
    """Return {'groups': {battery,buck,s2: [objects]}, 'terminals': {...}}.

    Terminal positions are world coordinates before any caller rotation. They
    identify illustrative solder/lead locations, not a measured connector pinout.
    The buck polarity follows the readable owned photograph: both positive pads
    are left in top view with the output at +Y. Every object has source and
    dimension_status custom properties. No external leads/connectors are added.
    """
    groups = {name: [] for name in ('battery', 'buck', 's2')}
    cols = {}
    for key, label in [('battery', 'Battery'), ('buck', 'Owned adjustable buck'), ('s2', 'LOLIN S2 Mini')]:
        col = bpy.data.collections.new('REFERENCE • complete • ' + label)
        bpy.context.scene.collection.children.link(col)
        cols[key] = col
    sources = {'battery': BATTERY_SOURCE, 'buck': BUCK_SOURCE, 's2': WEMOS}
    assumed = 'Nominal appearance / feature placement; not physically measured'

    def material(key, rgb, metallic=0.0, roughness=.4):
        name = 'Complete electronics / ' + key
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
            m.use_nodes = True
        m.diffuse_color = (*rgb, 1)
        bs = m.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value = (*rgb, 1)
        bs.inputs['Metallic'].default_value = metallic
        bs.inputs['Roughness'].default_value = roughness
        return m

    mats = {
        'wrap': material('black shrink wrap', (.025, .034, .044), .03, .3),
        'cell': material('silver pouch', (.38, .42, .46), .65, .35),
        'label': material('battery label', (.027, .09, .15)),
        'cyan': material('label cyan', (.005, .58, .82)),
        'violet': material('LOLIN violet FR4', (.23, .025, .48)),
        'blue': material('converter blue FR4', (.015, .065, .14)),
        'trimmer': material('blue trimmer', (.025, .12, .4)),
        'gold': material('gold plated pad', (.72, .43, .1), .75, .28),
        'silver': material('tin and steel', (.58, .64, .7), .8, .28),
        'black': material('molded component', (.012, .017, .024), 0, .5),
        'ferrite': material('ferrite', (.09, .1, .12), .1, .7),
        'white': material('silkscreen', (.88, .91, .91), 0, .6),
        'ceramic': material('ceramic capacitor', (.39, .32, .2), 0, .55),
        'trace': material('soldermask trace relief', (.32, .075, .53), .05, .55),
    }

    def register(o, name, group, mat, status=assumed, source=None, track=True):
        o.name = name
        for col in list(o.users_collection):
            col.objects.unlink(o)
        cols[group].objects.link(o)
        if mat:
            o.data.materials.append(mats[mat])
        o['dimension_status'] = status
        o['source'] = source or sources[group]
        o['model_role'] = 'Purchased component reference; not a printable part'
        o['units'] = 'mm'
        if track:
            groups[group].append(o)
        return o

    def box(name, loc, dim, group, mat, radius=0, status=assumed, source=None, track=True):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = register(bpy.context.object, name, group, mat, status, source, track)
        o.dimensions = dim
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if radius:
            mod = o.modifiers.new('Rounded case edges', 'BEVEL')
            mod.width = min(radius, min(dim)/2-.0001)
            mod.segments = 4
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return o

    def cylinder(name, loc, radius, height, group, mat, axis='Z', status=assumed, track=True):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=height, location=loc)
        o = register(bpy.context.object, name, group, mat, status, track=track)
        if axis == 'Y':
            o.rotation_euler.x = math.pi/2
        elif axis == 'X':
            o.rotation_euler.y = math.pi/2
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return o

    def subtract(o, cutter):
        bpy.context.view_layer.objects.active = o
        mod = o.modifiers.new('True opening', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)

    def bore(o, x, y, z, radius, depth, group):
        subtract(o, cylinder('temporary drill', (x, y, z), radius, depth, group, None, track=False))

    def polygon_plate(name, points, bottom, thickness, group, mat, status=assumed, source=None):
        # Remove duplicated arc endpoints before making the closed planar mesh.
        clean = []
        for p in points:
            if not clean or math.dist(p, clean[-1]) > 1e-6:
                clean.append(p)
        if len(clean) > 1 and math.dist(clean[0], clean[-1]) < 1e-6:
            clean.pop()
        n = len(clean)
        verts = [(x, y, z) for z in (bottom, bottom+thickness) for x, y in clean]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
        faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
        mesh = bpy.data.meshes.new(name + ' mesh')
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        o = bpy.data.objects.new(name, mesh)
        return register(o, name, group, mat, status, source)

    def rounded_points(cx, cy, width, length, radius):
        pts = []
        for x, y, start in [(width/2-radius, length/2-radius, 0),
                            (-width/2+radius, length/2-radius, 90),
                            (-width/2+radius, -length/2+radius, 180),
                            (width/2-radius, -length/2+radius, 270)]:
            for i in range(9):
                a = math.radians(start+i*90/8)
                pts.append((cx+x+radius*math.cos(a), cy+y+radius*math.sin(a)))
        return pts

    def text(name, value, loc, size, group, mat='white', angle=0, align='CENTER'):
        bpy.ops.object.text_add(location=loc)
        o = register(bpy.context.object, name, group, mat)
        o.data.body = value
        o.data.size = size
        o.data.align_x = align
        o.data.align_y = 'CENTER'
        o.data.extrude = .001
        o.rotation_euler.z = angle
        return o

    def pad(name, x, y, ztop, pcb, group, outer=.9, drill=.46, square=False):
        # Drill the PCB itself, not just a decorative ring resting on solid FR4.
        bore(pcb, x, y, ztop-.8, drill, 5, group)
        for face_z in (ztop+.026, ztop-pcb.get('pcb_thickness', 1.6)-.026):
            if square:
                ring = box(name, (x, y, face_z), (outer*2, outer*2, .05), group, 'gold', .05)
            else:
                ring = cylinder(name, (x, y, face_z), outer, .05, group, 'gold')
            bore(ring, x, y, face_z, drill, .5, group)
        return [x, y, ztop+.06]

    def smd(name, x, y, z, length, width, height, group, kind='black'):
        box(name, (x, y, z+height/2), (length, width, height), group, kind, .035)
        for side in (-1, 1):
            box(name+' termination', (x+side*(length/2-.1), y, z+.12), (.22, width+.06, .24), group, 'silver')

    # Battery: separate illustrative cell pouches inside an accurately bounded wrap.
    b = P['battery']
    bx, by, bz = b['center']
    bw, bl, bh = b['width'], b['length'], b['height']
    cell_h = (bh-1.2)/2
    for n, offset in [(1, -(cell_h+.12)/2), (2, (cell_h+.12)/2)]:
        box('Battery • internal cell %d envelope' % n, (bx, by, bz+offset),
            (bw-.8, bl-3, cell_h), 'battery', 'cell', .5,
            'Illustrative two-cell stack within total pack envelope; no internal construction metrology')
    wrap = box('Battery • Lumenier 300 mAh 2S wrap', (bx, by, bz), (bw, bl, bh-.16),
               'battery', 'wrap', .7, 'Published 48×17×12 mm pack envelope; wrap/seams illustrative')
    inner = box('temporary wrap cavity', (bx, by, bz), (bw-.35, bl-.5, bh-.5),
                'battery', None, .5, track=False)
    subtract(wrap, inner)
    for side in (-1, 1):
        box('Battery • sealed end seam', (bx, by+side*(bl/2-.45), bz),
            (bw-.5, .55, bh-.5), 'battery', 'wrap', .12)
    label_z = bz+bh/2-.045
    box('Battery • printed label backing', (bx, by+.2, label_z), (bw-1.7, bl-6, .045), 'battery', 'label', .015)
    box('Battery • cyan capacity field', (bx, by+bl*.19, label_z+.03), (bw-2.5, bl*.26, .014), 'battery', 'cyan')
    text('Battery • capacity marking', '300', (bx, by+bl*.19, label_z+.04), 5.0, 'battery')
    text('Battery • capacity units', 'mAh', (bx, by+bl*.065, label_z+.04), 1.5, 'battery')
    text('Battery • brand marking', 'Lumenier', (bx, by-bl*.085, label_z+.04), 2.5, 'battery')
    text('Battery • chemistry marking', '2S  7.4V', (bx, by-bl*.21, label_z+.04), 1.8, 'battery')
    text('Battery • chemistry marking small', 'LiPo  /  XT30', (bx, by-bl*.29, label_z+.04), 1.3, 'battery')
    terminals = {'battery': {
        'positive': [bx+2.2, by-bl/2, bz+1.0],
        'negative': [bx-2.2, by-bl/2, bz+1.0],
        'balance_lead_exit': [bx, by-bl/2, bz-2.0],
    }}

    # Converter: standard long module, photographic arrangement and assumed size.
    r = P['buck']
    rx, ry = r['center_xy']
    rw, rl, rt, rb = r['width'], r['length'], r['pcb_thickness'], r['pcb_bottom']
    rz = rb+rt
    pcb = polygon_plate('Buck • blue PCB', rounded_points(rx, ry, rw, rl, .7), rb, rt, 'buck', 'blue')
    pcb['pcb_thickness'] = rt
    pcb['dimension_status'] = '43×21 mm planning board envelope; PCB thickness1.6 mm assumed; verify owned board'
    t = {}
    for name, xx, yy in [('IN+', -rw/2+1.6, -rl/2+1.6), ('IN-', rw/2-1.6, -rl/2+1.6),
                         ('OUT+', -rw/2+1.6, rl/2-1.6), ('OUT-', rw/2-1.6, rl/2-1.6)]:
        t[name] = pad('Buck • '+name+' solder pad', rx+xx, ry+yy, rz, pcb, 'buck', 1.25, .62, square=True)
        text('Buck • '+name+' silk', name, (rx+xx+(-1 if xx>0 else 1)*2.3, ry+yy, rz+.075),
             1.15, 'buck', angle=math.pi/2)
    for xx, yy in [(-rw/2+3.0, -rl/2+6.4), (rw/2-3.0, rl/2-6.4)]:
        bore(pcb, rx+xx, ry+yy, rz-.8, 1.55, 5, 'buck')
        ring = cylinder('Buck • mounting-hole silk ring', (rx+xx, ry+yy, rz+.028), 2, .04, 'buck', 'white')
        bore(ring, rx+xx, ry+yy, rz, 1.7, .5, 'buck')
    # Aluminum electrolytics have molded pedestals, metal lids and scored vents.
    available_h = r['height']-rt
    cap_h = min(10.8, available_h-.45)
    for name, xx, yy, legend in [('Output', 0.0, rl/2-6.1, '220\n35V'),
                                ('Input', .7, -rl/2+6.1, '100\n50V')]:
        x, y = rx+xx, ry+yy
        box('Buck • '+name+' capacitor pedestal', (x, y, rz+.22), (8.8, 8.8, .44), 'buck', 'black', .15)
        cylinder('Buck • '+name+' capacitor sleeve', (x, y, rz+.44+cap_h/2), 4.2, cap_h, 'buck', 'black')
        top = rz+.44+cap_h
        lid = cylinder('Buck • '+name+' capacitor aluminum lid', (x, y, top-.07), 3.92, .12, 'buck', 'silver')
        for axis in (0, math.pi/2):
            groove = box('temporary vent groove', (x, y, top-.005), (5.6, .08, .1), 'buck', None, track=False)
            groove.rotation_euler.z = axis
            subtract(lid, groove)
        text('Buck • '+name+' capacitor legend', legend, (x, y, top+.002), 1.55, 'buck', 'black')
    # Shielded 470 inductor, with space beside it for the W103 trimmer.
    ix, iy = rx+2.5, ry+3.0
    ih = min(7.2, available_h-.4)
    box('Buck • 470 inductor square base', (ix, iy, rz+ih/2), (12.5, 12.5, ih), 'buck', 'black', .65)
    cylinder('Buck • inductor ferrite center', (ix, iy, rz+ih+.04), 4.95, .12, 'buck', 'ferrite')
    text('Buck • inductor value', '470', (ix, iy, rz+ih+.11), 3.2, 'buck', 'black')
    tx, ty = rx-7.4, ry+3.2
    box('Buck • W103 multiturn trimmer', (tx, ty, rz+2.4), (4.2, 10.3, 4.8), 'buck', 'trimmer', .15)
    text('Buck • W103 marking', 'W103', (tx, ty+1, rz+4.85), 1.45, 'buck', 'black', angle=math.pi/2)
    screw = cylinder('Buck • voltage adjustment screw', (tx, ty-3.55, rz+5.0), 1.28, .5, 'buck', 'gold')
    subtract(screw, box('temporary screw slot', (tx, ty-3.55, rz+5.23), (2.5, .32, .3), 'buck', None, track=False))
    # D2PAK-style regulator package, metal tab and five bent leads.
    qx, qy = rx-5.2, ry-7.0
    box('Buck • regulator metal tab', (qx, qy, rz+.18), (8.1, 10, .36), 'buck', 'silver', .15)
    box('Buck • regulator IC body', (qx-.2, qy, rz+1.8), (7.5, 8.8, 3.2), 'buck', 'black', .15)
    text('Buck • regulator IC identifier', 'REGULATOR', (qx-.2, qy, rz+3.44), .9, 'buck', 'white', angle=math.pi/2)
    for i in range(5):
        yy = qy-3.3+i*1.65
        box('Buck • regulator lead', (rx+.5, yy, rz+.4), (4.4, .62, .65), 'buck', 'silver', .08)
    smd('Buck • rectifier diode', rx+8, ry-7.8, rz+.12, 2.1, 5.6, 1.65, 'buck')
    box('Buck • diode cathode band', (rx+8, ry-5.8, rz+1.82), (2.12, .35, .035), 'buck', 'silver')
    for x, y in [(-7.3, 11.9), (-6.5, -2.9), (6.2, -14.9), (-5.5, 15.4)]:
        smd('Buck • small passives', rx+x, ry+y, rz+.05, 2, 1, .55, 'buck')
    terminals['buck'] = t

    # S2 PCB with antenna-end corner radii and USB-end notch seen in official photo.
    e = P['s2']
    ex, ey = e['center_xy']
    ew, el, et, eb = e['width'], e['length'], e['pcb_thickness'], e['pcb_bottom']
    ez = eb+et
    pts = []
    for cx, cy, start, radius in [(ew/2-4, el/2-4, 0, 4), (-ew/2+4, el/2-4, 90, 4)]:
        for i in range(9):
            a = math.radians(start+i*90/8)
            pts.append((ex+cx+radius*math.cos(a), ey+cy+radius*math.sin(a)))
    pts += [(ex-ew/2, ey-el/2+7.5), (ex-ew/2+2, ey-el/2+6.5), (ex-ew/2+2, ey-el/2+1)]
    for cx, cy, start in [(-ew/2+3, -el/2+1, 180), (ew/2-1, -el/2+1, 270)]:
        for i in range(9):
            a = math.radians(start+i*90/8)
            pts.append((ex+cx+math.cos(a), ey+cy+math.sin(a)))
    pcb = polygon_plate('S2 • LOLIN V1.0.0 PCB outline', pts, eb, et, 's2', 'violet',
                        'Manufacturer outline34.3×25.4; corner/notch shape traced nominally; thickness1.6 assumed', WEMOS_DIM)
    pcb['pcb_thickness'] = et
    # Published transverse positions; longitudinal offset remains explicitly assumed.
    for side in (-1, 1):
        hx, hy = ex+side*10.2, ey+el/2-3.3
        bore(pcb, hx, hy, ez-.8, 1, 5, 's2')
        for z in (ez+.026, eb-.026):
            ring = cylinder('S2 • mounting-hole copper annulus', (hx, hy, z), 1.72, .05, 's2', 'gold')
            bore(ring, hx, hy, z, 1, .5, 's2')
            ring['dimension_status'] = 'HoleØ2 and transverse20.4 spacing published; Y offset3.3 and copper annulus assumed'
            ring['source'] = WEMOS_DIM
    left_outer = ['EN', '3', '5', '7', '9', '11', '12', '3V3']
    left_inner = ['1', '2', '4', '6', '8', '10', '13', '14']
    right_inner = ['40', '38', '36', '34', '21', '17', 'GND', '15']
    right_outer = ['39', '37', '35', '33', '18', '16', 'GND', 'VBUS']
    s2_t = {}
    for xx, names, outer in [(-11.43, left_outer, True), (-8.89, left_inner, False),
                              (8.89, right_inner, False), (11.43, right_outer, True)]:
        for i, name in enumerate(names):
            yy = ey+8.89-i*2.54
            point = pad('S2 • '+name+' through-pad', ex+xx, yy, ez, pcb, 's2', .8, .45)
            # Electrical names, not pin numbers or guessed underside coordinates.
            if name in ('VBUS', '16', '18', '3', '7') or (name == 'GND' and xx > 10):
                s2_t['GPIO'+name if name.isdigit() else name] = point
            if outer:
                label_x = ex+xx+(-1.1 if xx>0 else 1.1)
                text('S2 • '+name+' silk label', name, (label_x, yy, ez+.07), .58, 's2', angle=math.pi/2)
        pcb['header_geometry_source'] = KICAD
        pcb['header_geometry_status'] = '2.54 pitch; outer22.86 / inner17.78 span from KiCad nominal footprint; pad drill assumed'
    # ESP32-S2FN4R2, 7x7x0.85 package; precise board placement still photo-based.
    chip_x, chip_y = ex+1.6, ey-.7
    chip = box('S2 • ESP32-S2FN4R2 QFN56', (chip_x, chip_y, ez+.05+.85/2),
               (7, 7, .85), 's2', 'black', .05,
               'Espressif7×7×0.85 nominal package; solder standoff0.05 and XY placement assumed', ESP_PACKAGE)
    for side in (-1, 1):
        for i in range(14):
            offset = -2.6+i*.4
            box('S2 • QFN edge termination', (chip_x+side*3.51, chip_y+offset, ez+.07), (.12, .18, .12), 's2', 'silver')
            box('S2 • QFN edge termination', (chip_x+offset, chip_y+side*3.51, ez+.07), (.18, .12, .12), 's2', 'silver')
    cylinder('S2 • IC pin-one mark', (chip_x-2.8, chip_y+2.8, ez+.91), .18, .015, 's2', 'white')
    text('S2 • chip marking', 'ESP32-S2', (chip_x, chip_y+.9, ez+.913), .87, 's2', 'white')
    text('S2 • chip variant', 'FN4R2', (chip_x, chip_y-.7, ez+.913), .8, 's2', 'white')
    # Hollow USB-C shell; its insertion corridor points outward along -Y.
    ux, uy = ex, ey-el/2+2.35
    usb = box('S2 • USB-C metal shell', (ux, uy, ez+1.65), (8.8, 7.1, 3.2), 's2', 'silver', .55)
    inner = box('temporary USB hollow', (ux, uy-.18, ez+1.65), (7.65, 8.2, 2.1), 's2', None, .5, track=False)
    subtract(usb, inner)
    box('S2 • USB contact tongue', (ux, uy-.8, ez+1.65), (6.35, 4.6, .52), 's2', 'black', .12)
    for i in range(12):
        xx = ux-2.75+i*.5
        box('S2 • USB gold contact', (xx, uy-1.3, ez+1.93), (.19, 2.35, .045), 's2', 'gold')
    for side in (-1, 1):
        box('S2 • USB retaining lug', (ux+side*4.4, uy+1, ez+.18), (.8, 1.7, .36), 's2', 'silver', .1)
    s2_t['USB_C_front_center'] = [ux, uy-3.55, ez+1.65]
    # Small side-actuated buttons beside USB, in official top-photo positions.
    for side, name in [(-1, 'RST'), (1, '0')]:
        x = ex-ew/2+3.0 if side < 0 else ex+ew/2-1.05
        y = ey-el/2+3.2
        box('S2 • '+name+' switch body', (x, y, ez+.8), (2.1, 4, 1.6), 's2', 'white', .12)
        box('S2 • '+name+' side actuator', (x+side*1.45, y, ez+.9), (.8, 1.9, .9), 's2', 'black', .08)
        for yy in (-1.65, 1.65):
            box('S2 • switch solder lug', (x, y+yy, ez+.12), (2.7, .45, .24), 's2', 'silver')
        text('S2 • '+name+' button label', name, (x-side*2.25, y, ez+.04), .8, 's2', angle=math.pi/2)
    # Crystal, regulator and representative decoupling/passives match the photo.
    box('S2 • 40MHz crystal', (ex+3, ey+6.9, ez+.62), (3.2, 2.5, 1.15), 's2', 'silver', .2)
    text('S2 • crystal legend', '40.0', (ex+3, ey+6.9, ez+1.22), .58, 's2', 'black')
    smd('S2 • 3V3 regulator', ex-5.1, ey-6.7, ez+.05, 2.8, 2, 1.0, 's2')
    for x, y, direction in [(-6, 8, 0), (-3, 8, 0), (-4.7, 5, 0), (0, 9, 0),
                              (-6.3, .3, 1), (-6.3, -2.5, 1), (5, -6.3, 0),
                              (2.7, -6.3, 0), (.2, -6.3, 0), (-1.8, -8.1, 0)]:
        smd('S2 • ceramic decoupling', ex+x, ey+y, ez+.03,
            .9 if direction else 1.5, 1.5 if direction else .8, .65, 's2', 'ceramic')
    # A continuous visible meander; RF geometry here is appearance, not antenna artwork.
    ay = ey+el/2-1.4
    antenna_pts = [(ex-7.8, ey+8.8), (ex-7.8, ay), (ex-4.8, ay),
                   (ex-4.8, ay-2.8), (ex-1.5, ay-2.8), (ex-1.5, ay),
                   (ex+1.8, ay), (ex+1.8, ay-2.8), (ex+5.0, ay-2.8),
                   (ex+5.0, ay), (ex+7.4, ay)]
    for a, b in zip(antenna_pts, antenna_pts[1:]):
        x, y = (a[0]+b[0])/2, (a[1]+b[1])/2
        box('S2 • antenna trace beneath soldermask', (x, y, ez+.014),
            (max(.28, abs(a[0]-b[0])+.28), max(.28, abs(a[1]-b[1])+.28), .022), 's2', 'trace')
    text('S2 • board identity', 'S2 Mini', (ex+6.4, ey+1.2, ez+.05), 1.25, 's2', angle=math.pi/2)
    # Small actual through-vias improve underside appearance without inventing connectivity.
    for i in range(9):
        x, y = ex-5.8+i*1.35, ey+10.0
        bore(pcb, x, y, ez-.8, .13, 5, 's2')
    terminals['s2'] = s2_t
    bpy.context.view_layer.update()
    return {'groups': groups, 'terminals': terminals}
