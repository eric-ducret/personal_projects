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
# stochastic validation: an actual random contact process on the same
# graph, same R/I, same rule -- but nodes are really infected or not,
# not a propagated probability. Checks whether the mean-field curve
# (and its noisy variation on the clustered graph) reflects the real
# stochastic dynamics, or is an artifact of the deterministic,
# synchronous mean-field update.
# ---------------------------------------------------------------------

def stochastic_run(neighbor_idx, N, R, I, iterations, seed_node, rng):
    state = np.zeros(N, dtype=bool)
    state[seed_node] = True
    history = np.empty(iterations + 1)
    history[0] = state.mean()
    for t in range(1, iterations + 1):
        infected_neighbors = state[neighbor_idx]
        prob_infect = 1 - np.prod(np.where(infected_neighbors, 1 - R, 1.0), axis=1)
        newly_infected = (~state) & (rng.random(N) < prob_infect)
        stays_infected = state & (rng.random(N) >= I)
        state = newly_infected | stays_infected
        history[t] = state.mean()
    return history


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


# ---------------------------------------------------------------------
# Figure 3: stochastic replicates vs. the deterministic mean-field curve
# ---------------------------------------------------------------------

N_REPLICATES = 40
rng = np.random.default_rng(0)

print(f"--- running {N_REPLICATES} stochastic replicates per network ---")
grid_runs = np.array([stochastic_run(grid_idx, grid_N, R, I, ITERATIONS, 0, rng)
                       for _ in range(N_REPLICATES)])
clust_runs = np.array([stochastic_run(clust_idx, clust_N, R, I, ITERATIONS, 0, rng)
                        for _ in range(N_REPLICATES)])

grid_extinct = int((grid_runs[:, -1] == 0).sum())
clust_extinct = int((clust_runs[:, -1] == 0).sum())
print(f"Grid: {grid_extinct}/{N_REPLICATES} replicates went extinct")
print(f"Clustered: {clust_extinct}/{N_REPLICATES} replicates went extinct")

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, runs, det_hist, title, color in [
    (axes[0], grid_runs, grid_hist, "Grid", GRID_COLOR),
    (axes[1], clust_runs, clust_hist, "Clustered", CLUST_COLOR),
]:
    for run in runs:
        ax.plot(run, color=color, alpha=0.15, linewidth=0.8)
    ax.plot(runs.mean(axis=0), color=color, linewidth=2, label="stochastic mean")
    ax.plot(det_hist, color="#f0f6fc", linestyle="--", linewidth=1.5, label="deterministic mean-field")
    ax.set_title(f"{title}: {N_REPLICATES} stochastic runs vs. mean-field")
    ax.set_xlabel("Iterations")
    ax.set_ylabel("Proportion of infected individuals")
    ax.legend()
plt.tight_layout()
plt.savefig(FIGURES / "stochastic_vs_meanfield.png", dpi=150, facecolor="#0d1117")
plt.close(fig)
print("saved stochastic_vs_meanfield.png")

grid_stoch_var = np.diff(grid_runs.mean(axis=0))
clust_stoch_var = np.diff(clust_runs.mean(axis=0))

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(clust_var, color=CLUST_COLOR, alpha=0.4, linewidth=1, label="Clustered, deterministic")
ax.plot(clust_stoch_var, color=CLUST_COLOR, linewidth=2, label="Clustered, stochastic mean")
ax.plot(grid_var, color=GRID_COLOR, alpha=0.4, linewidth=1, label="Grid, deterministic")
ax.plot(grid_stoch_var, color=GRID_COLOR, linewidth=2, label="Grid, stochastic mean")
ax.set_title(f"Variation over iterations: deterministic vs. averaged stochastic ({N_REPLICATES} runs)")
ax.set_xlabel("Iterations")
ax.set_ylabel("Variation of infected proportion")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(FIGURES / "variation_comparison.png", dpi=150, facecolor="#0d1117")
plt.close(fig)
print("saved variation_comparison.png")
