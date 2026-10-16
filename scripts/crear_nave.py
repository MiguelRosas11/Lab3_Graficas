"""Ejecutar con Blender 4.5: blender --background --python scripts/crear_nave.py.

La unica geometria inicial es un cubo. Cada detalle es una extrusion de una
cara existente; las extrusiones coplanares escaladas forman los insets.
Las camaras y luces se crean DESPUES de guardar y exportar el modelo.
"""
from pathlib import Path
import math
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "modelo"
PREVIEW = ROOT / "capturas"
MODEL.mkdir(exist_ok=True)
PREVIEW.mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

COLORS = [
    ("Casco_perla", (0.61, 0.70, 0.76, 1)),
    ("Alas_petroleo", (0.025, 0.25, 0.29, 1)),
    ("Cabina_azul", (0.025, 0.075, 0.14, 1)),
    ("Bordes_naranja", (0.95, 0.23, 0.045, 1)),
    ("Motor_grafito", (0.045, 0.055, 0.07, 1)),
    ("Interior_motor", (0.12, 0.62, 0.76, 1)),
]
mesh = bpy.data.meshes.new("Cubo_extruido")
ship = bpy.data.objects.new("Nave_Aster", mesh)
bpy.context.collection.objects.link(ship)
bpy.context.view_layer.objects.active = ship
ship.select_set(True)
for name, color in COLORS:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    # Sin nodos, texturas, metalicidad, transparencia ni emisiones.
    material.use_nodes = False
    mesh.materials.append(material)

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2)
for v in bm.verts:
    v.co.x *= 0.85
    v.co.y *= 1.2
    v.co.z *= 0.38
bm.normal_update()
front = next(f for f in bm.faces if f.normal.y < -0.9)
back = next(f for f in bm.faces if f.normal.y > 0.9)
top = next(f for f in bm.faces if f.normal.z > 0.9)
sides = [(s, next(f for f in bm.faces if f.normal.x * s > 0.9)) for s in (-1, 1)]


def extrude(face, move=(0, 0, 0), scale=(1, 1, 1), material=0):
    """Extrude Region, Scale y Move sobre la nueva cara, sin islas sueltas."""
    center = face.calc_center_median().copy()
    result = bmesh.ops.extrude_face_region(bm, geom=[face])
    verts = [g for g in result["geom"] if isinstance(g, bmesh.types.BMVert)]
    new_set = set(verts)
    cap = next(f for f in bm.faces if all(v in new_set for v in f.verts))
    for v in verts:
        delta = v.co - center
        v.co = center + Vector(tuple(delta[i] * scale[i] + move[i] for i in range(3)))
    for f in bm.faces:
        if any(v in new_set for v in f.verts):
            f.material_index = material
    bmesh.ops.delete(bm, geom=[face], context="FACES_ONLY")
    return cap


# Morro: tres extrusiones progresivas de la cara frontal.
cap = extrude(front, (0, -1.35, -0.035), (0.78, 1, 0.82))
cap = extrude(cap, (0, -1.15, -0.07), (0.28, 1, 0.52))
extrude(cap, (0, -0.28, 0), (0.50, 1, 0.58), material=3)

# Alas simetricas: inset en la raiz, extrusiones barridas y puntas elevadas.
for sign, face in sides:
    cap = extrude(face, scale=(1, 0.78, 0.40))
    cap = extrude(cap, (sign * 1.0, 0.40, 0.02), (1, 0.90, 0.80), material=1)
    cap = extrude(cap, (sign * 1.75, 0.90, 0.04), (1, 0.42, 0.65), material=1)
    cap = extrude(cap, (sign * 0.38, 0.22, 0.02), (1, 0.80, 0.90), material=3)
    extrude(cap, (sign * 0.12, 0.12, 0.52), (1, 0.72, 0.70), material=3)

# Cabina: inset y extrusion; el cristal es solo color base azul oscuro.
cap = extrude(top, scale=(0.64, 0.72, 1))
cap = extrude(cap, (0, -0.12, 0.12), (0.94, 0.96, 1), material=3)
cap = extrude(cap, (0, 0.14, 0.64), (0.68, 0.66, 1), material=2)
cap.material_index = 2

# Popa y tobera: marco e inset hacia dentro, cerrado y sin objetos extra.
cap = extrude(back, (0, 0.72, 0.03), (0.86, 1, 0.90))
cap = extrude(cap, (0, 0.20, 0), (0.92, 1, 0.92), material=4)
cap = extrude(cap, scale=(0.70, 1, 0.66), material=3)
cap = extrude(cap, (0, -0.22, 0), (0.86, 1, 0.84), material=4)
cap.material_index = 5

bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
assert all(e.is_manifold for e in bm.edges), "La nave debe ser una superficie cerrada"
bm.to_mesh(mesh)
bm.free()
mesh.update()
bevel = ship.modifiers.new("Bevel_suave", "BEVEL")
bevel.width = 0.035
bevel.segments = 1
bevel.affect = "EDGES"
triangles = ship.modifiers.new("Triangulado_exportacion", "TRIANGULATE")
triangles.quad_method = "BEAUTY"
ship["origen"] = "Un cubo; inset, extrude, scale, move y modificadores bevel/triangulate"
ship["frente"] = "-Y; arriba +Z"

# Encuadre comodo al abrir el archivo editable.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_distance = 13
            area.spaces.active.region_3d.view_rotation = Vector((9, -12, 10)).to_track_quat("Z", "Y")
            area.spaces.active.shading.color_type = "MATERIAL"

bpy.ops.wm.save_as_mainfile(filepath=str(MODEL / "nave_aster.blend"))
bpy.ops.wm.obj_export(
    filepath=str(MODEL / "nave_aster.obj"),
    export_selected_objects=True,
    apply_modifiers=True,
    export_triangulated_mesh=True,
    export_materials=True,
    export_normals=True,
    export_uv=False,
    forward_axis="NEGATIVE_Z",
    up_axis="Y",
)
print("MODELO_EXPORTADO", flush=True)

# Estudio temporal para la imagen: no forma parte del .blend ni del OBJ.
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1050
scene.render.resolution_percentage = 100
scene.world.color = (0.16, 0.16, 0.16)
scene.view_settings.view_transform = "AgX"
scene.render.image_settings.file_format = "PNG"


def aim(obj, point=(0, -0.3, 0)):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


for name, location, energy, size in [
    ("Luz_principal", (1, -5, 9), 1800, 7),
    ("Luz_relleno", (-7, -1, 4), 1100, 6),
    ("Luz_contorno", (3, 7, 6), 2200, 5),
]:
    light = bpy.data.lights.new(name, "AREA")
    light.energy = energy
    light.shape = "DISK"
    light.size = size
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj)
camera = bpy.data.cameras.new("Camara_temporal")
camera.type = "ORTHO"
camera.ortho_scale = 11.5
camera_obj = bpy.data.objects.new("Camara_temporal", camera)
scene.collection.objects.link(camera_obj)
scene.camera = camera_obj
scene.render.film_transparent = False
for name, location in [("nave_perspectiva", (9, -12, 10)), ("nave_posterior", (-9, 12, 8))]:
    camera_obj.location = location
    aim(camera_obj)
    scene.render.filepath = str(PREVIEW / (name + ".png"))
    bpy.ops.render.render(write_still=True)

if "--giro" in sys.argv:
    # Fotogramas para un GIF que muestra la nave completa desde todos los lados.
    frames = ROOT / "tmp/giro"
    frames.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    scene.cycles.samples = 16
    for frame in range(24):
        angle = 2 * math.pi * frame / 24 - math.pi / 2
        camera_obj.location = (14 * math.cos(angle), 14 * math.sin(angle), 10)
        aim(camera_obj)
        scene.render.filepath = str(frames / f"{frame:02}.png")
        bpy.ops.render.render(write_still=True)
