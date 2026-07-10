import math
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import networkx as nx
import matplotlib.pyplot as plt

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
})

PERIOD_CMAP = plt.get_cmap("viridis")
MAX_PERIOD_SHOWN = 5  # color scale is fixed across figures so period colors are comparable
BASIN_PALETTE = ["#f78166", "#58a6ff", "#56d364", "#e3b341", "#bc8cff", "#39d353", "#ff7b72"]


def period_color(p):
    return PERIOD_CMAP(min(p, MAX_PERIOD_SHOWN) / MAX_PERIOD_SHOWN)


# ---------------------------------------------------------------------
# the Pea Pattern transformation
# ---------------------------------------------------------------------

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
    """One step: for each distinct digit present in n's base-k representation
    (largest to smallest), emit its count (in base k) followed by the digit."""
    ds = digits_base_k(n, k)
    counts = Counter(ds)
    out = []
    for digit in sorted(counts, reverse=True):
        c = counts[digit]
        out.extend(digits_base_k(c, k))
        out.append(digit)
    return value_of_digits(out, k)


# sanity checks against the paper
assert pea_step(123, 10) == 131211
assert pea_step(7, 2) == 7
assert pea_step(78, 2) == 78


def digit_str(n, k):
    return "".join(str(d) for d in digits_base_k(n, k))


# ---------------------------------------------------------------------
# full worked example (also printed to stdout, and reproduced in the README)
# ---------------------------------------------------------------------

def print_full_example(n, k):
    print(f"\nFull example, base {k}, starting from {n}:")
    cur = n
    while True:
        s = digit_str(cur, k)
        print(f"  {cur} = {s}")
        nxt = pea_step(cur, k)
        if nxt == cur:
            break
        cur = nxt
    print(f"  -> fixed point {cur} = {digit_str(cur, k)}")


print_full_example(19, 2)


# ---------------------------------------------------------------------
# build the functional graph reachable from 1..N, and detect its cycles
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


def find_cycle(node, parent):
    seen = {}
    path = []
    cur = node
    while cur not in seen:
        seen[cur] = len(path)
        path.append(cur)
        cur = parent[cur]
    start = seen[cur]
    cyc = path[start:]
    # canonicalize: rotate so the cycle always starts at its smallest member,
    # otherwise the same cycle reached from different nodes (different
    # rotations of the same tuple) would be treated as distinct cycles
    i = cyc.index(min(cyc))
    return tuple(cyc[i:] + cyc[:i])


def all_cycles(parent):
    cache = {}

    def cycle_of(node):
        if node in cache:
            return cache[node]
        cyc = find_cycle(node, parent)
        for c in cyc:
            cache[c] = cyc
        cache[node] = cyc  # cache the query node too, even if it's not itself a cycle member
        return cyc

    for node in parent:
        cycle_of(node)
    return cache  # node -> its cycle (tuple)


# ---------------------------------------------------------------------
# Figure: force-directed relation graph for a given base
# ---------------------------------------------------------------------

def plot_force_graph(k, n_max, out_name, seed=42, label_stars=True):
    parent = build_graph(k, n_max)
    node_cycle = all_cycles(parent)
    cycles = sorted(set(node_cycle.values()), key=lambda c: min(c))
    basin_color = {c: BASIN_PALETTE[i % len(BASIN_PALETTE)] for i, c in enumerate(cycles)}

    G = nx.DiGraph()
    G.add_nodes_from(parent.keys())
    for u, v in parent.items():
        if u != v:
            G.add_edge(u, v)
    for cyc in cycles:
        p = len(cyc)
        if p > 1:
            for i in range(p):
                G.add_edge(cyc[i], cyc[(i + 1) % p])

    components = sorted(nx.weakly_connected_components(G), key=len, reverse=True)

    pos = {}
    big = components[0]
    sub = G.subgraph(big)
    big_pos = nx.spring_layout(sub, k=1.6 / (len(sub) ** 0.5), iterations=150, seed=seed)
    pos.update(big_pos)

    xs = [p[0] for p in big_pos.values()]
    ys = [p[1] for p in big_pos.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    cx0, cy0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2

    rest = components[1:]
    for i, comp in enumerate(rest):
        sub = G.subgraph(comp)
        sub_pos = nx.spring_layout(sub, k=1.6 / (max(len(sub), 2) ** 0.5), iterations=150, seed=seed)
        angle = 2 * math.pi * i / max(len(rest), 1)
        r = span * 0.65
        cx, cy = cx0 + r * math.cos(angle), cy0 + r * math.sin(angle)
        for node, (x, y) in sub_pos.items():
            pos[node] = (x + cx, y + cy)

    fig, ax = plt.subplots(figsize=(14, 14))
    ax.set_facecolor("#0d1117")

    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        ax.plot([x0, x1], [y0, y1], color="#30363d", linewidth=0.3, alpha=0.6, zorder=1)

    for node in G.nodes():
        c = basin_color[node_cycle[node]]
        x, y = pos[node]
        ax.scatter([x], [y], s=5, color=c, zorder=2, linewidths=0)

    for cyc in cycles:
        c = period_color(len(cyc))
        for node in cyc:
            x, y = pos[node]
            ax.scatter([x], [y], s=240, color=c, marker="*", zorder=3,
                       edgecolors="#f0f6fc", linewidths=1.0)
        if label_stars:
            # label once, near the first node of the cycle
            x, y = pos[cyc[0]]
            label = " -> ".join(f"{v} ({digit_str(v, k)})" for v in cyc)
            if len(cyc) > 1:
                label += f"  (period {len(cyc)})"
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(0, 16),
                        ha="center", fontsize=9, color="#c9d1d9")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(FIGURES / out_name, dpi=200, facecolor="#0d1117")
    plt.close(fig)
    print(f"saved {out_name} (base {k}, {len(G)} nodes, {len(cycles)} basins)")
    return parent, node_cycle


parent2, node_cycle2 = plot_force_graph(2, 3000, "graph_base2.png")
plot_force_graph(3, 3000, "graph_base3.png")
plot_force_graph(10, 800, "graph_base10.png", label_stars=False)
plot_force_graph(15, 800, "graph_base15.png", label_stars=False)


# ---------------------------------------------------------------------
# Figure: return map (u_n, u_n+1) for base 2, stationary points
# colored by the period of the cycle they belong to
# ---------------------------------------------------------------------

xs = list(parent2.keys())

regular_x, regular_y = [], []
stat_x, stat_y, stat_c = [], [], []
for x in xs:
    cyc = node_cycle2[x]
    if x in cyc:
        stat_x.append(x)
        stat_y.append(parent2[x])
        stat_c.append(period_color(len(cyc)))
    else:
        regular_x.append(x)
        regular_y.append(parent2[x])

fig, ax = plt.subplots(figsize=(9, 9))
ax.scatter(regular_x, regular_y, s=4, color="#58a6ff", alpha=0.5, linewidths=0, label="u_n -> u_n+1")
ax.scatter(stat_x, stat_y, s=180, color=stat_c, marker="*", edgecolors="#f0f6fc",
           linewidths=1.0, zorder=3, label="stationary points")
for x in stat_x:
    ax.annotate(str(x), (x, parent2[x]), textcoords="offset points", xytext=(6, 6), fontsize=9)
ax.set_xlabel("u_n")
ax.set_ylabel("u_n+1")
plt.tight_layout()
plt.savefig(FIGURES / "return_map.png", dpi=200, facecolor="#0d1117")
plt.close(fig)
print("saved return_map.png")
