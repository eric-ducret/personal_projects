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


def run_lookup(a, b, steps=300):
    u = [a, b]
    for _ in range(steps):
        u_n = u[-1]
        idx = u_n % len(u)
        u.append(u[idx] + 1)
    return u


def detect_loop(seq, min_reps=3):
    diffs = [seq[k + 1] - seq[k] for k in range(len(seq) - 1)]
    n = len(diffs)
    for p in range(1, n // min_reps):
        tail = diffs[n - min_reps * p :]
        chunk = tail[:p]
        if all(tail[i] == chunk[i % p] for i in range(len(tail))):
            onset = n - min_reps * p
            while onset > 0 and diffs[onset - 1] == diffs[onset - 1 + p]:
                onset -= 1
            return onset, p
    return None, None


seeds = [
    (-11, 0), (5, -3), (-5, -5),
    (-3, 8), (7, -11), (-7, 13),
    (-50, 50), (37, 11), (0, -17),
]

PALETTE = ["#58a6ff", "#f78166", "#56d364", "#e3b341", "#bc8cff", "#39d353",
           "#ff7b72", "#79c0ff", "#ffa657"]

# Figure 1 — raw sequences
fig, axes = plt.subplots(3, 3, figsize=(20, 16))
fig.patch.set_facecolor("#0d1117")
for k, (a, b) in enumerate(seeds):
    ax = axes[k // 3, k % 3]
    seq = run_lookup(a, b, 300)
    ax.plot(seq, linewidth=0.8, color=PALETTE[k])
    ax.set_title(f"u₀={a}, u₁={b}", fontsize=9, color="#8b949e")
    ax.set_facecolor("#0d1117")
    for spine in ax.spines.values():
        spine.set_edgecolor("#21262d")
plt.suptitle("uₙ₊₁ = u[uₙ mod (n+1)] + 1  —  raw sequences", fontsize=14,
             color="#c9d1d9", y=1.01)
plt.tight_layout()
plt.savefig(FIGURES / "sequences.png", dpi=150, bbox_inches="tight",
            facecolor="#0d1117")
plt.close()
print("saved sequences.png")

# Figure 2 — difference sequences
fig, axes = plt.subplots(3, 3, figsize=(20, 16))
fig.patch.set_facecolor("#0d1117")
for k, (a, b) in enumerate(seeds):
    ax = axes[k // 3, k % 3]
    seq = run_lookup(a, b, 300)
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    ax.plot(diffs, linewidth=0.8, color=PALETTE[k])
    ax.axhline(0, color="#30363d", linewidth=0.5)
    ax.set_title(f"u₀={a}, u₁={b}", fontsize=9, color="#8b949e")
    ax.set_facecolor("#0d1117")
    for spine in ax.spines.values():
        spine.set_edgecolor("#21262d")
plt.suptitle("Differences of uₙ₊₁ = u[uₙ mod (n+1)] + 1", fontsize=14,
             color="#c9d1d9", y=1.01)
plt.tight_layout()
plt.savefig(FIGURES / "differences.png", dpi=150, bbox_inches="tight",
            facecolor="#0d1117")
plt.close()
print("saved differences.png")

# Figure 3 — parameter space heatmaps over [-50, 50]²
print("computing parameter space [-50,50]² ...")
vals = list(range(-50, 51))
n = len(vals)
onset_map = np.full((n, n), np.nan)
period_map = np.full((n, n), np.nan)

for i, a in enumerate(vals):
    for j, b in enumerate(vals):
        if a == 0 and b == 0:
            continue
        seq = run_lookup(a, b, 2000)
        onset, period = detect_loop(seq)
        if onset is not None:
            onset_map[i, j] = onset
            period_map[i, j] = period

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
fig.patch.set_facecolor("#0d1117")
fig.suptitle(r"$u_{n+1} = u_{[u_n \,\mathrm{mod}\, (n+1)]} + 1$  —  parameter space $[-50,50]^2$",
             fontsize=18, color="#c9d1d9", y=1.02)

im0 = axes[0].imshow(np.log(onset_map), cmap="inferno", origin="lower")
axes[0].set_title("log onset  (steps until differences become periodic)",
                  color="#c9d1d9", fontsize=11)
plt.colorbar(im0, ax=axes[0])

im1 = axes[1].imshow(np.log1p(period_map + 1), cmap="inferno", origin="lower")
axes[1].set_title("log(1 + period)", color="#c9d1d9", fontsize=11)
plt.colorbar(im1, ax=axes[1])

tick_pos = range(0, n, 25)
for ax in axes:
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([vals[t] for t in tick_pos])
    ax.set_yticks(tick_pos)
    ax.set_yticklabels([vals[t] for t in tick_pos])
    ax.set_xlabel("b")
    ax.set_ylabel("a")
    ax.set_facecolor("#0d1117")

plt.tight_layout()
plt.savefig(FIGURES / "parameter_space.png", dpi=150, bbox_inches="tight",
            facecolor="#0d1117")
plt.close()
print("saved parameter_space.png")

# Figure 4 — zoomed positive quadrant [0, 200]²
print("computing zoomed positive quadrant [0,200]² ...")
vals2 = list(range(0, 200))
n2 = len(vals2)
onset_map2 = np.full((n2, n2), np.nan)

for i, a in enumerate(vals2):
    for j, b in enumerate(vals2):
        if a == 0 and b == 0:
            continue
        seq = run_lookup(a, b, 2000)
        onset, _ = detect_loop(seq)
        if onset is not None:
            onset_map2[i, j] = onset

plt.figure(figsize=(14, 14))
plt.gcf().patch.set_facecolor("#0d1117")
plt.gca().set_facecolor("#0d1117")
plt.title(
    r"Steps to periodicity for $u_{n+1} = 1 + u_{[u_n \,\mathrm{mod}\, (n+1)]}$"
    "\ninitial conditions $(a,b) \in [0, 200]^2$",
    fontsize=20, color="#c9d1d9", pad=16,
)
plt.imshow(5 ** np.log(onset_map2), cmap="inferno", origin="lower")
tick_pos2 = range(0, n2, 50)
plt.xticks(tick_pos2, [vals2[t] for t in tick_pos2], color="#8b949e")
plt.yticks(tick_pos2, [vals2[t] for t in tick_pos2], color="#8b949e")
plt.xlabel("b", color="#c9d1d9")
plt.ylabel("a", color="#c9d1d9")
cbar = plt.colorbar()
cbar.ax.yaxis.set_tick_params(color="#8b949e")
plt.tight_layout()
plt.savefig(FIGURES / "zoomed_quadrant.png", dpi=150, bbox_inches="tight",
            facecolor="#0d1117")
plt.close()
print("saved zoomed_quadrant.png")

print("all figures generated.")
