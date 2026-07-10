# Epidemic Topology

> *Does the shape of a social network change how a disease moves through it — even when everyone has the same number of contacts?*

An SIS (susceptible → infected → susceptible) model run on two networks that are identical except for structure: both exactly 4-regular, both ~20,450 nodes. One is a **grid** wrapped into a torus; the other is a **clustered** network built by recursively replacing each node with a small clique.

$$P_{x,n+1} = P_{x,n}(1-I) + (1-P_{x,n})\left(1 - \prod_{k=1}^{V} (1 - R \, P_{k,n})\right)$$

$P_{x,n}$ is the probability node $x$ is infected at step $n$, $R$ the transmission probability, $I$ the recovery probability, $V$ the neighbors of $x$. This is a deterministic mean-field approximation — it propagates an infection *probability*, not real infected/susceptible individuals.

---

## The two networks

<p align="center"><img src="figures/topologies.png" width="800" /></p>

Both are 4-regular by construction. Starting from $K_5$ and recursively replacing each node with a small clique 6 times gives $5 \times 4^6 = 20{,}480$ nodes, close to the grid's $143^2 = 20{,}449$.

## Propagation dynamics

<p align="center"><img src="figures/propagation.png" width="800" /></p>

The grid's infection curve is a clean sigmoid. The clustered network is slower, and its rate of change is noisy and erratic where the grid's stays smooth.

Worth a quick check: the two networks have nearly identical average shortest path length (4.50 vs 4.82) — so "harder-to-reach sub-populations" isn't the real difference. What differs is the clustering coefficient (0.0 vs 0.5).

---

## Stochastic validation

The formula above assumes neighbors act independently — exactly what dense clustering violates. Re-running the same rule as a real stochastic process (genuine infected/susceptible states, coin-flip transmission and recovery, 40 runs per network) tests that assumption directly.

<p align="center"><img src="figures/stochastic_vs_meanfield.png" width="800" /></p>

On the grid, the stochastic mean tracks the deterministic curve closely. On the clustered network it doesn't: the deterministic model predicts ~90% infected by iteration 160, the stochastic mean only ~43%. The independence assumption lets it double-count transmissions inside cliques that, in reality, mostly land on already-correlated neighbors.

<p align="center"><img src="figures/variation_comparison.png" width="560" /></p>

Averaging the stochastic runs also smooths out nearly all the jagged variation — that noise was a synchronous-update artifact, not a real effect. The true picture: propagation is genuinely, smoothly slower on the clustered network, and the deterministic model got both the smoothness and the speed wrong.

(At $R=0.5$, $I=0.1$ the epidemic is comfortably supercritical — none of the 80 stochastic runs went extinct. A deterministic model could never show extinction at all, since it can only decay smoothly toward zero.)

---

## Code

```
code/generate_figures.py   — graph construction, deterministic + stochastic simulation, every figure above
```

```bash
python code/generate_figures.py
```

Requires `networkx`, `numpy`, `matplotlib`. Runs in under a minute.
