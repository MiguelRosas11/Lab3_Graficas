"""Verifica el entregable OBJ sin dependencias externas: python scripts/verificar_obj.py."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "modelo/nave_aster.obj"
vertices, faces, materials = [], [], set()
objects = []
mtllib = None
for line in path.read_text(encoding="utf-8").splitlines():
    parts = line.split()
    if not parts:
        continue
    if parts[0] == "v":
        vertices.append(tuple(map(float, parts[1:4])))
    elif parts[0] == "f":
        assert len(parts) == 4, "Se encontro una cara sin triangular"
        face = tuple(int(p.split("/")[0]) - 1 for p in parts[1:])
        assert len(set(face)) == 3, "Indices repetidos"
        faces.append(face)
    elif parts[0] == "usemtl":
        materials.add(parts[1])
    elif parts[0] == "mtllib":
        mtllib = parts[1]
    elif parts[0] == "o":
        objects.append(parts[1])

assert vertices and faces, "El archivo no contiene geometria"
assert len(objects) == 1, f"Se esperaba un solo objeto: {objects}"
assert all(math.isfinite(c) for v in vertices for c in v)
edges = Counter()
oriented = Counter()
adjacency = defaultdict(set)
volume = 0.0
for a, b, c in faces:
    assert all(0 <= i < len(vertices) for i in (a, b, c)), "Indice fuera de rango"
    p, q, r = (vertices[i] for i in (a, b, c))
    u = tuple(q[i] - p[i] for i in range(3))
    v = tuple(r[i] - p[i] for i in range(3))
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    assert sum(t*t for t in cross) > 1e-16, "Triangulo degenerado"
    volume += (p[0]*(q[1]*r[2]-q[2]*r[1]) + p[1]*(q[2]*r[0]-q[0]*r[2]) + p[2]*(q[0]*r[1]-q[1]*r[0])) / 6
    for i, j in ((a, b), (b, c), (c, a)):
        edges[tuple(sorted((i, j)))] += 1
        oriented[(i, j)] += 1
        adjacency[i].add(j)
        adjacency[j].add(i)
assert all(count == 2 for count in edges.values()), "Borde abierto o no manifold"
assert all(oriented[(a, b)] == oriented[(b, a)] == 1 for a, b in edges), "Normales inconsistentes"
visited, pending = set(), [0]
while pending:
    index = pending.pop()
    if index not in visited:
        visited.add(index)
        pending.extend(adjacency[index] - visited)
assert len(visited) == len(vertices), "Hay islas o vertices sueltos"
assert len(vertices) - len(edges) + len(faces) == 2, "Topologia inesperada"
assert volume > 0, "Volumen negativo o nulo"
assert mtllib and (path.parent / mtllib).is_file(), "Falta el MTL"
mtl = (path.parent / mtllib).read_text(encoding="utf-8")
assert "map_" not in mtl, "No se permiten texturas"
definitions = {line.split(maxsplit=1)[1] for line in mtl.splitlines() if line.startswith("newmtl ")}
assert materials <= definitions, "Material sin definir"
report = {
    "archivo": path.name,
    "objetos": len(objects),
    "vertices": len(vertices),
    "triangulos": len(faces),
    "materiales": sorted(materials),
    "componentes_conectados": 1,
    "superficie_cerrada_manifold": True,
    "normales_consistentes": True,
    "triangulos_degenerados": 0,
    "volumen": round(volume, 6),
    "texturas_externas": False,
    "resultado": "OK",
}
print(json.dumps(report, indent=2, ensure_ascii=False))
