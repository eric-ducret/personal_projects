import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

SOURCES = Path(__file__).parent.parent.parent / "sources"
MEDIA = Path(__file__).parent.parent / "media"
MEDIA.mkdir(exist_ok=True)

MODULUS = 32
STATIC_MAX_SIDE = 900
GIF_MAX_SIDE = 500
N_FRAMES = 32


def load_gray(path, max_side):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = max_side / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)))
    X = np.array(img).astype(float)
    return np.dot(X[..., :3], [0.2989, 0.5870, 0.1140])


def to_gray_frame(band):
    # band is in [0, MODULUS); stretch to full 0-255 for display
    return (band * (255.0 / MODULUS)).astype(np.uint8)


def save_static(gray, name):
    frame = to_gray_frame(gray % MODULUS)
    Image.fromarray(frame, mode="L").save(MEDIA / f"{name}_stripes.png", optimize=True)
    print(f"saved {name}_stripes.png")


def save_gif(gray, name):
    frames = [Image.fromarray(to_gray_frame((gray + offset) % MODULUS), mode="L")
              for offset in range(N_FRAMES)]
    frames[0].save(
        MEDIA / f"{name}_stripes.gif",
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        optimize=True,
    )
    print(f"saved {name}_stripes.gif")


for name in ["eye", "flower"]:
    gray_static = load_gray(SOURCES / f"{name}.jpg", STATIC_MAX_SIDE)
    save_static(gray_static, name)
    gray_gif = load_gray(SOURCES / f"{name}.jpg", GIF_MAX_SIDE)
    save_gif(gray_gif, name)
