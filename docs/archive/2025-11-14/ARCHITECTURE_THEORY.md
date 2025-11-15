# Theoretical Foundation: Context Injection Architectures

## Core Framework

### Information-Theoretic Perspective

**MCP (Model Context Protocol)** implements **lazy evaluation of conditional dependencies**. Rather than eagerly loading all potentially relevant context $C$ into prompt space, MCP allows the model to construct queries $Q(M_t)$ based on current model state $M_t$, receiving context $C_q = f(Q(M_t))$ on-demand. This preserves **d-separation structure** by avoiding collider bias introduced through unconditional injection.

**Forced context injection** implements hard conditioning $P(O|M, C_{\text{all}})$ where all potentially relevant context loads upfront. This:
- Creates high-dimensional state space requiring traversal
- Introduces collider bias through unconditional dependencies
- Saturates attention mechanisms causing dilution
- Fixes the attractor landscape before generation begins

### D-Separation and Causal Structure

**D-separation** defines conditional independence in directed acyclic graphs (DAGs): nodes $X$ and $Z$ are d-separated by $Y$ if all paths between them are blocked by conditioning on $Y$.

In context injection systems:
$$P(O|M, C) \neq P(O|M) \cdot P(O|C)$$

Forced injection creates hard conditioning that can introduce spurious dependencies through **collider effects**—when two independent causes share a common effect, conditioning on the effect induces correlation between causes.

**MCP lazy evaluation** implements soft conditioning $P(O|M, C_{Q(M)})$ where context loads conditionally based on model state. This:
- Maintains d-separation by avoiding spurious conditioning
- Enables dynamic attractor landscape modification during generation
- Preserves attention for relevant context
- Allows serial scaling through dependent query chains

### Clique Complexes and Topological Structure

**Context injection** = Clique complex construction in knowledge space
- Vertices represent knowledge elements (facts, concepts, procedures)
- Edges represent conditional dependencies or co-activation patterns
- Cliques represent mutually coherent context sets where all elements are pairwise compatible

**Forced context injection** creates large cliques by loading all related knowledge simultaneously. This is computationally expensive (checking coherence is clique-finding, which is NP-complete) and may form spurious cliques through collider effects.

**MCP lazy evaluation** builds cliques incrementally through queries, adding vertices only when edges to existing clique members are verified. This is equivalent to greedy clique construction.

### Attractor Basins as Maximal Cliques

**Attractor concretion** forms cliques in activation space:
- Co-activated neural patterns form edges
- Stable attractors correspond to maximal cliques (cannot add more patterns without breaking coherence)
- Basin boundaries are regions where cliques become disconnected

**K-clique percolation** identifies overlapping memory structures:
- Low $k$: Individual concepts (small cliques)
- Medium $k$: Composite representations (moderate cliques)
- High $k$: Complex multi-concept states requiring many elements to co-stabilize

### Information Geometry and Fisher Information

The **Fisher Information Matrix (FIM)** quantifies the curvature of the statistical manifold:

$$I_{kl} = -E\left[\frac{\partial^2}{\partial \theta_k \partial \theta_l} \log P(x|\theta)\right]$$

For attractor networks, the inverse FIM determinant bounds achievable precision via the Cramér-Rao inequality:

$$\det(\text{Cov}[\hat{\theta}]) \geq \frac{1}{\det(I)}$$

**Context injection modifies the FIM**, reshaping the manifold geometry and accessible basins. Higher Fisher Information = more structure = better compression possible.

### Serial Scaling Constraints

The **Serial Scaling Hypothesis** proves certain computations require depth—chains of dependent reasoning steps that cannot be parallelized. Context injection architectures face fundamental tradeoffs:

- **Upfront injection** pays serial cost during prompt construction but enables parallel generation
- **MCP lazy evaluation** distributes serial cost across generation through iterative queries

Neither escapes the underlying computational constraint that complex reasoning requires sequential dependent steps. The architectural choice determines **when** serial costs are paid, not whether they exist.

### Edge-of-Chaos Dynamics

**Class 4 cellular automata** exist at the phase transition between order (Classes I/II) and chaos (Class III). They exhibit "complex patterns of localized structures" with very long transients.

The **lambda parameter** $\lambda$ quantifies the probability of non-quiescent state transitions:
- $\lambda \approx 0$: Class I/II (fixed-point/periodic attractors)
- $\lambda \approx 0.5$: Class IV (edge-of-chaos, long transients)
- $\lambda \approx 1$: Class III (chaotic behavior)

**Optimal context injection** operates at the edge-of-chaos:
- Too much structure (forced injection): Rigid dogma, fails when conditions change
- Too much noise (random tool calls): Prevents stable knowledge accumulation
- Optimal balance: Localized wisdom structures that adapt without dissolving

### Wisdom as Dimensionality Reduction

**Wisdom-as-compression** formalizes intergenerational knowledge transmission as finding the minimal sufficient statistic. Given high-dimensional experience space $\mathcal{E} \in \mathbb{R}^n$, wisdom is a projection $\mathcal{W}: \mathcal{E} \to \mathbb{R}^m$ where $m \ll n$ that maximizes Fisher information preservation:

$$\mathcal{W}^* = \arg\max_{\mathcal{W}} \frac{I_F(\mathcal{W}(\mathcal{E}))}{\dim(\mathcal{W})}$$

The critical refinement: wisdom preserves **causal structure**, not raw information. The compressed representation must maintain the d-separation graph—which variables are conditionally independent given which observations.

## Implementation in BOP

Our `StructuredOrchestrator` implements these principles:

1. **Lazy Evaluation**: Tools called on-demand based on subproblem needs
2. **D-Separation Preservation**: Tracks conditioning sets to avoid collider bias
3. **Topological Analysis**: Uses clique complexes to analyze context coherence
4. **Attractor Basin Tracking**: Identifies maximal cliques as stable knowledge structures
5. **Fisher Information Estimation**: Measures structure for compression assessment
6. **Serial Scaling Awareness**: Respects dependent reasoning chains through schema decomposition

This provides a **rigorous mathematical foundation** for understanding context-agent architectures as dynamical systems operating on evolving topological structures.

