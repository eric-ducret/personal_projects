# Epidemic Topology

> Does the *shape* of a social network change how a disease spreads through it?

Real populations don't mix randomly — people cluster into families, workplaces, friend groups. If that structure matters, two populations with the exact same number of contacts per person could still have very different epidemics, purely from how those contacts are arranged.

To test that, structure has to be isolated as the only variable: same transmission rule, same number of neighbors per node, same population size — only the network's shape changes.

## Two ways to arrange the same number of contacts

<p align="center"><img src="figures/topologies.png" width="800" /></p>

Both networks are exactly 4-regular (every node has 4 neighbors) and close in size (~20,450 nodes):

- **Grid** — a torus-wrapped lattice. No two neighbors of a node are ever neighbors of each other (clustering coefficient = 0).
- **Clustered** — built by recursively replacing every node with a small clique. Neighbors are tightly interconnected (clustering coefficient = 0.5).

Average shortest path length is nearly identical between them (4.50 vs 4.82) — so if propagation differs, it isn't because one network makes distant people harder to reach.

## The transmission rule

$$P_{x,n+1} = P_{x,n}(1-I) + (1-P_{x,n})\left(1 - \prod_{k=1}^{V} (1 - R \, P_{k,n})\right)$$

Each node's infection probability $P_{x,n}$ updates from its own state and its neighbors' ($R$ = transmission probability per contact, $I$ = recovery probability, $V$ = neighbors of $x$) — a standard deterministic mean-field approximation, not individuals.

## Propagation dynamics

<p align="center"><img src="figures/propagation.png" width="800" /></p>

Same model, same parameters, same seed — the grid infects in a clean sigmoid, the clustered network is slower and its rate of change stays noisy throughout.

---

## Stochastic validation

The mean-field formula assumes each neighbor's contribution is independent — exactly what dense clustering violates. Re-running the same rule as a real stochastic process (genuine infected/susceptible states, coin-flip transmission and recovery, 40 runs per network) tests that directly.

<p align="center"><img src="figures/stochastic_vs_meanfield.png" width="800" /></p>

On the grid, the stochastic mean tracks the deterministic curve closely. On the clustered network it doesn't: the deterministic model predicts ~90% infected by iteration 160, the stochastic mean only ~43%.

<p align="center"><img src="figures/variation_comparison.png" width="560" /></p>

Averaging the stochastic runs also smooths out nearly all the jagged variation seen in the deterministic clustered curve — that noise was a synchronous-update artifact, not a real effect. Propagation is genuinely, smoothly slower on the clustered network; the deterministic model got both the smoothness and the speed wrong.

(At $R=0.5$, $I=0.1$ the epidemic is comfortably supercritical — none of the 80 stochastic runs went extinct.)

---

## Code

```
code/generate_figures.py   — graph construction, deterministic + stochastic simulation, every figure above
```

```bash
python code/generate_figures.py
```

Requires `networkx`, `numpy`, `matplotlib`. Runs in under a minute.
