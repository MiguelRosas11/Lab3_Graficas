"""Tras generar los fotogramas con --giro: python scripts/crear_gif.py.

Requiere Pillow: python -m pip install Pillow.
"""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
paths = sorted((root / "tmp/giro").glob("*.png"))
assert len(paths) == 24, "Generar primero con crear_nave.py -- --giro"
frames = []
for path in paths:
    with Image.open(path) as image:
        frames.append(image.convert("RGB").quantize(colors=128))
output = root / "capturas/nave_giro.gif"
frames[0].save(output, save_all=True, append_images=frames[1:], duration=100, loop=0, disposal=2)
with Image.open(output) as gif:
    assert gif.n_frames == 24
    assert gif.size == (720, 540)
    for index in range(gif.n_frames):
        gif.seek(index)
        gif.load()
print(f"GIF_OK: {output.name}, 24 fotogramas, 720x540, {output.stat().st_size} bytes")
