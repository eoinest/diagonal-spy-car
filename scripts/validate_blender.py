"""Run in Blender after opening the saved assembly; nominal solids only."""
import bpy, bmesh, json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
pr=list(bpy.data.collections['PRINTED • prototype'].objects)
hw=list(bpy.data.collections['HARDWARE • nominal reference'].objects)
def bounds(o):
    v=[o.matrix_world@Vector(p) for p in o.bound_box]
    return tuple(min(p[i] for p in v) for i in range(3)),tuple(max(p[i] for p in v) for i in range(3))
def overlaps(a,b):
    x,y=bounds(a);u,v=bounds(b)
    return all(min(y[i],v[i])-max(x[i],u[i])>0.02 for i in range(3))
def volume_intersection(a,b):
    c=a.copy();c.data=a.data.copy();bpy.context.scene.collection.objects.link(c)
    bpy.context.view_layer.objects.active=c
    m=c.modifiers.new('Nominal fit intersection','BOOLEAN');m.operation='INTERSECT';m.solver='EXACT';m.object=b
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm=bmesh.new();bm.from_mesh(c.data);vol=abs(bm.calc_volume(signed=True));bm.free()
    mesh=c.data;bpy.data.objects.remove(c,do_unlink=True);bpy.data.meshes.remove(mesh)
    return vol
pairs=[];tested=0
for i,a in enumerate(pr):
    if a.name=='08_fit_coupon':continue
    for b in hw+pr[i+1:]:
        if b.type!='MESH' or not overlaps(a,b):continue
        tested+=1;v=volume_intersection(a,b)
        if v>0.05:pairs.append({'a':a.name,'b':b.name,'intersection_mm3':round(v,4)})
result={'scope':'Printed parts versus nominal hardware envelopes and other printed parts; cosmetic details, wires, assembly tolerances, mechanical loading and purchased revision variation excluded.','positive_AABB_pairs_checked':tested,'intersections_over_0.05_mm3':pairs}
(R/'cad/clearance-report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
if pairs: raise RuntimeError('Resolve nominal solid intersections before publishing')
