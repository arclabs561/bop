"""Context topology analysis using clique complexes and information geometry."""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

# Import uncertainty functions (avoid circular import by importing here)
try:
    from .uncertainty import (
        compute_epistemic_uncertainty_jsd,
        compute_aleatoric_uncertainty_entropy,
        compute_total_uncertainty,
    )
    UNCERTAINTY_AVAILABLE = True
except ImportError:
    UNCERTAINTY_AVAILABLE = False


@dataclass
class ContextNode:
    """
    Represents a knowledge element in the context graph.

    Trust and uncertainty are integrated into the core node structure:
    - credibility: External source trustworthiness (0.0 to 1.0)
    - confidence: Internal structural support (0.0 to 1.0)
    - epistemic_uncertainty: Reducible uncertainty (what we don't know)
    - aleatoric_uncertainty: Irreducible randomness
    """

    id: str
    content: str
    source: str  # e.g., "perplexity", "firecrawl", "local"
    dependencies: Set[str] = None  # IDs of nodes this depends on
    # Trust and uncertainty (integrated)
    credibility: float = 0.5  # Source trustworthiness (external)
    confidence: float = 0.5  # Structural support (internal)
    epistemic_uncertainty: float = 0.5  # Reducible uncertainty
    aleatoric_uncertainty: float = 0.3  # Irreducible randomness
    verification_count: int = 0  # Independent verifications
    belief_alignment: float = 0.5  # How evidence aligns with priors

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        # Clamp values to valid ranges
        self.credibility = max(0.0, min(1.0, self.credibility))
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.epistemic_uncertainty = max(0.0, min(1.0, self.epistemic_uncertainty))
        self.aleatoric_uncertainty = max(0.0, min(1.0, self.aleatoric_uncertainty))
        self.belief_alignment = max(0.0, min(1.0, self.belief_alignment))


@dataclass
class CliqueStructure:
    """
    Represents a clique in the context graph.

    Trust-aware: tracks both coherence and trust metrics.
    """

    nodes: Set[str]  # Node IDs in the clique
    coherence_score: float  # How coherent this clique is
    dimension: int  # Size of clique (k-clique)
    # Trust metrics (integrated)
    avg_credibility: float = 0.5  # Average source credibility
    avg_confidence: float = 0.5  # Average structural confidence
    trust_score: float = 0.5  # Combined trust metric
    adversarial_risk: float = 0.0  # Risk of being disinformation cluster


class ContextTopology:
    """
    Analyzes context structure using clique complexes and information geometry.

    Integrated trust and uncertainty modeling:
    - Trust propagation through Bayesian networks
    - Epistemic/aleatoric uncertainty decomposition
    - Adversarial detection via structural/semantic analysis
    - Credibility vs confidence separation

    Based on the theoretical framework:
    - Context injection = Clique complex construction
    - MCP queries = Incremental clique discovery
    - Attractor basins = Maximal cliques (trust-aware)
    - D-separation = Topological structure (trust-weighted)
    """

    def __init__(self):
        """Initialize the topology analyzer."""
        self.nodes: Dict[str, ContextNode] = {}
        self.edges: Dict[Tuple[str, str], float] = {}  # Edge weights (coherence)
        self.edge_trust: Dict[Tuple[str, str], float] = {}  # Trust in edges
        self.cliques: List[CliqueStructure] = []
        self.betti_numbers: Dict[int, int] = {}  # Topological invariants
        self.source_trust: Dict[str, float] = {}  # Source-level credibility
        self.verification_graph: Dict[str, Set[str]] = {}  # Cross-verification
        # Calibration tracking (aligned with production patterns)
        self.confidence_predictions: List[Tuple[float, bool]] = []  # (predicted, actual)
        self.schema_violations: List[Dict[str, Any]] = []  # Track consistency issues

    def add_node(self, node: ContextNode) -> None:
        """Add a context node."""
        self.nodes[node.id] = node

    def add_edge(
        self,
        node1_id: str,
        node2_id: str,
        weight: float = 1.0,
        trust: Optional[float] = None,
    ) -> None:
        """
        Add an edge between nodes (represents coherence/dependency).

        Trust-aware: computes trust from node credibility if not provided.

        Args:
            node1_id: First node ID
            node2_id: Second node ID
            weight: Edge weight (coherence score)
            trust: Trust in this edge (defaults to geometric mean of node credibilities)

        Raises:
            ValueError: If either node doesn't exist
        """
        if node1_id not in self.nodes:
            raise ValueError(f"Node {node1_id} does not exist")
        if node2_id not in self.nodes:
            raise ValueError(f"Node {node2_id} does not exist")
        if node1_id == node2_id:
            raise ValueError("Cannot add self-loop edge")

        edge = tuple(sorted([node1_id, node2_id]))
        self.edges[edge] = weight

        # Compute trust if not provided (Bayesian: geometric mean of source credibilities)
        if trust is None:
            node1 = self.nodes[node1_id]
            node2 = self.nodes[node2_id]
            trust = (node1.credibility * node2.credibility) ** 0.5
        self.edge_trust[edge] = trust

    def compute_cliques(self, min_size: int = 2, max_size: Optional[int] = None) -> List[CliqueStructure]:
        """
        Compute cliques in the context graph.

        Uses greedy approach for tractability (exact clique-finding is NP-complete).

        Args:
            min_size: Minimum clique size (default: 2)
            max_size: Maximum clique size (default: number of nodes)

        Returns:
            List of maximal cliques
        """
        if not self.nodes:
            return []

        if min_size < 1:
            raise ValueError("min_size must be at least 1")
        if max_size is None:
            max_size = len(self.nodes)
        if max_size < min_size:
            # If max_size < min_size, no cliques can be found
            return []

        cliques = []
        node_ids = list(self.nodes.keys())

        # Greedy clique construction
        for i, node_id in enumerate(node_ids):
            # Start with single node
            current_clique = {node_id}
            candidates = set(node_ids[i + 1:])

            # Expand clique by adding compatible nodes
            while candidates:
                best_candidate = None
                best_score = 0.0

                for candidate in candidates:
                    # Check if candidate is connected to all clique members
                    if all(
                        tuple(sorted([candidate, member])) in self.edges
                        for member in current_clique
                    ):
                        # Compute coherence score
                        score = sum(
                            self.edges.get(tuple(sorted([candidate, member])), 0.0)
                            for member in current_clique
                        ) / len(current_clique)

                        if score > best_score:
                            best_score = score
                            best_candidate = candidate

                if best_candidate and len(current_clique) < max_size:
                    current_clique.add(best_candidate)
                    candidates.remove(best_candidate)
                else:
                    break

            if len(current_clique) >= min_size:
                coherence = self._compute_clique_coherence(current_clique)
                # Compute trust metrics for clique
                trust_metrics = self._compute_clique_trust(current_clique)
                cliques.append(CliqueStructure(
                    nodes=current_clique,
                    coherence_score=coherence,
                    dimension=len(current_clique) - 1,  # k-clique has dimension k-1
                    avg_credibility=trust_metrics["avg_credibility"],
                    avg_confidence=trust_metrics["avg_confidence"],
                    trust_score=trust_metrics["trust_score"],
                    adversarial_risk=trust_metrics["adversarial_risk"],
                ))

        # Remove subsumed cliques (keep only maximal)
        maximal_cliques = []
        for clique in sorted(cliques, key=lambda c: len(c.nodes), reverse=True):
            is_subsumed = any(
                clique.nodes.issubset(other.nodes) and clique.nodes != other.nodes
                for other in maximal_cliques
            )
            if not is_subsumed:
                maximal_cliques.append(clique)

        self.cliques = maximal_cliques
        return maximal_cliques

    def _compute_clique_coherence(self, nodes: Set[str]) -> float:
        """Compute coherence score for a clique."""
        if len(nodes) < 2:
            return 1.0

        edge_weights = [
            self.edges.get(tuple(sorted([n1, n2])), 0.0)
            for n1 in nodes
            for n2 in nodes
            if n1 < n2
        ]

        return np.mean(edge_weights) if edge_weights else 0.0

    def _compute_clique_trust(self, nodes: Set[str]) -> Dict[str, float]:
        """
        Compute trust metrics for a clique.

        Returns:
            Dictionary with avg_credibility, avg_confidence, trust_score, adversarial_risk
        """
        if not nodes:
            return {
                "avg_credibility": 0.5,
                "avg_confidence": 0.5,
                "trust_score": 0.5,
                "adversarial_risk": 0.0,
            }

        node_list = list(nodes)
        credibilities = [self.nodes[nid].credibility for nid in node_list]
        confidences = [self.nodes[nid].confidence for nid in node_list]

        avg_credibility = np.mean(credibilities) if credibilities else 0.5
        avg_confidence = np.mean(confidences) if confidences else 0.5

        # Trust score = weighted combination (credibility more important for source trust)
        trust_score = 0.6 * avg_credibility + 0.4 * avg_confidence

        # Adversarial risk: low trust + high coherence = suspicious cluster
        coherence = self._compute_clique_coherence(nodes)
        if trust_score < 0.3 and coherence > 0.7:
            adversarial_risk = 0.5  # Suspicious: coherent but untrusted
        elif trust_score < 0.2:
            adversarial_risk = 0.8  # High risk: very low trust
        else:
            adversarial_risk = 0.0

        return {
            "avg_credibility": float(avg_credibility),
            "avg_confidence": float(avg_confidence),
            "trust_score": float(trust_score),
            "adversarial_risk": float(adversarial_risk),
        }
    
    def compute_clique_uncertainty(self, nodes: Set[str]) -> Dict[str, float]:
        """
        Compute uncertainty metrics for a clique using JSD and entropy.
        
        Uses information-theoretic approach:
        - Epistemic uncertainty: JSD-based (measures disagreement)
        - Aleatoric uncertainty: Entropy-based (measures inherent randomness)
        - Total uncertainty: Weighted combination
        
        Args:
            nodes: Set of node IDs in the clique
        
        Returns:
            Dictionary with epistemic, aleatoric, and total uncertainty
        """
        if not nodes or not UNCERTAINTY_AVAILABLE:
            # Fallback to simple average if uncertainty module unavailable
            node_list = list(nodes) if nodes else []
            if node_list:
                epistemic_vals = [self.nodes[nid].epistemic_uncertainty for nid in node_list]
                aleatoric_vals = [self.nodes[nid].aleatoric_uncertainty for nid in node_list]
                return {
                    "epistemic": float(np.mean(epistemic_vals)) if epistemic_vals else 0.5,
                    "aleatoric": float(np.mean(aleatoric_vals)) if aleatoric_vals else 0.3,
                    "total": float(np.mean(epistemic_vals) + 0.5 * np.mean(aleatoric_vals)) if epistemic_vals and aleatoric_vals else 0.5,
                }
            return {
                "epistemic": 0.5,
                "aleatoric": 0.3,
                "total": 0.5,
            }
        
        # Extract predictions from nodes
        predictions = []
        for node_id in nodes:
            node = self.nodes[node_id]
            # Convert to probability distribution using confidence
            # [confidence, 1-confidence] for binary classification
            pred = np.array([
                1.0 - node.epistemic_uncertainty,  # Confidence (inverse of epistemic uncertainty)
                node.epistemic_uncertainty  # Epistemic uncertainty
            ])
            predictions.append(pred)
        
        # Compute uncertainties using JSD and entropy
        epistemic = compute_epistemic_uncertainty_jsd(predictions)
        aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
        total = compute_total_uncertainty(epistemic, aleatoric, beta=0.5)
        
        return {
            "epistemic": float(epistemic),
            "aleatoric": float(aleatoric),
            "total": float(total),
        }

    def compute_betti_numbers(self) -> Dict[int, int]:
        """
        Compute Betti numbers (topological invariants) of the clique complex.

        NOTE: This is a graph-level approximation, not true simplicial homology.
        For the clique complex, we approximate:
        - β₀: Connected components of the underlying graph
        - β₁: 1D cycles approximated via Euler's formula

        Why approximation:
        - True simplicial homology requires computing boundary operators ∂_k: C_k → C_{k-1}
        - Would need to construct chain complex: ... → C_2 → C_1 → C_0 → 0
        - Then compute H_k = ker(∂_k) / im(∂_{k+1}) via Smith normal form
        - This is computationally expensive (O(n³) for matrix operations)

        Our approximation:
        - Uses graph connectivity (faster, O(V+E))
        - Good enough for detecting disconnected knowledge domains (β₀)
        - Reasonable estimate of cycles/feedback loops (β₁)
        - Sufficient for information geometry heuristics

        For production use requiring exact topology:
        - Consider using libraries like GUDHI (simplicial complexes)
        - Or compute boundary matrices explicitly for small complexes
        """
        if not self.nodes:
            self.betti_numbers = {0: 0, 1: 0}
            return self.betti_numbers

        # β₀: Count connected components
        visited = set()
        components = 0

        for node_id in self.nodes:
            if node_id not in visited:
                components += 1
                self._dfs_component(node_id, visited)

        beta_0 = components

        # β₁: Approximate using Euler's formula for graphs
        # For a graph: χ = V - E = β₀ - β₁
        # So: β₁ = β₀ - (V - E) = β₀ - V + E
        # This is an approximation - true simplicial homology requires
        # computing homology groups of the clique complex
        num_edges = len(self.edges)
        num_nodes = len(self.nodes)
        beta_1 = max(0, beta_0 - num_nodes + num_edges)

        self.betti_numbers = {
            0: beta_0,
            1: beta_1,
        }

        return self.betti_numbers

    def _dfs_component(self, node_id: str, visited: Set[str]) -> None:
        """DFS to find connected component."""
        visited.add(node_id)
        for edge, _ in self.edges.items():
            if node_id in edge:
                neighbor = edge[0] if edge[1] == node_id else edge[1]
                if neighbor not in visited:
                    self._dfs_component(neighbor, visited)

    def compute_euler_characteristic(self) -> int:
        """
        Compute Euler characteristic of the clique complex.

        χ = Σ (-1)ⁿ |n-simplices|
        """
        # Count simplices by dimension
        simplices_by_dim = defaultdict(int)
        for clique in self.cliques:
            simplices_by_dim[clique.dimension] += 1

        # Euler characteristic
        chi = sum((-1) ** dim * count for dim, count in simplices_by_dim.items())
        return chi

    def analyze_d_separation(
        self,
        node_a: str,
        node_b: str,
        conditioning_set: Set[str],
        trust_threshold: float = 0.3,
    ) -> bool:
        """
        Check if nodes A and B are d-separated given conditioning set.

        Trust-aware: low-trust paths are considered blocked (unreliable connections).

        NOTE: This is a simplified implementation. Full d-separation requires:
        - Directed graph structure (we have undirected)
        - Collider detection (nodes with converging arrows)
        - Proper blocking rules for colliders vs non-colliders

        For undirected graphs, this reduces to: are all paths blocked?

        Args:
            node_a: First node
            node_b: Second node
            conditioning_set: Set of nodes to condition on
            trust_threshold: Minimum trust for path to be considered valid

        Returns:
            True if d-separated (conditionally independent), False otherwise
        """
        if node_a not in self.nodes or node_b not in self.nodes:
            return True  # Trivially independent if nodes don't exist

        if node_a == node_b:
            return False  # Node is always dependent on itself

        # Validate conditioning set
        invalid_conditioning = conditioning_set - set(self.nodes.keys())
        if invalid_conditioning:
            raise ValueError(f"Conditioning set contains invalid nodes: {invalid_conditioning}")

        # Find all paths between A and B
        paths = self._find_paths(node_a, node_b, max_length=10)

        if not paths:
            return True  # No paths = d-separated

        # Check if all paths are blocked (by conditioning OR low trust)
        for path in paths:
            # Check if path is blocked by conditioning
            if not self._is_path_blocked(path, conditioning_set):
                # Check if path has sufficient trust
                path_trust = self._compute_path_trust(path)
                if path_trust >= trust_threshold:
                    return False  # Found unblocked, trusted path

        return True  # All paths blocked = d-separated

    def _compute_path_trust(self, path: List[str]) -> float:
        """
        Compute trust for a path (geometric mean of edge trusts).

        Trust decays with path length (Bayesian propagation).
        """
        if len(path) < 2:
            return 1.0

        edge_trusts = []
        for i in range(len(path) - 1):
            edge = tuple(sorted([path[i], path[i + 1]]))
            trust = self.edge_trust.get(edge, 0.5)
            edge_trusts.append(trust)

        if not edge_trusts:
            return 0.5

        # Geometric mean with decay: trust decreases with path length
        geometric_mean = np.prod(edge_trusts) ** (1.0 / len(edge_trusts))
        decay_factor = 0.9 ** (len(path) - 1)  # Exponential decay
        return geometric_mean * decay_factor

    def _find_paths(self, start: str, end: str, max_length: int = 10) -> List[List[str]]:
        """
        Find all paths between two nodes.

        Args:
            start: Starting node ID
            end: Ending node ID
            max_length: Maximum path length to prevent infinite loops

        Returns:
            List of paths (each path is a list of node IDs)
        """
        if start not in self.nodes or end not in self.nodes:
            return []

        if start == end:
            return [[start]]  # Trivial path

        paths = []
        max_paths = 100  # Limit to prevent exponential explosion

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(paths) >= max_paths:
                return
            if len(path) > max_length:
                return
            if current == end:
                paths.append(path[:])
                return

            visited.add(current)
            for edge, _ in self.edges.items():
                if current in edge:
                    neighbor = edge[0] if edge[1] == current else edge[1]
                    if neighbor not in visited and neighbor in self.nodes:
                        dfs(neighbor, path + [neighbor], visited)
            visited.remove(current)

        dfs(start, [start], set())
        return paths

    def _is_path_blocked(self, path: List[str], conditioning: Set[str]) -> bool:
        """
        Check if a path is blocked by conditioning set.

        Simplified: path is blocked if any intermediate node is in conditioning set.
        """
        # Check intermediate nodes (not start/end)
        for node in path[1:-1]:
            if node in conditioning:
                return True  # Blocked by conditioning
        return False  # Path not blocked

    def get_attractor_basins(
        self,
        min_trust: float = 0.5,
        min_coherence: float = 0.5,
    ) -> List[Set[str]]:
        """
        Identify attractor basins as maximal cliques.

        Trust-aware: filters by both coherence and trust.

        Attractor basins = coherent, trusted context sets that stabilize together.

        Args:
            min_trust: Minimum trust score threshold
            min_coherence: Minimum coherence threshold

        Returns:
            List of trusted attractor basin node sets
        """
        if not self.cliques:
            # Auto-compute if not already done
            self.compute_cliques()

        return [
            clique.nodes
            for clique in self.cliques
            if clique.coherence_score >= min_coherence
            and clique.trust_score >= min_trust
            and clique.adversarial_risk < 0.5  # Exclude high-risk cliques
        ]

    def compute_fisher_information_estimate(self) -> float:
        """
        Estimate Fisher Information based on clique structure and trust.

        Trust-aware: high trust = more information = higher Fisher Information.

        NOTE: This is a heuristic estimate, not true Fisher Information Matrix.
        
        True Fisher Information requires:
        - Probability model P(x|θ) with parameters θ
        - Computing I_kl = -E[∂²/∂θ_k ∂θ_l log P(x|θ)]
        - Full statistical manifold with metric tensor

        Our heuristic approximation:
        - Clique coherence ≈ local curvature (high coherence = high information)
        - Betti numbers ≈ manifold complexity (low cycles = more structure)
        - Trust scores ≈ reliability of information (affects information quality)
        
        Rationale:
        - High coherence cliques indicate strong statistical dependencies
        - Low β₁ (few cycles) indicates tree-like structure = more compressible
        - Trust-weighted coherence reflects information quality
        
        This gives a 0-1 normalized estimate suitable for:
        - Comparing different context configurations
        - Guiding tool selection (prefer high-Fisher contexts)
        - Compression potential assessment

        For production use requiring exact Fisher Information:
        - Fit explicit probability model (e.g., Gaussian, exponential family)
        - Compute metric tensor on parameter space
        - Use information geometry libraries

        Returns:
            Heuristic Fisher Information estimate (0.0 to ~1.0)
        """
        if not self.cliques:
            return 0.0

        # Fisher Information relates to curvature of statistical manifold
        # Approximate using clique coherence, trust, and structure
        total_coherence = sum(c.coherence_score for c in self.cliques)
        total_trust = sum(c.trust_score for c in self.cliques)
        num_cliques = len(self.cliques)
        avg_coherence = total_coherence / num_cliques if num_cliques > 0 else 0.0
        avg_trust = total_trust / num_cliques if num_cliques > 0 else 0.5

        # Structure measure: how well-organized the cliques are
        # Lower cycles (β₁) = more tree-like = more structure
        # Avoid division by zero
        beta_1 = self.betti_numbers.get(1, 0)
        structure_measure = 1.0 / (1.0 + beta_1)

        # Trust-weighted: high trust = more reliable information = higher Fisher Info
        # Combine: coherence × trust × structure
        return min(1.0, avg_coherence * avg_trust * structure_measure)
    
    def compute_logical_depth_estimate(
        self,
        node_id: str,
        compression_ratio: float = 0.1,
    ) -> float:
        """
        Estimate Bennett's logical depth for a context node.
        
        ## Theoretical Foundation: Bennett's Logical Depth
        
        Charles Bennett's logical depth formalizes the concept of "valuable, hard-earned
        knowledge" - information that requires significant computational effort to produce
        from a compressed description. This contrasts with:
        - **Kolmogorov complexity**: Measures compressibility (short description = low complexity)
        - **Logical depth**: Measures computational effort (hard to produce = high depth)
        
        Example: A random string has high Kolmogorov complexity (hard to compress) but low
        logical depth (easy to produce). A proof of Fermat's Last Theorem has both high
        complexity and high depth (hard to compress AND hard to produce).
        
        ## Why This Matters for BOP
        
        BOP's knowledge structure research aims to understand the "shape of ideas" - which
        knowledge structures are valuable, deep, and meaningful. Logical depth provides a
        formal measure of knowledge value beyond just information content:
        - High depth = knowledge that required significant effort to develop
        - Low depth = easily produced or trivial knowledge
        
        This connects to the SSH document's discussion of "wisdom passed through ages" - deep
        knowledge that has been refined and validated over time.
        
        ## Implementation Approach
        
        We use a heuristic approximation based on:
        - **Trust**: High trust = valuable knowledge (validated, reliable)
        - **Coherence**: High coherence = structured knowledge (well-organized, meaningful)
        - **Verification**: More verification = more effort (multiple sources confirm)
        
        The compression ratio parameter reflects that more compressed descriptions require
        more computational effort to decompress (higher depth).
        
        Note: True logical depth requires computing the minimum time to produce a string from
        its shortest description using a universal Turing machine. Our heuristic captures
        the intuition: valuable, structured, verified knowledge has higher logical depth.
        
        Logical depth = computational effort to produce string from compressed description.
        
        Args:
            node_id: Node identifier
            compression_ratio: Assumed compression ratio for description (0-1)
        
        Returns:
            Estimated logical depth (0-1 normalized)
        """
        if node_id not in self.nodes:
            return 0.0
        
        node = self.nodes[node_id]
        
        # Logical depth correlates with:
        # 1. Trust (high trust = valuable knowledge)
        # 2. Coherence (high coherence = structured knowledge)
        # 3. Verification count (more verification = more effort)
        
        trust_component = node.trust_score
        coherence_component = getattr(node, 'coherence_score', 0.5)
        verification_component = min(1.0, node.verification_count / 5.0)  # Normalize
        
        # Weighted combination
        logical_depth = (
            0.4 * trust_component +
            0.3 * coherence_component +
            0.3 * verification_component
        )
        
        # Apply compression ratio (more compression = more depth required)
        logical_depth *= (1.0 + compression_ratio)
        
        return min(1.0, logical_depth)

    def analyze_context_injection_impact(
        self,
        new_nodes: List[ContextNode],
    ) -> Dict[str, Any]:
        """
        Analyze how adding new context nodes affects topology.

        NOTE: This modifies the topology permanently. For reversible analysis,
        consider using a copy of the topology.

        Returns analysis of:
        - New cliques formed
        - Betti number changes
        - D-separation structure changes
        - Fisher Information changes

        Args:
            new_nodes: List of new context nodes to add

        Returns:
            Dictionary with topology impact metrics
        """
        if not new_nodes:
            return {
                "new_cliques": 0,
                "betti_delta": {},
                "fisher_delta": 0.0,
                "topology_changed": False,
            }

        # Store original state
        original_betti = self.betti_numbers.copy()
        original_cliques = len(self.cliques)
        original_fisher = self.compute_fisher_information_estimate()

        # Add new nodes
        for node in new_nodes:
            # Skip if node already exists (idempotent)
            if node.id not in self.nodes:
                self.add_node(node)
                # Track source trust
                if node.source not in self.source_trust:
                    self.source_trust[node.source] = node.credibility
                else:
                    # Update source trust (Bayesian: weighted average)
                    old_trust = self.source_trust[node.source]
                    new_trust = node.credibility
                    # Simple moving average (could use proper Bayesian updating)
                    self.source_trust[node.source] = 0.7 * old_trust + 0.3 * new_trust

            # Add edges based on dependencies (trust-aware)
            for dep_id in node.dependencies:
                if dep_id in self.nodes and dep_id != node.id:
                    try:
                        # Edge trust = geometric mean of node credibilities
                        dep_node = self.nodes[dep_id]
                        edge_trust = (node.credibility * dep_node.credibility) ** 0.5
                        self.add_edge(node.id, dep_id, weight=0.8, trust=edge_trust)
                    except ValueError:
                        # Edge might already exist or invalid, skip
                        pass

        # Recompute topology
        self.compute_cliques()
        self.compute_betti_numbers()
        new_fisher = self.compute_fisher_information_estimate()

        # Compute deltas
        all_dims = set(list(self.betti_numbers.keys()) + list(original_betti.keys()))
        betti_delta = {
            dim: self.betti_numbers.get(dim, 0) - original_betti.get(dim, 0)
            for dim in all_dims
        }

        # Detect adversarial patterns
        adversarial_patterns = self._detect_adversarial_patterns()

        return {
            "new_cliques": len(self.cliques) - original_cliques,
            "betti_delta": betti_delta,
            "fisher_delta": new_fisher - original_fisher,
            "topology_changed": any(
                self.betti_numbers.get(dim, 0) != original_betti.get(dim, 0)
                for dim in all_dims
            ),
            "adversarial_patterns": len(adversarial_patterns),
            "trust_summary": self._get_trust_summary(),
        }

    def _detect_adversarial_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect potential adversarial/disinformation patterns.

        Indicators:
        - Low-trust cliques (coherent but untrusted)
        - Isolated high-trust nodes (verification targets)
        - High adversarial risk cliques
        """
        patterns = []

        # Check for low-trust cliques
        for clique in self.cliques:
            if clique.trust_score < 0.3 and clique.coherence_score > 0.6:
                patterns.append({
                    "type": "low_trust_clique",
                    "nodes": clique.nodes,
                    "trust_score": clique.trust_score,
                    "coherence": clique.coherence_score,
                    "risk": "Potential disinformation cluster",
                })

        # Check for isolated high-trust nodes
        for node_id, node in self.nodes.items():
            if node.credibility > 0.7:
                # Count high-trust neighbors
                high_trust_neighbors = 0
                for edge, trust in self.edge_trust.items():
                    if node_id in edge:
                        neighbor = edge[0] if edge[1] == node_id else edge[1]
                        neighbor_node = self.nodes.get(neighbor)
                        if neighbor_node and neighbor_node.credibility > 0.7 and trust > 0.7:
                            high_trust_neighbors += 1

                if high_trust_neighbors == 0:
                    patterns.append({
                        "type": "isolated_high_trust",
                        "node": node_id,
                        "credibility": node.credibility,
                        "risk": "Potential target for disinformation",
                    })

        return patterns

    def _get_trust_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about trust in the network.

        Aligned with production patterns: confidence scores, calibration, provenance.
        """
        if not self.edge_trust:
            return {
                "avg_trust": 0.5,
                "high_trust_edges": 0,
                "low_trust_edges": 0,
                "avg_credibility": 0.5,
                "avg_confidence": 0.5,
                "calibration_error": None,
                "schema_violations": len(self.schema_violations),
            }

        trusts = list(self.edge_trust.values())
        credibilities = [n.credibility for n in self.nodes.values()]
        confidences = [n.confidence for n in self.nodes.values()]

        # Compute calibration error if we have predictions
        calibration_error = None
        calibration_improvement = None
        if self.confidence_predictions:
            # Expected Calibration Error (ECE) - standard metric
            bins = 10
            bin_boundaries = np.linspace(0, 1, bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]

            ece = 0.0
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = [
                    (pred, actual)
                    for pred, actual in self.confidence_predictions
                    if bin_lower <= pred < bin_upper
                ]
                if in_bin:
                    accuracy_in_bin = np.mean([actual for _, actual in in_bin])
                    avg_confidence_in_bin = np.mean([pred for pred, _ in in_bin])
                    ece += len(in_bin) / len(self.confidence_predictions) * abs(
                        accuracy_in_bin - avg_confidence_in_bin
                    )
            calibration_error = float(ece)
            
            # Try to improve calibration using uncertainty metrics
            if UNCERTAINTY_AVAILABLE and len(self.nodes) > 1:
                try:
                    from .calibration_improvement import improve_calibration_with_uncertainty
                    
                    # Extract predictions and uncertainties from nodes
                    predictions = []
                    confidence_scores = []
                    for node in self.nodes.values():
                        # Create binary prediction from confidence
                        pred = np.array([node.confidence, 1.0 - node.confidence])
                        predictions.append(pred)
                        confidence_scores.append(node.confidence)
                    
                    # Get actual outcomes from confidence_predictions if available
                    actual_outcomes = [actual for _, actual in self.confidence_predictions]
                    
                    if len(actual_outcomes) == len(confidence_scores):
                        improvement_result = improve_calibration_with_uncertainty(
                            predictions,
                            confidence_scores,
                            actual_outcomes,
                            use_aleatoric_weighting=True,
                        )
                        calibration_improvement = improvement_result.get("calibration_improvement")
                except Exception:
                    # If calibration improvement fails, continue without it
                    pass

        result = {
            "avg_trust": float(np.mean(trusts)) if trusts else 0.5,
            "high_trust_edges": sum(1 for t in trusts if t > 0.7),
            "low_trust_edges": sum(1 for t in trusts if t < 0.3),
            "avg_credibility": float(np.mean(credibilities)) if credibilities else 0.5,
            "avg_confidence": float(np.mean(confidences)) if confidences else 0.5,
            "calibration_error": calibration_error,
            "schema_violations": len(self.schema_violations),
        }

    def check_schema_consistency(self, node: ContextNode) -> List[str]:
        """
        Check schema consistency (production pattern).

        Simple validation rules to prevent obvious errors.
        In production, would use domain-specific schemas.

        Returns:
            List of violation messages (empty if consistent)
        """
        violations = []

        # Example validations (would be domain-specific in practice)
        content_lower = node.content.lower()

        # Check for obvious contradictions (would be expanded)
        # This is a placeholder - real schemas would be more sophisticated

        if violations:
            self.schema_violations.append({
                "node_id": node.id,
                "violations": violations,
                "timestamp": "now",  # Would use actual timestamp
            })

        return violations

    def update_confidence_from_evidence(
        self,
        node_id: str,
        new_evidence: bool,
        evidence_quality: float = 0.5,
    ) -> None:
        """
        Update confidence based on new evidence (TRAIL pattern).

        Implements temporal confidence updates as evidence accumulates.

        Args:
            node_id: Node to update
            new_evidence: Whether evidence supports the claim
            evidence_quality: Quality of the evidence (0.0 to 1.0)
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Bayesian-style update: confidence increases with supporting evidence
        if new_evidence:
            # Increase confidence (weighted by evidence quality)
            node.confidence = min(1.0, node.confidence + 0.1 * evidence_quality)
            node.verification_count += 1
        else:
            # Decrease confidence if evidence contradicts
            node.confidence = max(0.0, node.confidence - 0.1 * evidence_quality)

        # Clamp to valid range
        node.confidence = max(0.0, min(1.0, node.confidence))

        # Track for calibration
        self.confidence_predictions.append((node.confidence, new_evidence))

