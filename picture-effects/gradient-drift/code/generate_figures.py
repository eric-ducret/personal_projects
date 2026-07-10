import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from skimage.filters import sobel_v, sobel_h
from scipy.ndimage import gaussian_filter

SOURCES = Path(__file__).parent.parent.parent / "sources"
MEDIA = Path(__file__).parent.parent / "media"
MEDIA.mkdir(exist_ok=True)

MAX_SIDE = 700
GRID = 130          # dots per side
FACTOR = 0.6        # step size per frame
N_FRAMES = 90
STATIC_FRAME = 24   # peak flow-line density; later frames disperse into a sparse star field
BLUR_SIGMA = 4


def load_rgb(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = MAX_SIDE / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)))
    return np.array(img)


def run(name):
    img = gaussian_filter(load_rgb(SOURCES / f"{name}.jpg"), sigma=BLUR_SIGMA)
    H, W, _ = img.shape
    gray = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])
    direction = np.arctan2(sobel_v(gray), sobel_h(gray))

    xs, ys = np.meshgrid(np.linspace(0, H, GRID), np.linspace(0, W, GRID), indexing="ij")
    coords = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(float)

    fig, ax = plt.subplots(figsize=(7, 7 * H / W), facecolor="black")
    ax.set_facecolor("black")
    scat = ax.scatter(coords[:, 1], -coords[:, 0], s=1.5, color="white", alpha=0.6, linewidths=0)
    ax.set_xlim(0, W)
    ax.set_ylim(-H, 0)
    ax.axis("off")
    plt.tight_layout(pad=0)

    frames = []
    for f in range(N_FRAMES):
        xi = np.clip(coords[:, 0].round().astype(int), 0, H - 1)
        yi = np.clip(coords[:, 1].round().astype(int), 0, W - 1)
        in_bounds = (coords[:, 0] > 0) & (coords[:, 0] < H) & (coords[:, 1] > 0) & (coords[:, 1] < W)
        angle = direction[xi, yi]
        coords[in_bounds, 0] -= np.cos(angle)[in_bounds] * FACTOR
        coords[in_bounds, 1] -= np.sin(angle)[in_bounds] * FACTOR

        scat.set_offsets(np.stack([coords[:, 1], -coords[:, 0]], axis=1))
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[..., :3]
        frames.append(Image.fromarray(buf).convert("L"))

    plt.close(fig)

    frames[STATIC_FRAME].save(MEDIA / f"{name}_drift.png", optimize=True)
    print(f"saved {name}_drift.png")

    frames[0].save(
        MEDIA / f"{name}_drift.gif",
        save_all=True,
        append_images=frames[1:],
        duration=45,
        loop=0,
        optimize=True,
    )
    print(f"saved {name}_drift.gif")


for name in ["eye", "flower"]:
    run(name)
