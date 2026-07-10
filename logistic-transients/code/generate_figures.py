import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

FIGURES = Path(__file__).parent.parent / "figures"
FIGURES.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#0d1117",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "text.color": "#c9d1d9",
    "grid.color": "#21262d",
})

# R's default categorical palette (R >= 4.0), reproduced here since the
# original script colors each point by `col=k`.
R4_PALETTE = ["#f0f6fc", "#DF536B", "#61D04F", "#2297E6",
              "#28E2E5", "#CD0BBC", "#F5C710", "#8b949e"]


def transient(r, x0=0.99999, n=40):
    """First n iterates of x_{k+1} = r*x_k*(1-x_k) from a fixed x0.
    This is what the R script actually plots (the pre-convergence transient),
    instead of the converged tail a bifurcation diagram normally shows."""
    xs = np.empty(n)
    x = x0
    for i in range(n):
        x = x * r * (1 - x)
        xs[i] = x
    return xs


def converged_tail(r, x0=0.5, warmup=500, keep=100):
    """Textbook bifurcation diagram: discard the transient, keep the attractor."""
    x = x0
    for _ in range(warmup):
        x = r * x * (1 - x)
    xs = np.empty(keep)
    for i in range(keep):
        x = r * x * (1 - x)
        xs[i] = x
    return xs


# Figure 1 — the transient (the "bug")
r_values = np.arange(1, 4.5, 0.005)
fig, ax = plt.subplots(figsize=(10, 8))
colors = [R4_PALETTE[k % 8] for k in range(40)]
with np.errstate(over="ignore", invalid="ignore"):
    for r in r_values:
        ys = transient(r)
        ax.scatter(np.full(40, r), ys, c=colors, s=1.0, marker='.', linewidths=0)
ax.set_xlim(0.7, 4)
ax.set_ylim(0, 1.05)
ax.set_xlabel("r")
ax.set_ylabel("x")
plt.tight_layout()
plt.savefig(FIGURES / "transient.png", dpi=200, facecolor="#0d1117")
plt.close(fig)
print("saved transient.png")

# Figure 2 — the converged tail, for comparison
r_values2 = np.arange(1, 4.5, 0.002)
fig, ax = plt.subplots(figsize=(10, 8))
with np.errstate(over="ignore", invalid="ignore"):
    for r in r_values2:
        ys = converged_tail(r)
        ax.scatter(np.full(len(ys), r), ys, c="#f0f6fc", s=0.3, marker='.', linewidths=0)
ax.set_xlim(0.7, 4)
ax.set_ylim(0, 1.05)
ax.set_xlabel("r")
ax.set_ylabel("x")
plt.tight_layout()
plt.savefig(FIGURES / "converged.png", dpi=200, facecolor="#0d1117")
plt.close(fig)
print("saved converged.png")
