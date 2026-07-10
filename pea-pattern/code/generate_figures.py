import math
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

FIGURES = Path(__file__).parent.parent / "figures"
FIGURES.mkdir(exist_ok=True)

K = 2       # base 2 -- the base with only two convergence values
N = 3000    # explore starting numbers 1..N

plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#0d1117",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "text.color": "#c9d1d9",
})


def digits_base_k(n, k):
    if n == 0:
        return [0]
    ds = []
    while n > 0:
        ds.append(n % k)
        n //= k
    return ds[::-1]


def value_of_digits(ds, k):
    v = 0
    for d in ds:
        v = v * k + d
    return v


def pea_step(n, k):
    """One step of the Pea Pattern transformation: for each distinct digit
    present in n's base-k representation (largest to smallest), emit its
    count (in base k) followed by the digit itself."""
    ds = digits_base_k(n, k)
    counts = Counter(ds)
    out = []
    for digit in sorted(counts, reverse=True):
        c = counts[digit]
        out.extend(digits_base_k(c, k))
        out.append(digit)
    return value_of_digits(out, k)


# sanity check against the paper's own worked example (base 10: 123 -> 131211)
assert pea_step(123, 10) == 131211
# and the two base-2 fixed points
assert pea_step(7, 2) == 7
assert pea_step(78, 2) == 78


# ---------------------------------------------------------------------
# Figure 1: relation graph -- every number's orbit under repeated pea_step,
# for starting values 1..N, laid out as a radial tree rooted at the fixed
# points it converges to.
# ---------------------------------------------------------------------

def build_graph(k, n_max):
    parent = {}
    explored = set()

    def expand(n):
        cur = n
        while cur not in explored:
            explored.add(cur)
            nxt = pea_step(cur, k)
            parent[cur] = nxt
            cur = nxt

    for start in range(1, n_max + 1):
        expand(start)
    return parent


def radial_layout(parent):
    children = defaultdict(list)
    for node, p in parent.items():
        if node != p:
            children[p].append(node)
    roots = sorted({v for v in parent.values() if parent[v] == v})

    leaf_cache = {}

    def count_leaves(node):
        if node in leaf_cache:
            return leaf_cache[node]
        kids = children.get(node, [])
        v = 1 if not kids else sum(count_leaves(c) for c in kids)
        leaf_cache[node] = v
        return v

    pos = {}

    def layout(node, depth, angle_lo, angle_hi):
        pos[node] = (depth, (angle_lo + angle_hi) / 2)
        kids = sorted(children.get(node, []))
        if not kids:
            return
        weights = [count_leaves(c) for c in kids]
        total = sum(weights)
        a = angle_lo
        for c, w in zip(kids, weights):
            span = (angle_hi - angle_lo) * w / total
            layout(c, depth + 1, a, a + span)
            a += span

    for i, r in enumerate(roots):
        layout(r, 0, i * 2 * math.pi / len(roots), (i + 1) * 2 * math.pi / len(roots))

    def radius_of(depth):
        return math.sqrt(depth + 0.3)

    xy = {node: (radius_of(d) * math.cos(a), radius_of(d) * math.sin(a))
          for node, (d, a) in pos.items()}
    return xy, roots


def basin_of(node, parent):
    cur = node
    seen = set()
    while parent[cur] != cur and cur not in seen:
        seen.add(cur)
        cur = parent[cur]
    return cur


parent = build_graph(K, N)
xy, roots = radial_layout(parent)
palette = ["#58a6ff", "#f78166"]
basin_color = {r: palette[i % len(palette)] for i, r in enumerate(roots)}

fig, ax = plt.subplots(figsize=(14, 14))
ax.set_facecolor("#0d1117")

for node in xy:
    p = parent[node]
    if p == node:
        continue
    x0, y0 = xy[node]
    x1, y1 = xy[p]
    ax.plot([x0, x1], [y0, y1], color="#30363d", linewidth=0.4, alpha=0.7, zorder=1)

for node, (x, y) in xy.items():
    ax.scatter([x], [y], s=3, color=basin_color[basin_of(node, parent)], zorder=2, linewidths=0)

for r in roots:
    x, y = xy[r]
    ax.scatter([x], [y], s=260, color="#f0f6fc", marker="*", zorder=3,
               edgecolors=basin_color[r], linewidths=1.5)
    label = f"{r} ({bin(r)[2:]})"
    label += "\nreached only from itself" if r == 7 else "\neverything else lands here"
    ax.annotate(label, (x, y), textcoords="offset points", xytext=(0, 22),
                ha="center", fontsize=11, color="#c9d1d9")

ax.set_aspect("equal")
ax.axis("off")
plt.tight_layout()
plt.savefig(FIGURES / "graph.png", dpi=200, facecolor="#0d1117")
plt.close(fig)
print(f"saved graph.png ({len(xy)} nodes, roots={roots})")


# ---------------------------------------------------------------------
# Figure 2: iterations to reach the fixed point, for n = 1..N2
# ---------------------------------------------------------------------

def steps_to_fixed_point(n, k, max_iter=200):
    cur = n
    for i in range(max_iter):
        nxt = pea_step(cur, k)
        if nxt == cur:
            return i, cur
        cur = nxt
    return None, cur


N2 = 5000
xs, ys, targets = [], [], []
for n in range(1, N2 + 1):
    steps, t = steps_to_fixed_point(n, K)
    xs.append(n)
    ys.append(steps)
    targets.append(t)

colors = ["#58a6ff" if t == 7 else "#f78166" for t in targets]

fig, ax = plt.subplots(figsize=(12, 6))
ax.scatter(xs, ys, c=colors, s=3, linewidths=0)
ax.set_xlabel("n")
ax.set_ylabel("iterations to fixed point")
plt.tight_layout()
plt.savefig(FIGURES / "iterations.png", dpi=200, facecolor="#0d1117")
plt.close(fig)
print("saved iterations.png")
