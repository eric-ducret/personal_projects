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

Worth a quick check: the original hypothesis was that clustering slows spread by creating harder-to-reach sub-populations, but the two networks have nearly identical average shortest path length (4.50 vs 4.82 on comparable preview-scale graphs) — the real structural difference is the clustering coefficient (0.0 vs 0.5), not distance.

---

## Stochastic validation

The formula above is a *mean-field* approximation: it propagates an infection **probability** deterministically, assuming a node's neighbors act independently. That assumption is exactly what dense local clustering violates. To check what the model is actually getting wrong, the same rule was re-run as a real stochastic process on the same two graphs — every node is genuinely infected or not, transmission per edge is a coin flip with probability $R$, recovery is a coin flip with probability $I$ — for 40 independent runs per network.

<p align="center"><img src="figures/stochastic_vs_meanfield.png" width="800" /></p>

On the **grid**, the stochastic mean tracks the deterministic curve closely — the mean-field approximation is basically fine there, as expected with zero clustering.

On the **clustered** network, it isn't a minor discrepancy: by iteration 160 the deterministic model predicts ~90% of the population infected, while the actual stochastic mean over 40 runs is only ~43%. The mean-field model doesn't just get the *noise* wrong on this network, it gets the *speed* wrong — badly, and in one consistent direction (too fast). The independence assumption lets the model "double count" transmission opportunities inside a clique that, in reality, mostly land on individuals who are already infected or about to be through a correlated neighbor.

<p align="center"><img src="figures/variation_comparison.png" width="560" /></p>

Averaging 40 stochastic runs also smooths out almost all of the jagged variation the deterministic model showed for the clustered network — confirming that noise was mostly a synchronous-update artifact of the mean-field approximation, not a real epidemiological effect. The true picture is simpler than either version first suggested: propagation is genuinely, smoothly slower on the clustered network — the deterministic model invented the jaggedness and, at the same time, badly underestimated just how much slower it really is.

(With $R=0.5$, $I=0.1$ on 4-regular graphs of ~20,000 nodes, the epidemic is comfortably supercritical — none of the 80 stochastic runs died out. Extinction from a single seed would be a real possibility closer to the epidemic threshold, which the deterministic model, being unable to hit exactly zero, could never show at all.)

---

## Code

```
code/generate_figures.py   — graph construction, deterministic + stochastic simulation, every figure above
```

```bash
python code/generate_figures.py
```

Requires `networkx`, `numpy`, `matplotlib`. Both the deterministic and stochastic simulation loops are vectorized (fixed-degree neighbor lookup array); the deterministic one is verified to match the original per-node update exactly. The full ~20,450-node, 160-iteration run — deterministic plus 40 stochastic replicates per network — takes under a minute.
