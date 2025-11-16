# Structured Reasoning Theory: LLM Reasoning Dynamics

## Core Concepts

### Prompt as Program in Token Space

A prompt \( P \) is a sequence of tokens that serves as an instruction or program for the Large Language Model (LLM). The prompt functions as a program written in the language of tokens that directs the LLM's behavior.

**Formalization:**
- Token generation: \( t_{k+1} \sim S(P(t_{k+1} | t_1, t_2, ..., t_k; W)) \)
- Sequence generation: \( O = \{t_{n+1}, t_{n+2}, ..., t_{n+m}\} \)

### Kolmogorov Complexity and Function Implementation

For a given function ideal \( F \), there may exist many implementations that satisfy its properties. The Kolmogorov complexity \( K(f) \) of the intended function must roughly match the complexity of the prompt description, lest the implementation is necessarily wrong.

**Key Inequality:**
\[
K(F) \leq K(P) + K_{\text{model}} + K_{\text{output}}
\]

When \( K(g) < K(f) \), the agent is being ambiguous. When \( K(g) > K(f) \), we've over-described, leading to misinterpretation.

### Stochastic Vector Field F

The LLM's generation process can be viewed as a stochastic vector field \( F \) in token/embedding space. Each prompt represents a point in this field, subject to dynamics until it outputs an end token.

**Dynamical System:**
- Successive generated output representations are induced for each sampled function output \( y \sim Y \)
- At auto-regressive step \( t \), we have points in sparse or dense space \( x_t \)
- Transitions occur according to sparse space log-prob token transitions in \( \mathcal{M} \)
- A stochastic vector field \( F \) in the token/embedding dual space is induced

### Dependency Gaps and Intermediate Reasoning

A **dependency gap** arises when a model needs to estimate a conditional relationship between variables that rarely co-occur directly in training data, but are conditionally dependent through intermediate variables.

**Mathematical Formulation:**
\[
P(C | A) = \sum_B P(C | B) P(B | A)
\]

Where \( B \) represents intermediate variables that bridge the gap between \( A \) and \( C \).

### d-Separation and Reasoning

In Bayesian networks, d-separation determines conditional independence. For reasoning:

- If \( A \) and \( C \) are d-separated by \( B \), then:
  \[
  P(A, C | B) = P(A | B) P(C | B)
  \]

- Scaffolded reasoning through \( B \) reduces bias:
  \[
  P(C | A) = \sum_B P(C | B) P(B | A)
  \]

## Structured Reasoning Schemas

### Schema as Probabilistic Scaffold

Structured schemas (e.g., JSON-based) act as probabilistic scaffolds that:
1. Reduce entropy by structuring context
2. Create feedback loops through nested objects
3. Guide token generation toward coherent outputs

**Schema Effectiveness:**
\[
P(C | A, \text{schema}) \ll P(C | A)
\]

Schemas partition output into fields with local constraints:
\[
P(t_1, t_2, ..., t_n | S, X) = \prod_{i=1}^{k} P(F_i | F_1, ..., F_{i-1}, S, X)
\]

### Mantras as Currents

Keys in JSON schemas function as "mantras" that:
- Anchor the model to specific reasoning paths
- Create attractors in the vector field \( F \)
- Reduce entropy by constraining token probabilities

**Formalization:**
A JSON schema \( G \) can be viewed as an imposed sub-field over \( F \):
\[
G: x_t \mapsto \mathbb{P}(x_{t+1} | x_t, \text{key})
\]

### Locality of Experience

Reasoning emerges from the locality of experience. When training data has local structure, intermediate reasoning steps allow models to connect variables indirectly, reducing bias by leveraging intermediate variables.

**Key Insight:** Chain-of-thought reasoning bridges gaps in sparse local training data by connecting variables through intermediate steps that align with training-local dependencies.

## Rule Modification and Fitness Landscapes

### Adaptive Evolution Analogy

The process of adaptive evolution through rule spaces parallels reasoning in LLMs:
- Rules determine transitions in configuration space
- Fitness corresponds to reasoning quality (coherence, alignment, utility)
- Dependency gaps correspond to fitness plateaus

### Fitness-Neutral Sets

Multiple rules may yield identical phenotypes, allowing exploration without immediate gains. JSON schemas define equivalence classes of reasoning paths, where intermediate outputs may vary syntactically but remain semantically aligned.

### Path Properties

For rules \( r_1, r_2 \in R \):
- **Admissible path**: Sequence \( \pi = (r_1, ..., r_n) \) where \( F(r_{i+1}) \geq F(r_i) \)
- **Path length**: \( |\pi| \)
- **Minimal path length**: \( d_\pi(r_1, r_2) = \min\{|\pi| : \pi \text{ is admissible}\} \)

## Computational Bounds

### Complexity Constraints

1. **Lower bound on rule complexity:**
   \[
   K(r) \geq \log_2(n) - O(1)
   \]

2. **Upper bound on achievable values:**
   \[
   \max_{r \in R} F(r) \leq 2^{k^n + O(1)}
   \]

3. **Space-time trade-off:**
   \[
   k^n \cdot T(v) \geq \Omega(v^2)
   \]

### Phase Transitions

Define order parameter:
\[
\phi(r) = \lim_{t \to \infty} \frac{1}{t} \sum_{s=1}^t w(\varepsilon_r^s(c_0))
\]

Critical phenomena:
- \( \phi(r) = 0 \) for \( F(r) < F_c \)
- \( \phi(r) \sim (F(r) - F_c)^\beta \) near \( F_c \)
- Power law correlations at \( F_c \)

## Practical Implications

### Schema Design Principles

1. **Explicit Intermediate Variables**: Schemas should encourage intermediate reasoning steps that align with d-separating variables
2. **Nested Structures for Marginalization**: Nested fields simulate marginalization over intermediate variables
3. **Feedback Loops for Refinement**: Iterative schemas mirror recursive marginalization

### Why Schemas Work

1. **Entropy Reduction**: Schemas reduce token entropy by conditioning reasoning on local structures
2. **Alignment with Locality**: Schemas guide models to generate intermediate variables consistent with local statistical structure
3. **Feedback Stabilization**: Nested schemas act as implicit marginalization, stabilizing reasoning paths

### Limitations

1. **Over-specification**: Too rigid schemas can constrain creativity
2. **Under-specification**: Vague fields may produce generic reasoning
3. **Imbalanced Complexity**: Excessive nesting can overwhelm model capacity

