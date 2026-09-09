"""Remove the extra bulk capacitor from a saved assembly, preserving other parts.
Run before power_update.py. The base build.py already omits these parts.
"""
import bpy,bmesh,struct,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'rolling'))
from mesh_checks import validate_stl
MODEL=OUT/'complete-spy-car.blend'
source_hash=hashlib.sha256(MODEL.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene=bpy.data.scenes['01 ASSEMBLED'];bpy.context.window.scene=scene
deck=next(o for o in scene.objects if o.get('assembly_group')=='deck')
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith(('220uF 10V external bulk capacitor','Bulk capacitor metal lid','Bulk positive to distribution','Bulk negative to distribution')):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
# Only the under-deck region occupied by the former capacitor cradle and stops.
bpy.ops.mesh.primitive_cube_add(size=1,location=(15,0,21))
cut=bpy.context.object;cut.dimensions=(9,11,8)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
def subtract(tool):
 bpy.context.view_layer.objects.active=deck
 mod=deck.modifiers.new('Remove obsolete capacitor holder','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
subtract(cut)
# Preserve/reapply the already-approved fuse lead bores if a stale open Blender
# window was saved over the file before this update. No other deck region changes.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.75,depth=12,location=(-15,0,20.2),rotation=(1.5707963267948966,0,0))
subtract(bpy.context.object)
bm=bmesh.new();bm.from_mesh(deck.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(deck.data);bm.free()
for s in bpy.data.scenes:
 for o in s.objects:
  if o!=deck and o.get('assembly_group')=='deck':o.data=deck.data.copy()
# Export the edited deck, using the same rounding and topology check as build.py.
mesh=deck.data.copy();mesh.transform(deck.matrix_world)
verts=[v.co for v in mesh.vertices];lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
shift=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
for v in mesh.vertices:v.co=Vector(tuple(round(a,5) for a in v.co+shift))
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.calc_loop_triangles()
path=OUT/'electronics-deck.stl'
with path.open('wb') as f:
 f.write(b'Diagonal spy car v0.6.2 / mm / no external bulk'.ljust(80,b'\0'));f.write(struct.pack('<I',len(mesh.loop_triangles)))
 for t in mesh.loop_triangles:
  vs=[mesh.vertices[i].co for i in t.vertices];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]).normalized();f.write(struct.pack('<12fH',*n,*vs[0],*vs[1],*vs[2],0))
bpy.data.meshes.remove(mesh)
check=validate_stl(path);assert check['valid'],check
assert not [o.name for o in bpy.data.objects if o.name.startswith(('220uF','Bulk capacitor','Bulk positive','Bulk negative'))]
report={'revision':'0.6.2-no-external-bulk','source_sha256':source_hash,'removed_objects':removed,'deck_stl':check,'retained':'Converter onboard capacitors and 100 nF S2 bypass; existing fuse correction','scope':'Capacitor holder removed only below deck at X 10.5..19.5, Y -5.5..5.5, Z 17..25 mm. Fuse bores preserved/reapplied.','physical_fit_verified':False}
(OUT/'bulk-removal-validation.json').write_text(json.dumps(report,indent=2)+'\n')
# Keep the printable-deck report current; other original checks remain historical.
old=json.loads((OUT/'validation.json').read_text());old['revision']='0.6.2-no-external-bulk';check['file']='electronics-deck.stl';old['stl']=[check if x['file']=='electronics-deck.stl' else x for x in old['stl']];old['latest_edit']='bulk-removal-validation.json; earlier assembly collision and inventory values are from the full 0.6.1 build'
(OUT/'validation.json').write_text(json.dumps(old,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
print('BULK_REMOVAL_OK',json.dumps(report))
