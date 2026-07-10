# Epidemic Topology

> *Does the shape of a social network change how a disease moves through it — even when everyone has the same number of contacts?*

A simple SIS (susceptible → infected → susceptible) model, run on two networks that are identical in every way except their large-scale structure: both are exactly 4-regular (every individual has 4 contacts) and have about the same number of nodes (~20,450). One is a **grid** wrapped into a torus; the other is a **clustered** network built by recursively replacing each node with a small clique. Everything else — transmission rate, recovery rate, iteration count, seed — is held fixed.

$$P_{x,n+1} = P_{x,n}(1-I) + (1-P_{x,n})\left(1 - \prod_{k=1}^{V} (1 - R \, P_{k,n})\right)$$

$P_{x,n}$ is the probability node $x$ is infected at step $n$; $R$ is the transmission probability per contact; $I$ is the recovery probability; $V$ is $x$'s set of neighbors. Every node updates in parallel: it either stays infected (probability $1-I$), or gets newly infected from at least one of its already-infected neighbors.

This isn't a stochastic simulation of individuals — it tracks an infection *probability* for every node deterministically, which is the standard mean-field approximation used to study epidemics on networks.

---

## The two networks

<p align="center"><img src="figures/topologies.png" width="800" /></p>

Both graphs are exactly 4-regular by construction — the grid because every cell connects to its 4 torus neighbors, the clustered graph because replacing a degree-$d$ node with $d$ new nodes (each wired to one old neighbor and to every other new node) preserves degree $d$ at every step. Starting from $K_5$ and repeating that replacement 6 times gives $5 \times 4^6 = 20{,}480$ nodes, close to the grid's $143^2 = 20{,}449$.

## Propagation dynamics

<p align="center"><img src="figures/propagation.png" width="800" /></p>

Starting from a single infected node, the grid's infection curve is a clean sigmoid. The clustered network is slower to take off, reaches full saturation later, and — more strikingly — its rate of change is **noisy and erratic** throughout, where the grid's stays smooth.

---

## Flagged: the "isolated sub-populations" explanation doesn't hold up

The original writeup's hypothesis was that clustering slows a disease down because it creates "isolated sub-groups" that are harder to reach — i.e., a **path-length** effect. Checking that directly on comparable preview-scale graphs (81 vs 80 nodes):

| | avg. clustering coefficient | avg. shortest path length |
|---|---|---|
| Grid | 0.000 | 4.50 |
| Clustered | 0.500 | 4.82 |

The average shortest path length is nearly identical between the two — so "distance between sub-populations" is not really what differs here. What *does* differ, by construction, is the **clustering coefficient**: the grid has none (no two neighbors of a node are ever neighbors of each other), while the clustered graph is built entirely out of small dense cliques (clustering = 0.5).

That distinction matters for a more subtle reason than reachability: this model updates **every node synchronously** at every step, and the update rule is a nonlinear feedback loop between a node and its neighbors. Inside a clique, every node's neighbors are also strongly coupled to *each other*, so a local group can jointly overshoot and correct in near-lockstep — exactly the kind of local resonance that produces the noisy, high-frequency variation seen in the clustered curve above. The grid has no such tightly-closed local loops (clustering = 0), so it has nothing to resonate with, and its variation curve stays smooth.

In short: the interesting result here is real, but the mechanism the original report proposed (harder-to-reach sub-populations) doesn't match the measured graph statistics. **Local clustering density interacting with synchronous updating** is a better-supported explanation than path length for both the slower propagation *and* the oscillatory noise — and that noise may partly be a synchronous-update artifact of the mean-field approximation itself rather than a real epidemiological effect. It's exactly the kind of thing an asynchronous or stochastic (Gillespie-style) simulation would help settle, and the original report's own suggested next step — adding a resistant state — wouldn't address this at all.

---

## Code

```
code/generate_figures.py   — graph construction, vectorized simulation, both figures above
```

```bash
python code/generate_figures.py
```

Requires `networkx`, `numpy`, `matplotlib`. The simulation loop is vectorized (fixed-degree neighbor lookup array), verified to match the original per-node update exactly, and runs the full ~20,450-node, 160-iteration simulation for both networks in a few seconds.
