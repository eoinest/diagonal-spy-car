"""Audit the current assembly against a saved previous assembly.
Run Blender with --python verify_simplification.py -- --before /path/to/previous.blend.
The comparison preserves primary geometry; the deck intentionally changes.
"""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BEFORE=Path(sys.argv[sys.argv.index('--before')+1])
def inventory(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 sc=bpy.data.scenes['01 ASSEMBLED']
 res={}
 for o in sc.objects:
  if o.type=='MESH' and o.get('assembly_group') in ('base','battery','battery_band','buck','s2','drive_left','drive_right'):
   # Sorted world vertices allow unchanged geometry despite mesh-index ordering.
   verts=sorted(tuple(round(a,4) for a in o.matrix_world@v.co) for v in o.data.vertices)
   res[o.name]=hashlib.sha256(repr(verts).encode()).hexdigest()
 return res
before=inventory(BEFORE)
after=inventory(ROOT/'complete-spy-car.blend')
changed=[n for n in before if before[n]!=after.get(n)]
assert not changed,changed
forbidden=('perfboard','sense resistor','resistor lead','sense gpio','sense ground','sense fused','adc filter','bs250p','2n3904','adc carrier','adc spring','adc retaining','adc fixed')
leftovers=[o.name for o in bpy.data.objects if any(t in o.name.lower() for t in forbidden)]
assert not leftovers,leftovers
r={'revision':json.loads((ROOT/'parameters.json').read_text())['revision'],'previous_file_sha256':hashlib.sha256(BEFORE.read_bytes()).hexdigest(),'comparison':'Primary component world-space vertices rounded to 0.0001 mm vs supplied previous assembly', 'preserved_primary_meshes':len(before),'changed_primary_meshes':changed,'remaining_sensing_objects':leftovers,'deck':'Excluded from primary-part comparison; printed deck changes are validated in validation.json','physical_fit_verified':False}
(ROOT/'simplification-validation.json').write_text(json.dumps(r,indent=2)+'\n')
print('SIMPLIFICATION_AUDIT_OK',json.dumps(r))
