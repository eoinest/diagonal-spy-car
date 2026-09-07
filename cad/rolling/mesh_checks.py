"""Strict binary-STL checks for printable, closed single-solid meshes.

Usage: python3 cad/rolling/mesh_checks.py [file.stl ...]
With no arguments, checks every .stl in this script's directory.

The pass/fail result uses the exact serialized float32 coordinates. A second
topology report rounds coordinates to five decimal places (0.00001 mm) for
diagnosis only: welding never turns an invalid export into a passing result.
This checks mesh structure, not assembly clearance, strength, or print settings.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path


_TRIANGLE = struct.Struct('<12fH')
_ZERO_Z_TOLERANCE_MM = 0.00001


def _topology(triangles, weld_digits=None):
    """Return topology/volume metrics; input coordinates must all be finite."""
    vertex_ids = {}
    vertices = []
    faces = []
    duplicate_keys = Counter()
    edges = {}
    zero_area = 0
    normals = []
    for tri in triangles:
        ids = []
        for point in tri:
            key = (tuple(round(value, weld_digits) for value in point)
                   if weld_digits is not None else point)
            if key not in vertex_ids:
                vertex_ids[key] = len(vertices)
                vertices.append(key)
            ids.append(vertex_ids[key])
        face_id = len(faces)
        faces.append(tuple(ids))
        duplicate_keys[tuple(sorted(ids))] += 1
        a, b, c = (vertices[i] for i in ids)
        u = tuple(b[k] - a[k] for k in range(3))
        v = tuple(c[k] - a[k] for k in range(3))
        cross = (u[1]*v[2] - u[2]*v[1],
                 u[2]*v[0] - u[0]*v[2],
                 u[0]*v[1] - u[1]*v[0])
        normals.append(cross)
        if cross == (0.0, 0.0, 0.0):
            zero_area += 1
        for i in range(3):
            start, end = ids[i], ids[(i+1) % 3]
            edge = (min(start, end), max(start, end))
            edges.setdefault(edge, []).append((face_id, start, end))

    # Connectivity is through shared edges, not merely a touching vertex.
    parent = list(range(len(faces)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(a, b):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    bad_winding = 0
    for incidents in edges.values():
        first = incidents[0][0]
        for incident in incidents[1:]:
            join(first, incident[0])
        if len(incidents) == 2:
            _, a, b = incidents[0]
            _, c, d = incidents[1]
            if a != d or b != c:
                bad_winding += 1

    bounds = ([[min(point[k] for point in vertices),
                max(point[k] for point in vertices)] for k in range(3)]
              if vertices else None)
    origin = vertices[0] if vertices else (0.0, 0.0, 0.0)
    # Translation and fsum reduce cancellation when a mesh is far from origin.
    volume_terms = []
    for face, normal in zip(faces, normals):
        a = vertices[face[0]]
        volume_terms.append(sum((a[k]-origin[k])*normal[k] for k in range(3))/6.0)
    volume = math.fsum(volume_terms)
    return {
        'vertices': len(vertices),
        'triangles': len(faces),
        'zero_area_triangles': zero_area,
        'duplicate_faces': sum(count-1 for count in duplicate_keys.values()),
        'non_manifold_edges': sum(len(incidents) != 2 for incidents in edges.values()),
        'inconsistent_edge_winding': bad_winding,
        'connected_components': len({find(i) for i in range(len(faces))}),
        'signed_volume_mm3': volume,
        'bounds_mm': bounds,
        'minimum_z_mm': bounds[2][0] if bounds else None,
    }


def validate_stl(path) -> dict:
    """Validate a binary STL; return a JSON-safe report without modifying it."""
    path = Path(path)
    report = {'file': str(path), 'valid': False, 'errors': []}
    try:
        raw = path.read_bytes()
    except OSError as error:
        report['errors'].append('Cannot read file: ' + str(error))
        return report
    report['file_bytes'] = len(raw)
    if len(raw) < 84:
        report['errors'].append('Binary STL is shorter than its 84-byte header.')
        return report
    count = struct.unpack_from('<I', raw, 80)[0]
    expected = 84 + count*_TRIANGLE.size
    report['declared_triangles'] = count
    report['expected_file_bytes'] = expected
    report['binary_length_valid'] = len(raw) == expected
    if len(raw) != expected:
        report['errors'].append('File length does not match the binary triangle count.')
        return report
    if count == 0:
        report['errors'].append('Mesh contains no triangles.')
        return report

    triangles = []
    nonfinite_coordinates = 0
    nonfinite_normals = 0
    for index in range(count):
        record = _TRIANGLE.unpack_from(raw, 84 + index*_TRIANGLE.size)
        nonfinite_normals += sum(not math.isfinite(value) for value in record[:3])
        nonfinite_coordinates += sum(not math.isfinite(value) for value in record[3:12])
        triangles.append(tuple(tuple(record[offset:offset+3]) for offset in (3, 6, 9)))
    report['nonfinite_coordinates'] = nonfinite_coordinates
    report['nonfinite_stored_normals'] = nonfinite_normals
    if nonfinite_coordinates or nonfinite_normals:
        report['errors'].append('Serialized coordinates or stored normals contain NaN/Infinity.')
        return report

    exact = _topology(triangles)
    report.update(exact)
    report['welded_round_5_diagnostics'] = _topology(triangles, weld_digits=5)
    for metric, message in (
        ('zero_area_triangles', 'Mesh contains zero-area triangles.'),
        ('duplicate_faces', 'Mesh contains coincident duplicate triangle faces.'),
        ('non_manifold_edges', 'Every edge must have exactly two incident triangles.'),
        ('inconsistent_edge_winding', 'Adjacent triangles have inconsistent winding.'),
    ):
        if exact[metric]:
            report['errors'].append(message)
    if exact['connected_components'] != 1:
        report['errors'].append('Mesh must contain one connected component through shared edges.')
    if not math.isfinite(exact['signed_volume_mm3']) or exact['signed_volume_mm3'] <= 0:
        report['errors'].append('Mesh must have finite positive signed volume.')
    if abs(exact['minimum_z_mm']) > _ZERO_Z_TOLERANCE_MM:
        report['errors'].append('Print orientation must place minimum Z at zero (within 0.00001 mm).')
    report['valid'] = not report['errors']
    return report


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    paths = ([Path(argument) for argument in argv] if argv
             else sorted(path for path in Path(__file__).resolve().parent.iterdir()
                         if path.is_file() and path.suffix.lower() == '.stl'))
    results = [validate_stl(path) for path in paths]
    passed = bool(results) and all(result['valid'] for result in results)
    summary = {'valid': passed, 'files_checked': len(results), 'results': results}
    if not paths:
        summary['errors'] = ['No STL files found.']
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
