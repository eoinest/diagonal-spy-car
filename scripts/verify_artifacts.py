"""Validate exported STL bytes/topology, BOM shape and relative documentation links."""
from pathlib import Path
import csv,json,re,struct,collections,math
R=Path(__file__).resolve().parents[1]
report=[]
for f in sorted((R/'stl').glob('*.stl')):
    raw=f.read_bytes(); n=struct.unpack_from('<I',raw,80)[0]
    assert len(raw)==84+50*n,(f,'truncated STL')
    edges=collections.Counter();degenerate=0;vertices=[];adj=collections.defaultdict(set)
    for i in range(n):
        d=struct.unpack_from('<12fH',raw,84+i*50)
        v=[tuple(round(x,5) for x in d[j:j+3]) for j in [3,6,9]]
        assert all(math.isfinite(x) for p in v for x in p)
        if len(set(v))<3:degenerate+=1
        vertices+=v
        for a,b in [(v[0],v[1]),(v[1],v[2]),(v[2],v[0])]:
            edges[tuple(sorted((a,b)))]+=1;adj[a].add(b);adj[b].add(a)
    assert degenerate==0,(f,'degenerate faces',degenerate)
    bad=sum(count!=2 for count in edges.values())
    assert bad==0,(f,'non-two-manifold STL edge incidence',bad)
    unseen=set(adj);components=0
    while unseen:
        components+=1;stack=[unseen.pop()]
        while stack:
            for v in adj[stack.pop()]:
                if v in unseen:unseen.remove(v);stack.append(v)
    assert components==1,(f,'disconnected printable bodies',components)
    low=min(v[2] for v in vertices);assert abs(low)<.001,(f,'not on build plane',low)
    report.append({'file':f.name,'triangles':n,'closed_connected_shell':True,'min_z_mm':low})
assert len(report)==8
with (R/'BOM.csv').open() as f:
    rows=list(csv.DictReader(f));assert len(rows)==40
    assert len({r['ref'] for r in rows})==len(rows)
    assert all(None not in r and r['quantity'] for r in rows)
missing=[]
for f in R.rglob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',f.read_text()):
        if '://' in link or link.startswith('#') or link.startswith('mailto:'):continue
        path=link.split('#')[0]
        if path and not (f.parent/path).exists():missing.append((str(f.relative_to(R)),path))
assert not missing,missing
out={'stl_binary_audit':report,'bom_rows':len(rows),'relative_markdown_links':'pass'}
(R/'cad/artifact-report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
