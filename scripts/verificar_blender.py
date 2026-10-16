"""Comprueba el editable y reimporta el OBJ con Blender 4.5."""
from pathlib import Path
import bpy
import bmesh

root = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root / "modelo/nave_aster.blend"))
objects = list(bpy.context.scene.objects)
assert len(objects) == 1 and objects[0].type == "MESH"
ship = objects[0]
assert [m.type for m in ship.modifiers] == ["BEVEL", "TRIANGULATE"]
assert len(ship.data.materials) == 6
assert all(not m.use_nodes for m in ship.data.materials)
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = ship.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
expected_vertices = len(mesh.vertices)
expected_faces = len(mesh.polygons)
assert all(len(p.vertices) == 3 for p in mesh.polygons)
evaluated.to_mesh_clear()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.obj_import(filepath=str(root / "modelo/nave_aster.obj"), forward_axis="NEGATIVE_Z", up_axis="Y")
objects = list(bpy.context.scene.objects)
assert len(objects) == 1 and objects[0].type == "MESH"
mesh = objects[0].data
assert len(mesh.vertices) == expected_vertices
assert len(mesh.polygons) == expected_faces
assert len(mesh.materials) == 6
assert all(len(p.vertices) == 3 for p in mesh.polygons)
bm = bmesh.new()
bm.from_mesh(mesh)
assert all(e.is_manifold for e in bm.edges)
assert bm.calc_volume(signed=True) > 0
bm.free()
print(f"REIMPORTACION_OK: {expected_vertices} vertices, {expected_faces} triangulos, 6 materiales; editable con un solo objeto")
