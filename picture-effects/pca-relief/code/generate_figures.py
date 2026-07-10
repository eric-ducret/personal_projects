import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from sklearn.decomposition import PCA
import pandas as pd
import plotly.graph_objects as go

SOURCES = Path(__file__).parent.parent.parent / "sources"
MEDIA = Path(__file__).parent.parent / "media"
MEDIA.mkdir(exist_ok=True)

SIDE = 220          # downscaled to a SIDE x SIDE grid of points
N_ROT_FRAMES = 72   # 5 degrees per frame


def load(path, side):
    img = Image.open(path).convert("RGB").resize((side, side))
    return np.array(img)


def pca_relief(name):
    X = load(SOURCES / f"{name}.jpg", SIDE)
    H, W, _ = X.shape
    pixels = X.reshape(-1, 3).astype(float) / 255.0

    pca = PCA(n_components=3)
    scores = pca.fit_transform(pixels)
    pc2 = scores[:, 1]

    ys, xs = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    xs = xs.ravel()
    ys = ys.ravel()

    # --- static hero PNG ---
    fig = plt.figure(figsize=(8, 8), facecolor="black")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("black")
    ax.scatter(xs, ys, pc2, c=pixels, s=2, linewidths=0)
    ax.set_axis_off()
    ax.view_init(elev=25, azim=-60)
    plt.tight_layout(pad=0)
    plt.savefig(MEDIA / f"{name}_relief.png", dpi=130, facecolor="black")
    plt.close(fig)
    print(f"saved {name}_relief.png")

    # --- rotating GIF ---
    fig = plt.figure(figsize=(6, 6), facecolor="black")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("black")
    ax.scatter(xs, ys, pc2, c=pixels, s=2, linewidths=0)
    ax.set_axis_off()
    ax.view_init(elev=25, azim=-60)
    plt.tight_layout(pad=0)

    frames = []
    for i in range(N_ROT_FRAMES):
        ax.view_init(elev=25, azim=-60 + i * 360 / N_ROT_FRAMES)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[..., :3]
        frames.append(Image.fromarray(buf))
    plt.close(fig)

    frames[0].save(
        MEDIA / f"{name}_relief.gif",
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        optimize=True,
    )
    print(f"saved {name}_relief.gif")

    # --- interactive Plotly HTML (self-contained) ---
    df = pd.DataFrame({
        "x": xs, "y": ys, "PC2": pc2,
        "color": [f"rgb({r},{g},{b})" for r, g, b in (pixels * 255).astype(int)],
    })
    fig3d = go.Figure(data=[go.Scatter3d(
        x=df["x"], y=df["y"], z=df["PC2"],
        mode="markers",
        marker=dict(size=1.5, color=df["color"], line=dict(width=0), opacity=1),
    )])
    fig3d.update_layout(
        scene=dict(
            bgcolor="black",
            xaxis=dict(visible=False), yaxis=dict(visible=False, autorange="reversed"),
            zaxis=dict(visible=False),
        ),
        paper_bgcolor="black",
        margin=dict(l=0, r=0, t=0, b=0),
        width=900, height=900,
    )
    fig3d.write_html(MEDIA / f"{name}_relief.html", include_plotlyjs="inline", full_html=True)
    print(f"saved {name}_relief.html")


for name in ["eye", "flower"]:
    pca_relief(name)
