import networkx as nx
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
    "legend.facecolor": "#161b22",
    "legend.edgecolor": "#30363d",
})
GRID_COLOR = "#58a6ff"
CLUST_COLOR = "#f78166"


# ---------------------------------------------------------------------
# graph construction (same constructions as the original notebook)
# ---------------------------------------------------------------------

def grid_graph(n):
    """n x n grid, wrapped into a torus -> every node has exactly 4 neighbors."""
    G = nx.Graph()
    matrix = [[r * n + c for c in range(n)] for r in range(n)]
    for row in range(n):
        for col in range(n):
            G.add_edge(matrix[row][col], matrix[(row + 1) % n][col])
            G.add_edge(matrix[row][col], matrix[row][(col + 1) % n])
    return G


def replace(G):
    """Replace every node by a small complete graph, preserving each node's degree."""
    nodes = list(G.nodes())
    for node in nodes:
        neighbors = list(nx.neighbors(G, node))
        G.remove_node(node)
        new_nodes = [f"{node}.{i}" for i in range(len(neighbors))]
        G.add_nodes_from(new_nodes)
        for i in range(len(new_nodes)):
            G.add_edge(new_nodes[i], neighbors[i])
            for j in range(i + 1, len(new_nodes)):
                G.add_edge(new_nodes[i], new_nodes[j])
    return G


def clustered_graph(n_replace):
    G = nx.complete_graph(5)  # every node has degree 4
    for _ in range(n_replace):
        G = replace(G)
    return G


# ---------------------------------------------------------------------
# vectorized SIS mean-field simulation (equivalent to the notebook's
# per-node Transition() function, validated to match it exactly)
# ---------------------------------------------------------------------

def neighbor_array(G):
    G = nx.convert_node_labels_to_integers(G)
    N = G.number_of_nodes()
    degs = [d for _, d in G.degree()]
    d0 = degs[0]
    assert all(d == d0 for d in degs), "graph must be regular for this vectorized form"
    idx = np.zeros((N, d0), dtype=int)
    for node in G.nodes():
        idx[node] = list(G.neighbors(node))
    return idx, N


def simulate(neighbor_idx, N, R, I, iterations, seed_node=0):
    P = np.zeros(N)
    P[seed_node] = 1.0
    history = [P.mean()]
    for _ in range(iterations):
        neighbor_P = P[neighbor_idx]
        prod_term = np.prod(1 - R * neighbor_P, axis=1)
        P = P * (1 - I) + (1 - P) * (1 - prod_term)
        history.append(P.mean())
    return np.array(history)


# ---------------------------------------------------------------------
# Figure 1: topology preview
# ---------------------------------------------------------------------

grid_small = grid_graph(9)          # 81 nodes
clust_small = clustered_graph(2)    # 80 nodes

print("--- structural comparison (preview-scale graphs) ---")
for name, G in [("Grid", grid_small), ("Clustered", clust_small)]:
    c = nx.average_clustering(G)
    L = nx.average_shortest_path_length(G)
    print(f"{name}: n={G.number_of_nodes()}, avg clustering={c:.3f}, avg shortest path={L:.3f}")

fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
for ax, G, title, color in [
    (axes[0], grid_small, "Grid graph (81 nodes)", GRID_COLOR),
    (axes[1], clust_small, "Clustered graph (80 nodes)", CLUST_COLOR),
]:
    pos = nx.spring_layout(G, seed=0)
    nx.draw(G, pos, ax=ax, node_size=15, node_color=color, edge_color="#30363d", width=0.6)
    ax.set_title(title, color="#c9d1d9")
plt.tight_layout()
plt.savefig(FIGURES / "topologies.png", dpi=150, facecolor="#0d1117")
plt.close(fig)
print("saved topologies.png")


# ---------------------------------------------------------------------
# Figure 2: propagation dynamics at full scale
# ---------------------------------------------------------------------

R, I, ITERATIONS = 0.5, 0.1, 160

n = 143  # 143^2 = 20449 nodes
grid_big = grid_graph(n)
grid_idx, grid_N = neighbor_array(grid_big)
grid_hist = simulate(grid_idx, grid_N, R, I, ITERATIONS)

clust_big = clustered_graph(6)  # 5 * 4^6 = 20480 nodes
clust_idx, clust_N = neighbor_array(clust_big)
clust_hist = simulate(clust_idx, clust_N, R, I, ITERATIONS)

print(f"Grid: {grid_N} nodes, Clustered: {clust_N} nodes")

grid_var = np.diff(grid_hist)
clust_var = np.diff(clust_hist)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].plot(grid_hist, label="Grid", color=GRID_COLOR)
axes[0].plot(clust_hist, label="Clustered", color=CLUST_COLOR)
axes[0].set_title(f"Infection over iterations, R={R}, I={I}")
axes[0].set_xlabel("Iterations")
axes[0].set_ylabel("Proportion of infected individuals")
axes[0].legend()

axes[1].plot(grid_var, label="Grid", color=GRID_COLOR)
axes[1].plot(clust_var, label="Clustered", color=CLUST_COLOR)
axes[1].set_title(f"Infection variation over iterations, R={R}, I={I}")
axes[1].set_xlabel("Iterations")
axes[1].set_ylabel("Variation of infected proportion")
axes[1].legend()

plt.tight_layout()
plt.savefig(FIGURES / "propagation.png", dpi=150, facecolor="#0d1117")
plt.close(fig)
print("saved propagation.png")
