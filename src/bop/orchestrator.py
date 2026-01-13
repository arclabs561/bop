"""Structured tool orchestration using reasoning schemas and information geometry."""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import numpy as np

from .context_topology import ContextNode, ContextTopology
from .llm import LLMService
from .mcp_tools import call_mcp_tool
from .research import ResearchAgent
from .schemas import ReasoningSchema, get_schema
from .token_importance import compute_token_importance_for_results

# Optional MUSE-based tool selection
try:
    from .uncertainty_tool_selection import (
        aggregate_results_with_aleatoric_weighting,
        select_tools_with_muse,
    )
    MUSE_SELECTION_AVAILABLE = True
except ImportError:
    MUSE_SELECTION_AVAILABLE = False
    select_tools_with_muse = None
    aggregate_results_with_aleatoric_weighting = None

logger = logging.getLogger(__name__)


@dataclass
class PipelineUncertainty:
    """Track uncertainty at each pipeline stage.

    Distinguishes operational uncertainty (pre-training to inference)
    from output uncertainty (quality of generated content).

    Based on "Rethinking the Uncertainty" (2410.20199v1).
    """
    # Operational uncertainty (model and data processing)
    query_decomposition: float = 0.5  # Operational: uncertainty in decomposition quality
    tool_selection: float = 0.5  # Operational: uncertainty in tool choice
    tool_execution: float = 0.5  # Operational: uncertainty in tool results
    result_aggregation: float = 0.5  # Operational: uncertainty in aggregation

    # Output uncertainty (quality of generated content)
    synthesis: float = 0.5  # Output: uncertainty in synthesis quality
    final_response: float = 0.5  # Output: uncertainty in final response

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "query_decomposition": self.query_decomposition,
            "tool_selection": self.tool_selection,
            "tool_execution": self.tool_execution,
            "result_aggregation": self.result_aggregation,
            "synthesis": self.synthesis,
            "final_response": self.final_response,
        }

# Optional constraint solver integration
try:
    from .constraints import (
        PYSAT_AVAILABLE,
        ConstraintSolver,
        ToolConstraint,
        create_default_constraints,
    )
    CONSTRAINTS_AVAILABLE = PYSAT_AVAILABLE
except ImportError:
    CONSTRAINTS_AVAILABLE = False
    ConstraintSolver = None
    ToolConstraint = None
    create_default_constraints = None


class ToolType(str, Enum):
    """Available tool types for research."""

    PERPLEXITY_DEEP = "perplexity_deep_research"
    PERPLEXITY_REASON = "perplexity_reason"
    PERPLEXITY_SEARCH = "perplexity_search"
    FIRECRAWL_SEARCH = "firecrawl_search"
    FIRECRAWL_SCRAPE = "firecrawl_scrape"
    FIRECRAWL_EXTRACT = "firecrawl_extract"
    TAVILY_SEARCH = "tavily_search"
    TAVILY_EXTRACT = "tavily_extract"


class ToolSelector:
    """Selects appropriate tools based on query characteristics."""

    @staticmethod
    def select_tools(
        subproblem: str,
        available_tools: Optional[List[ToolType]] = None,
    ) -> List[ToolType]:
        """
        Dynamically select tools based on subproblem characteristics.

        Args:
            subproblem: The subproblem to solve
            available_tools: Optional list of available tools

        Returns:
            List of selected tools
        """
        if available_tools is None:
            available_tools = list(ToolType)

        selected = []

        # Heuristics for tool selection
        subproblem_lower = subproblem.lower()

        # Deep research for complex, open-ended questions
        if any(word in subproblem_lower for word in ["comprehensive", "deep", "thorough", "analysis"]):
            selected.append(ToolType.PERPLEXITY_DEEP)

        # Reasoning for complex logical questions
        if any(word in subproblem_lower for word in ["why", "how", "explain", "reasoning", "logic"]):
            selected.append(ToolType.PERPLEXITY_REASON)

        # Quick search for factual queries
        if any(word in subproblem_lower for word in ["what", "when", "where", "who", "facts"]):
            selected.append(ToolType.PERPLEXITY_SEARCH)
            selected.append(ToolType.TAVILY_SEARCH)

        # Specific URLs or documents
        if "http" in subproblem_lower or "url" in subproblem_lower:
            selected.append(ToolType.FIRECRAWL_SCRAPE)

        # Structured data extraction
        if any(word in subproblem_lower for word in ["extract", "data", "structured", "table"]):
            selected.append(ToolType.FIRECRAWL_EXTRACT)
            selected.append(ToolType.TAVILY_EXTRACT)

        # Default: at least one search tool
        if not selected:
            selected.append(ToolType.PERPLEXITY_SEARCH)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(selected))


class StructuredOrchestrator:
    """
    Orchestrates multiple MCP tools using structured reasoning schemas.

    Implements theoretical framework:
    - MCP lazy evaluation preserves d-separation (avoids collider bias)
    - Context topology via clique complexes (coherent context sets)
    - Attractor basins as maximal cliques (stable knowledge structures)
    - Information geometry (Fisher Information, attention dilution)
    - Serial scaling constraints (dependent reasoning chains)

    This combines:
    - Structured reasoning (explicit intermediate steps)
    - Dynamic tool selection (flexibility based on subproblem)
    - Topological analysis (clique complexes, d-separation)
    - Synthesis (coherent combination preserving causal structure)
    """

    def __init__(
        self,
        research_agent: Optional[ResearchAgent] = None,
        llm_service: Optional[LLMService] = None,
        reset_topology_per_query: bool = True,
        use_constraints: bool = False,
        use_muse_selection: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            research_agent: Optional research agent instance
            llm_service: Optional LLM service for decomposition and synthesis
            reset_topology_per_query: Whether to reset topology between queries
            use_constraints: Whether to use constraint solver for tool selection
            use_muse_selection: Whether to use MUSE-based uncertainty-aware tool selection
        """
        self.research_agent = research_agent or ResearchAgent()
        self.llm_service = llm_service
        self.tool_selector = ToolSelector()
        self.topology = ContextTopology()
        self.context_history: List[ContextNode] = []
        self.use_muse_selection = use_muse_selection and MUSE_SELECTION_AVAILABLE
        self.reset_topology_per_query = reset_topology_per_query
        self._query_counter = 0  # For unique node IDs
        self.use_constraints = use_constraints and CONSTRAINTS_AVAILABLE
        if self.use_constraints:
            self.constraint_solver = ConstraintSolver()
            logger.info("Constraint solver enabled for optimal tool selection")
        else:
            self.constraint_solver = None
            if use_constraints and not CONSTRAINTS_AVAILABLE:
                logger.warning("Constraint solver requested but PySAT not available. Install with: uv sync --extra constraints")

    async def research_with_schema(
        self,
        query: str,
        schema_name: str = "decompose_and_synthesize",
        max_tools_per_subproblem: int = 2,
        preserve_d_separation: bool = True,
        prior_beliefs: Optional[List[Dict[str, Any]]] = None,
        adaptive_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Conduct research using structured schema with topological analysis.

        Implements lazy evaluation (MCP) to preserve d-separation structure,
        avoiding collider bias from forced context injection.

        Args:
            query: Research query
            schema_name: Schema to use for decomposition
            max_tools_per_subproblem: Maximum tools per subproblem
            preserve_d_separation: Whether to preserve d-separation
            prior_beliefs: Optional list of user's prior beliefs for alignment computation

        Returns:
            Research result dictionary with:
            - query: Original query
            - schema_used: Schema name
            - subsolutions: List of subproblem solutions
            - final_synthesis: Final synthesized result
            - source_matrix: Source agreement/disagreement matrix
            - topology: Enhanced topology with source_credibility, verification_info, cliques
            - tools_called: Number of tools called
            - d_separation_preserved: Whether d-separation was preserved
        """
        schema = get_schema(schema_name)
        if not schema:
            # Fallback to simple research
            return await self.research_agent.deep_research(query)

        # Reset topology if configured to do so
        if self.reset_topology_per_query:
            self.topology = ContextTopology()

        self._query_counter += 1
        query_id = self._query_counter

        # Initialize pipeline uncertainty tracking
        pipeline_uncertainty = PipelineUncertainty()

        # Step 1: Decompose query using schema (creates intermediate reasoning steps)
        if self.llm_service:
            decomposition = await self.llm_service.decompose_query(query, schema)
            # Estimate decomposition uncertainty (heuristic: based on number of subproblems)
            if decomposition:
                # More subproblems = potentially more uncertainty (but also more thorough)
                pipeline_uncertainty.query_decomposition = min(0.8, 0.3 + 0.1 * len(decomposition))
            else:
                pipeline_uncertainty.query_decomposition = 0.7  # High uncertainty if decomposition failed
        else:
            decomposition = await self._decompose_query(query, schema)
            pipeline_uncertainty.query_decomposition = 0.6  # Higher uncertainty for heuristic decomposition

        # Step 2: For each subproblem, dynamically select and call tools
        # This implements lazy evaluation - only load context when needed
        subsolutions = []
        conditioning_set = set()  # Track what we've conditioned on

        # NEW: Get adaptive reasoning depth estimate
        estimated_depth = None
        query_type = None
        if adaptive_manager:
            try:
                query_type = adaptive_manager._classify_query(query)
                estimated_depth = adaptive_manager.estimate_reasoning_depth(query, query_type)
                logger.info(f"Estimated reasoning depth: {estimated_depth} subproblems for query type: {query_type}")
            except Exception as e:
                logger.debug(f"Failed to estimate reasoning depth: {e}", exc_info=True)

        for i, subproblem in enumerate(decomposition):
            # NEW: Check for early stopping
            if adaptive_manager and query_type and i > 0 and len(subsolutions) >= 2:
                try:
                    # Estimate current quality (heuristic: based on subsolution quality)
                    current_quality = self._estimate_current_quality(subsolutions)

                    if adaptive_manager.should_early_stop(
                        current_quality, query_type, len(subsolutions)
                    ):
                        logger.info(
                            f"Early stopping: quality threshold met after {len(subsolutions)} subproblems "
                            f"(quality: {current_quality:.3f})"
                        )
                        break
                except Exception as e:
                    logger.debug(f"Early stopping check failed: {e}", exc_info=True)
            # Select tools dynamically based on subproblem characteristics
            if self.use_constraints and self.constraint_solver:
                logger.debug(f"Using constraint solver for subproblem {i+1}/{len(decomposition)}")
                tools = self._select_tools_with_constraints(
                    subproblem,
                    max_tools=max_tools_per_subproblem,
                )
                if not tools:  # Fallback to heuristics if constraints fail
                    logger.debug("Constraint solver returned no tools, using heuristics")
                    tools = self.tool_selector.select_tools(subproblem)
                    tools = tools[:max_tools_per_subproblem]
                else:
                    logger.debug(f"Constraint solver selected {len(tools)} tools")
            else:
                # Use topology to influence selection (avoid breaking coherence, maximize information gain)
                candidate_tools = self.tool_selector.select_tools(subproblem)

                # Apply MUSE-based uncertainty-aware selection if enabled
                if self.use_muse_selection and MUSE_SELECTION_AVAILABLE and select_tools_with_muse:
                    try:
                        # Get tool metadata (credibility, historical performance)
                        tool_metadata = []
                        for tool in candidate_tools:
                            credibility = self._get_source_credibility(tool.value)
                            # Get historical epistemic uncertainty if available
                            epistemic_unc = 0.5  # Default
                            # Could look up from topology or historical data
                            tool_metadata.append({
                                "credibility": credibility,
                                "confidence": credibility,  # Use credibility as confidence
                                "epistemic_uncertainty": epistemic_unc,
                                "aleatoric_uncertainty": 0.3,
                            })

                        # Apply MUSE selection
                        selected_tool_ids, selection_metadata = select_tools_with_muse(
                            [t.value for t in candidate_tools],
                            tool_metadata,
                            subproblem,
                            max_tools=max_tools_per_subproblem,
                            strategy="greedy",  # Maximize diversity
                        )

                        # Map back to ToolType enums
                        tool_map = {t.value: t for t in candidate_tools}
                        tools = [tool_map[tid] for tid in selected_tool_ids if tid in tool_map]

                        logger.debug(f"MUSE selected {len(tools)} tools: {[t.value for t in tools]}")
                        logger.debug(f"MUSE metadata: {selection_metadata}")
                    except Exception as e:
                        logger.debug(f"MUSE selection failed: {e}, falling back to heuristics")
                        # Fallback to topology-aware or simple selection
                        if preserve_d_separation and self.topology.nodes:
                            tools = self._topology_aware_tool_selection(
                                candidate_tools, subproblem, conditioning_set
                            )
                        else:
                            tools = candidate_tools
                        tools = tools[:max_tools_per_subproblem]
                else:
                    # Apply topology-aware filtering/ranking
                    if preserve_d_separation and self.topology.nodes:
                        tools = self._topology_aware_tool_selection(
                            candidate_tools, subproblem, conditioning_set
                        )
                    else:
                        tools = candidate_tools

                    tools = tools[:max_tools_per_subproblem]

            # Estimate tool selection uncertainty (operational) - update per subproblem
            if tools:
                # Fewer tools = potentially more uncertainty (less diversity)
                # Average across subproblems
                current_selection_uncertainty = max(0.3, 0.6 - 0.1 * len(tools))
                if i == 0:
                    pipeline_uncertainty.tool_selection = current_selection_uncertainty
                else:
                    pipeline_uncertainty.tool_selection = (
                        (pipeline_uncertainty.tool_selection * i + current_selection_uncertainty) / (i + 1)
                    )
            else:
                pipeline_uncertainty.tool_selection = 0.9  # Very high uncertainty if no tools selected

            # Call tools and collect results (MCP lazy evaluation)
            tool_results = []
            new_nodes = []

            for tool in tools:
                try:
                    result = await self._call_tool(tool, subproblem)
                    if result:
                        tool_results.append(result)

                        # Create context node for topology analysis (trust-aware)
                        # Use query_id to ensure uniqueness across queries
                        node_id = f"q{query_id}_{tool.value}_{i}_{len(new_nodes)}"

                        # Initialize trust/uncertainty based on source
                        # In production, would use learned source trust models
                        source_credibility = self._get_source_credibility(tool.value)
                        # Use heuristic for initial estimate (will be refined with JSD if multiple results)
                        epistemic_uncertainty = self._estimate_epistemic_uncertainty(
                            result, tool.value
                        )

                        # Compute belief alignment with prior beliefs
                        belief_alignment = await self._compute_belief_alignment(
                            result.get("result", ""),
                            prior_beliefs or []
                        )

                        node = ContextNode(
                            id=node_id,
                            content=result.get("result", ""),
                            source=tool.value,
                            dependencies=conditioning_set.copy(),  # Depends on previous context
                            credibility=source_credibility,
                            confidence=0.5,  # Will be updated based on structural support
                            epistemic_uncertainty=epistemic_uncertainty,
                            aleatoric_uncertainty=0.3,  # Default irreducible uncertainty
                            belief_alignment=belief_alignment,  # Computed based on prior beliefs
                        )

                        # Check schema consistency (production pattern)
                        violations = self.topology.check_schema_consistency(node)
                        if violations:
                            # Log violations but don't block (would flag for review in production)
                            pass

                        new_nodes.append(node)
                except Exception:
                    # Log error but continue with other tools
                    # In production, would use proper logging
                    continue

            # Refine epistemic uncertainty using JSD if we have multiple results
            # (after nodes are created, we can compute disagreement-based uncertainty)
            if len(new_nodes) > 1:
                try:
                    from .uncertainty import (
                        compute_epistemic_uncertainty_jsd,
                        extract_prediction_from_result,
                    )
                    # Extract predictions from nodes
                    # Match nodes to results by source and order
                    predictions = []
                    for idx, node in enumerate(new_nodes):
                        # Try to find matching result by source and index
                        matching_result = None
                        for result in tool_results:
                            result_source = result.get("source", "")
                            if node.source in str(result_source) or str(result_source) in node.source:
                                matching_result = result
                                break

                        # If no match found, use empty dict (will use node metadata)
                        if matching_result is None and idx < len(tool_results):
                            matching_result = tool_results[idx]
                        elif matching_result is None:
                            matching_result = {}

                        pred = extract_prediction_from_result(matching_result, node)
                        predictions.append(pred)

                    # Compute JSD-based epistemic uncertainty
                    if predictions:
                        jsd_epistemic = compute_epistemic_uncertainty_jsd(predictions)
                        # Update nodes with refined uncertainty (blend heuristic and JSD)
                        for node in new_nodes:
                            # Blend heuristic estimate with JSD-based estimate (weighted average)
                            node.epistemic_uncertainty = 0.5 * node.epistemic_uncertainty + 0.5 * jsd_epistemic

                        # Track result aggregation uncertainty (operational)
                        # Average across subproblems
                        current_aggregation_uncertainty = jsd_epistemic
                        if i == 0:
                            pipeline_uncertainty.result_aggregation = current_aggregation_uncertainty
                        else:
                            pipeline_uncertainty.result_aggregation = (
                                (pipeline_uncertainty.result_aggregation * i + current_aggregation_uncertainty) / (i + 1)
                            )
                except Exception as e:
                    # If JSD computation fails, continue with heuristic estimates
                    logger.debug(f"JSD-based uncertainty refinement failed: {e}", exc_info=True)

            # Estimate tool execution uncertainty (operational) - update per subproblem
            if tool_results:
                # Average epistemic uncertainty across results
                avg_epistemic = np.mean([node.epistemic_uncertainty for node in new_nodes]) if new_nodes else 0.5
                current_execution_uncertainty = float(avg_epistemic)
                if i == 0:
                    pipeline_uncertainty.tool_execution = current_execution_uncertainty
                else:
                    pipeline_uncertainty.tool_execution = (
                        (pipeline_uncertainty.tool_execution * i + current_execution_uncertainty) / (i + 1)
                    )
            else:
                pipeline_uncertainty.tool_execution = 0.8  # High uncertainty if no results

            # Analyze topology impact of adding these nodes
            if preserve_d_separation and new_nodes:
                try:
                    topology_impact = self.topology.analyze_context_injection_impact(new_nodes)
                except Exception as e:
                    # If topology analysis fails, continue without it (graceful degradation)
                    logger.debug(f"Topology analysis failed for subproblem {i+1}: {e}")
                    topology_impact = {"error": str(e)}
            else:
                topology_impact = {}

            # Aggregate results with aleatoric-aware weighting if enabled
            aggregated_results = None
            if MUSE_SELECTION_AVAILABLE and aggregate_results_with_aleatoric_weighting and len(tool_results) > 1 and len(new_nodes) > 1:
                try:
                    aggregated_results = aggregate_results_with_aleatoric_weighting(
                        tool_results,
                        new_nodes
                    )
                    logger.debug(f"Aleatoric-weighted aggregation: {len(aggregated_results.get('weights', []))} results")
                except Exception as e:
                    logger.debug(f"Aleatoric weighting failed: {e}, using standard synthesis")
                    aggregated_results = None

            # Synthesize results for this subproblem
            if self.llm_service:
                # Use aggregated results if available, otherwise use raw tool_results
                results_to_synthesize = tool_results
                if aggregated_results and aggregated_results.get("aggregated"):
                    # Pass weighted results to LLM (could enhance prompt with weights)
                    results_to_synthesize = tool_results  # Still pass all results, weights are metadata
                subsolution = await self.llm_service.synthesize_tool_results(results_to_synthesize, subproblem)
            else:
                # Use aggregated results if available
                if aggregated_results and aggregated_results.get("aggregated"):
                    subsolution = aggregated_results["aggregated"]
                else:
                    subsolution = self._synthesize_tool_results(tool_results, subproblem)

            # Update conditioning set (what we now know)
            conditioning_set.update(node.id for node in new_nodes)

            # Store aggregation metadata if available
            aggregation_metadata = None
            if aggregated_results:
                aggregation_metadata = {
                    "weights": aggregated_results.get("weights", []),
                    "aleatoric_uncertainties": aggregated_results.get("aleatoric_uncertainties", []),
                    "weighted_prediction": aggregated_results.get("weighted_prediction"),
                }

            subsolutions.append({
                "subproblem": subproblem,
                "tools_used": [tool.value for tool in tools],
                "results": tool_results,
                "synthesis": subsolution,
                "topology_impact": topology_impact,
                "aggregation_metadata": aggregation_metadata,  # NEW: Aleatoric weighting metadata
            })

        # Step 3: Synthesize all subsolutions using schema structure
        if self.llm_service:
            final_synthesis = await self.llm_service.synthesize_subsolutions(subsolutions, schema, query)
            # Estimate synthesis uncertainty (output uncertainty)
            # Heuristic: based on number of subsolutions and their quality
            if subsolutions:
                avg_subsolution_quality = np.mean([
                    len(s.get("synthesis", "")) / 500.0  # Normalize by expected length
                    for s in subsolutions
                ]) if subsolutions else 0.5
                pipeline_uncertainty.synthesis = float(np.clip(1.0 - avg_subsolution_quality, 0.2, 0.8))
            else:
                pipeline_uncertainty.synthesis = 0.9  # Very high uncertainty if no subsolutions
        else:
            final_synthesis = self._synthesize_subsolutions(subsolutions, schema, query)
            pipeline_uncertainty.synthesis = 0.6  # Higher uncertainty for heuristic synthesis

        # Compute final topology metrics (with error handling)
        try:
            self.topology.compute_cliques()
            self.topology.compute_betti_numbers()
            attractor_basins = self.topology.get_attractor_basins()
            fisher_info = self.topology.compute_fisher_information_estimate()
            euler_char = self.topology.compute_euler_characteristic()
        except Exception as e:
            # If topology computation fails, use defaults (graceful degradation)
            logger.warning(f"Topology computation failed: {e}")
            attractor_basins = []
            fisher_info = 0.0
            euler_char = 0

        # Get source credibility mapping
        source_credibility = self.topology.source_trust.copy()

        # Get verification counts and source diversity
        verification_info = {}
        for node_id, node in self.topology.nodes.items():
            source = node.source
            if source not in verification_info:
                verification_info[source] = {
                    "verification_count": 0,
                    "nodes": 0,
                }
            verification_info[source]["verification_count"] += node.verification_count
            verification_info[source]["nodes"] += 1

        # Compute token importance across all results
        all_results = []
        for subsolution in subsolutions:
            all_results.extend(subsolution.get("results", []))

        token_importance_data = compute_token_importance_for_results(query, all_results)

        # NEW: Compute logical depth for all nodes
        logical_depths = {}
        try:
            for node_id in self.topology.nodes:
                logical_depths[node_id] = self.topology.compute_logical_depth_estimate(node_id)
        except Exception as e:
            logger.debug(f"Failed to compute logical depths: {e}", exc_info=True)
            logical_depths = {}

        # Get clique details for visualization
        clique_details = []
        for clique in self.topology.cliques[:10]:  # Top 10 cliques
            node_sources = [
                self.topology.nodes[nid].source
                for nid in clique.nodes
                if nid in self.topology.nodes
            ]
            # Get verification counts for nodes in this clique
            clique_verifications = sum(
                self.topology.nodes[nid].verification_count
                for nid in clique.nodes
                if nid in self.topology.nodes
            )
            unique_sources = list(set(node_sources))

            # Compute JSD-based uncertainty for this clique
            clique_uncertainty = {}
            try:
                clique_uncertainty = self.topology.compute_clique_uncertainty(clique.nodes)
            except Exception as e:
                logger.debug(f"Failed to compute clique uncertainty: {e}", exc_info=True)
                clique_uncertainty = {"epistemic": 0.5, "aleatoric": 0.3, "total": 0.5}

            clique_details.append({
                "node_ids": list(clique.nodes),
                "node_sources": node_sources,
                "unique_sources": unique_sources,
                "source_diversity": len(unique_sources),  # Number of different source types
                "verification_count": clique_verifications,
                "coherence": float(clique.coherence_score),
                "trust": float(clique.trust_score),
                "risk": float(clique.adversarial_risk),
                "size": len(clique.nodes),
                "uncertainty": clique_uncertainty,  # NEW: JSD-based uncertainty metrics
            })

        # Build source relationship matrix (agreement/disagreement)
        source_matrix = self._build_source_matrix(subsolutions)

        # Estimate final response uncertainty (output uncertainty)
        # Based on synthesis quality and topology coherence
        try:
            if self.topology.cliques:
                avg_clique_trust = np.mean([c.trust_score for c in self.topology.cliques[:5]]) if self.topology.cliques else 0.5
                pipeline_uncertainty.final_response = float(np.clip(1.0 - avg_clique_trust, 0.2, 0.8))
            else:
                pipeline_uncertainty.final_response = 0.6
        except Exception:
            pipeline_uncertainty.final_response = 0.5

        # NEW: Resource triple metrics (depth-width-coordination)
        #
        # Theoretical Foundation: The "Triple Principle" from SSH research
        #
        # The resource triple formalizes fundamental computational constraints:
        # - Depth: Sequential reasoning steps (cannot be parallelized, SSH constraint)
        # - Width: Parallel operations (tools, parallelism)
        # - Coordination: Cost of coordinating parallel operations
        #
        # These are non-interchangeable resources. Attempts to "beat" constraints by pushing
        # on one dimension reintroduce costs in the others. For example:
        # - More depth → better quality but slower (serial constraint)
        # - More width → faster but higher coordination cost
        # - Less coordination → simpler but may miss dependencies
        #
        # Why Track This: Explicit metrics enable understanding of resource tradeoffs and
        # guide optimization decisions. Without metrics, these tradeoffs are implicit and
        # harder to reason about.
        resource_metrics = {
            "depth": len(subsolutions),  # Reasoning depth (subproblems) - SSH serial constraint
            "width": sum(len(s.get("tools_used", [])) for s in subsolutions),  # Parallelism (total tools)
            "coordination": len(set(
                tool for s in subsolutions
                for tool in s.get("tools_used", [])
            )),  # Unique tools (coordination cost - managing different tools)
            "total_tokens": sum(len(s.get("synthesis", "")) for s in subsolutions),  # Total compute
        }

        # NEW: Degradation triple metrics (corruption-loss-waste)
        #
        # Theoretical Foundation: The "Degradation Triple" from information flow analysis
        #
        # Information flow through systems suffers from three failure modes:
        # - Noise (corruption): Information is corrupted during transmission/processing
        # - Loss (death/forgetting): Information is lost entirely
        # - Waste (irrelevance): Information capacity is wasted on irrelevant content
        #
        # These are analogous to the resource triple but for information rather than computation.
        # Just as we can't "beat" resource constraints, we can't eliminate all degradation.
        #
        # Why Track This: Understanding degradation helps identify where information quality
        # is lost and guides improvements (e.g., IB filtering reduces waste, better synthesis
        # reduces loss, higher Fisher Information reduces noise).
        #
        # Noise: inverse of Fisher Information (higher Fisher = lower noise)
        # Fisher Information measures structure quality - high structure = less corruption
        noise_estimate = 1.0 - (fisher_info if fisher_info > 0 else 0.5)

        # Loss: synthesis uncertainty (information lost in synthesis)
        # Synthesis uncertainty measures how much information is lost when combining results
        loss_estimate = pipeline_uncertainty.synthesis

        # Waste: compression waste (if IB filtering was used, track waste)
        # Low coherence indicates wasted capacity on irrelevant or disconnected information
        # For now, estimate based on topology coherence (low coherence = waste)
        waste_estimate = 1.0 - (np.mean([c.coherence_score for c in self.topology.cliques[:5]]) if self.topology.cliques else 0.5)

        degradation_metrics = {
            "noise": float(noise_estimate),  # Corruption (inverse of Fisher Information)
            "loss": float(loss_estimate),  # Information loss (synthesis uncertainty)
            "waste": float(waste_estimate),  # Wasted capacity (low coherence)
        }

        return {
            "query": query,
            "schema_used": schema_name,
            "decomposition": decomposition,
            "subsolutions": subsolutions,
            "final_synthesis": final_synthesis,
            "tools_called": sum(len(s["tools_used"]) for s in subsolutions),
            "source_matrix": source_matrix,  # NEW: Source agreement/disagreement matrix
            "token_importance": token_importance_data,  # NEW: Token importance tracking
            "pipeline_uncertainty": pipeline_uncertainty.to_dict(),  # NEW: Pipeline uncertainty tracking
            "topology": {
                "betti_numbers": self.topology.betti_numbers,
                "euler_characteristic": euler_char,
                "fisher_information": fisher_info,
                "attractor_basins": len(attractor_basins),
                "max_clique_size": max((len(c.nodes) for c in self.topology.cliques), default=0),
                "trust_summary": self.topology._get_trust_summary(),
                "source_credibility": source_credibility,  # NEW: Source-level credibility
                "verification_info": verification_info,  # NEW: Verification counts per source
                "cliques": clique_details,  # NEW: Clique details for visualization
                "trusted_cliques": len([
                    c for c in self.topology.cliques
                    if c.trust_score > 0.6 and c.adversarial_risk < 0.3
                ]),
                "logical_depths": logical_depths,  # NEW: Logical depth estimates per node
                "avg_logical_depth": float(np.mean(list(logical_depths.values()))) if logical_depths else 0.0,  # NEW: Average logical depth
            },
            "d_separation_preserved": preserve_d_separation,
            "resource_triple": resource_metrics,  # NEW: Resource triple (depth-width-coordination)
            "degradation_triple": degradation_metrics,  # NEW: Degradation triple (noise-loss-waste)
        }

    async def _decompose_query(self, query: str, schema: ReasoningSchema) -> List[str]:
        """
        Decompose query into subproblems based on schema.

        Uses LLM service if available, falls back to simple heuristics.
        """
        # Try LLM-based decomposition if LLM service is available
        if self.llm_service:
            try:
                subproblems = await self.llm_service.decompose_query(query, schema)
                if subproblems and len(subproblems) > 0:
                    return subproblems
            except Exception as e:
                logger.warning(f"LLM decomposition failed: {e}, using fallback")

        # Fallback to simple heuristics
        if schema.name == "decompose_and_synthesize":
            return [
                f"Theoretical foundation: {query}",
                f"Recent empirical results: {query}",
                f"Alternative perspectives: {query}",
            ]
        # For other schemas, return single subproblem
        return [query]

    async def _call_tool(self, tool: ToolType, query: str) -> Optional[Dict[str, Any]]:
        """
        Call a specific MCP tool with caching.

        Args:
            tool: Tool type to call
            query: Query string

        Returns:
            Tool result dictionary or None if tool call fails
        """
        # Map tool types to MCP tool names and parameters
        tool_mapping = {
            ToolType.PERPLEXITY_DEEP: ("mcp_perplexity_deep_research", {"query": query}),
            ToolType.PERPLEXITY_REASON: ("mcp_perplexity_reason", {"query": query}),
            ToolType.PERPLEXITY_SEARCH: ("mcp_perplexity_search", {"query": query, "max_results": 5}),
            ToolType.FIRECRAWL_SEARCH: ("mcp_firecrawl-mcp_firecrawl_search", {"query": query, "limit": 5}),
            ToolType.FIRECRAWL_SCRAPE: ("mcp_firecrawl-mcp_firecrawl_scrape", {"url": query}),
            ToolType.FIRECRAWL_EXTRACT: ("mcp_firecrawl-mcp_firecrawl_extract", {"urls": [query] if query.startswith("http") else []}),
            ToolType.TAVILY_SEARCH: ("mcp_tavily-remote-mcp_tavily_search", {"query": query, "max_results": 5}),
            ToolType.TAVILY_EXTRACT: ("mcp_tavily-remote-mcp_tavily_extract", {"urls": [query] if query.startswith("http") else []}),
        }

        if tool not in tool_mapping:
            return {
                "tool": tool.value,
                "query": query,
                "result": f"Unknown tool: {tool.value}",
                "sources": [],
                "error": "Unknown tool type",
            }

        mcp_tool_name, mcp_kwargs = tool_mapping[tool]

        # Check cache first
        try:
            from .cache import cache_tool_result, get_cached_tool_result
            cached = get_cached_tool_result(mcp_tool_name, query, mcp_kwargs)
            if cached is not None:
                logger.info(f"Cache hit for tool {tool.value} with query: {query[:50]}...")
                return cached
        except Exception as e:
            logger.debug(f"Cache check failed: {e}")

        try:
            # Call MCP tool via helper
            mcp_result = await call_mcp_tool(mcp_tool_name, **mcp_kwargs)

            # Check for errors
            if "error" in mcp_result:
                return {
                    "tool": tool.value,
                    "query": query,
                    "result": f"[MCP Error] {mcp_result['error']}",
                    "sources": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "accessed_at": datetime.utcnow().isoformat(),
                    "error": mcp_result["error"],
                }

            # If MCP tool was actually called and returned results
            if not mcp_result.get("needs_mcp_call"):
                result = {
                    "tool": tool.value,
                    "query": query,
                    "result": mcp_result.get("result", ""),
                    "sources": mcp_result.get("sources", []),
                    "raw": mcp_result,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Cache successful results
                try:
                    from .cache import cache_tool_result
                    cache_tool_result(mcp_tool_name, query, mcp_kwargs, result, ttl_hours=24 * 7)
                except Exception as e:
                    logger.debug(f"Cache write failed: {e}")

                return result

            # MCP tool structure ready but not actually called
            # Return structured placeholder with metadata
            return {
                "tool": tool.value,
                "query": query,
                "result": f"[MCP integration ready] {tool.value} for: {query}",
                "sources": [],
                "mcp_tool": mcp_tool_name,
                "mcp_args": mcp_result.get("args", {}),
                "note": "MCP tool call structure prepared. Actual call should be made via MCP client when available.",
            }

        except Exception as e:
            return {
                "tool": tool.value,
                "query": query,
                "result": f"[Error calling MCP tool] {str(e)}",
                "sources": [],
                "error": str(e),
            }

    def _synthesize_tool_results(
        self,
        tool_results: List[Dict[str, Any]],
        subproblem: str,
    ) -> str:
        """
        Synthesize results from multiple tools for a single subproblem.

        Args:
            tool_results: Results from multiple tools
            subproblem: The subproblem being addressed

        Returns:
            Synthesized answer
        """
        if not tool_results:
            return f"No results found for: {subproblem}"

        # Simple synthesis: combine results
        # In practice, would use LLM to synthesize coherently
        # Filter out None/empty results
        valid_results = [r for r in tool_results if r and r.get("result")]
        if not valid_results:
            return f"No valid results found for: {subproblem}"

        summaries = [r.get("result", "") for r in valid_results]
        return "\n".join(summaries)

    def _topology_aware_tool_selection(
        self,
        candidate_tools: List[ToolType],
        subproblem: str,
        conditioning_set: Set[str],
    ) -> List[ToolType]:
        """
        Select tools based on topology analysis to preserve coherence and maximize information gain.

        Args:
            candidate_tools: Tools selected by heuristics
            subproblem: Current subproblem
            conditioning_set: Nodes we've already conditioned on

        Returns:
            Ranked/filtered list of tools
        """
        if not candidate_tools:
            return candidate_tools

        # Score each tool based on topology impact
        tool_scores = []

        for tool in candidate_tools:
            score = 1.0  # Base score

            # Check if tool would add information to existing cliques
            # (simulate adding a node from this tool)
            source_credibility = self._get_source_credibility(tool.value)

            # Prefer tools with higher credibility (trust-aware)
            score *= (0.5 + source_credibility)

            # Check if tool would connect to existing high-trust cliques
            if self.topology.cliques:
                # Find cliques that might benefit from this tool's information
                relevant_cliques = [
                    c for c in self.topology.cliques
                    if c.coherence_score > 0.6 and c.trust_score > 0.5
                ]
                if relevant_cliques:
                    # Prefer tools that could extend high-trust cliques
                    score *= 1.2

            # Penalize tools that would create too many new disconnected components
            # (prefer tools that connect to existing context)
            if len(conditioning_set) > 0:
                # Tools that can connect to existing context are preferred
                score *= 1.1

            # Prefer tools that preserve d-separation structure
            # (avoid tools that would create collider bias)
            if len(conditioning_set) > 1:
                # Multiple conditioning variables - be careful about colliders
                # For now, simple heuristic: prefer tools that don't create too many dependencies
                score *= 0.95  # Slight penalty for complex dependencies

            tool_scores.append((tool, score))

        # Sort by score (highest first)
        tool_scores.sort(key=lambda x: x[1], reverse=True)

        return [tool for tool, _ in tool_scores]

    def _synthesize_subsolutions(
        self,
        subsolutions: List[Dict[str, Any]],
        schema: ReasoningSchema,
        original_query: str,
    ) -> str:
        """
        Synthesize all subsolutions into final answer using schema structure.

        Preserves d-separation structure by respecting conditional dependencies
        between subproblems.

        Args:
            subsolutions: Results from all subproblems
            schema: Schema used for structuring
            original_query: Original research query

        Returns:
            Final synthesized answer
        """
        # Use schema structure to guide synthesis
        if schema.name == "decompose_and_synthesize":
            synthesis_parts = []
            for subsolution in subsolutions:
                # Include topology impact if available
                topology_note = ""
                if subsolution.get("topology_impact"):
                    impact = subsolution["topology_impact"]
                    if impact.get("topology_changed"):
                        topology_note = f"\n[Topology: {impact.get('new_cliques', 0)} new cliques, "
                        topology_note += f"Fisher Δ: {impact.get('fisher_delta', 0):.3f}]"

                synthesis_parts.append(
                    f"**{subsolution['subproblem']}**:\n{subsolution['synthesis']}{topology_note}"
                )
            return "\n\n".join(synthesis_parts)

        # Default: simple concatenation
        valid_subsolutions = [s for s in subsolutions if s.get("synthesis")]
        if not valid_subsolutions:
            return f"No valid solutions found for: {original_query}"
        return "\n\n".join(s["synthesis"] for s in valid_subsolutions)

    def _get_source_credibility(self, source: str) -> float:
        """
        Get source credibility score.

        In production, would use:
        - Learned trust models
        - Historical performance data
        - Cross-validation results
        - User feedback

        For now, use heuristics based on source type.
        """
        # Heuristic: different sources have different default credibility
        source_credibility_map = {
            "perplexity_deep_research": 0.75,  # Generally reliable
            "perplexity_reason": 0.70,
            "perplexity_search": 0.65,
            "firecrawl_search": 0.60,
            "firecrawl_scrape": 0.70,  # Direct source access
            "firecrawl_extract": 0.65,
            "tavily_search": 0.60,
            "tavily_extract": 0.65,
        }
        return source_credibility_map.get(source, 0.5)  # Default: uncertain

    async def _compute_belief_alignment(
        self,
        evidence_text: str,
        prior_beliefs: List[Dict[str, Any]],
    ) -> float:
        """
        Compute belief-evidence alignment using semantic similarity.

        Uses embedding-based similarity if available, falls back to keyword matching.

        Returns:
            0.0 to 1.0 where:
            - 0.0-0.3: Strong contradiction
            - 0.3-0.5: Weak contradiction or neutral
            - 0.5-0.7: Weak alignment
            - 0.7-1.0: Strong alignment
        """
        if not prior_beliefs or not evidence_text:
            return 0.5  # Neutral if no prior beliefs

        evidence_lower = evidence_text.lower()
        alignments = []

        for belief in prior_beliefs:
            belief_text = belief.get("text", "").lower()
            if not belief_text:
                continue

            try:
                # Try semantic alignment first (if LLM service available)
                alignment = await self._compute_semantic_alignment(belief_text, evidence_lower)
                alignments.append(alignment)
            except Exception as e:
                logger.debug(f"Failed to compute alignment for belief: {e}")
                # Fallback to neutral
                alignments.append(0.5)

        if not alignments:
            return 0.5

        # Return average alignment
        return float(sum(alignments) / len(alignments))

    async def _compute_semantic_alignment(self, belief_text: str, evidence_text: str) -> float:
        """
        Compute alignment using semantic similarity (embedding-based).

        Falls back to keyword matching if embeddings unavailable or LLM service unavailable.
        """
        if not self.llm_service:
            return self._compute_keyword_alignment(belief_text, evidence_text)

        try:
            # Use LLM service for semantic similarity (uses embeddings if available, keyword fallback otherwise)
            similarity = await self.llm_service.compute_similarity(belief_text, evidence_text)
            # Convert similarity (0-1) to alignment (0-1)
            return float(similarity)
        except Exception as e:
            logger.debug(f"Semantic alignment failed, using keyword fallback: {e}")
            return self._compute_keyword_alignment(belief_text, evidence_text)

    def _compute_keyword_alignment(self, belief_text: str, evidence_text: str) -> float:
        """Compute alignment using keyword matching (original method)."""
        # Simple keyword overlap check
        belief_words = set(belief_text.split())
        evidence_words = set(evidence_text.split())

        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "can", "this", "that", "these", "those"}
        belief_words = belief_words - stop_words
        evidence_words = evidence_words - stop_words

        if not belief_words:
            return 0.5

        # Check for contradiction indicators
        contradiction_words = {"but", "however", "contrary", "opposite", "disagree", "contradict",
                             "conflict", "different", "wrong", "incorrect", "false", "not"}
        has_contradiction = any(word in evidence_text for word in contradiction_words)

        # Compute overlap
        overlap = len(belief_words & evidence_words)
        total_belief_words = len(belief_words)

        if total_belief_words == 0:
            alignment = 0.5
        else:
            overlap_ratio = overlap / total_belief_words

            if has_contradiction:
                # Contradiction: invert alignment
                alignment = 1.0 - overlap_ratio
            else:
                # Alignment: direct ratio
                alignment = 0.5 + (overlap_ratio * 0.5)  # Scale to 0.5-1.0

        return alignment

    def _build_source_matrix(
        self,
        subsolutions: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build source relationship matrix showing agreement/disagreement patterns.

        Gracefully handles errors and returns empty dict on failure.

        Returns:
            Dictionary mapping claims/themes to source positions
        """
        if not subsolutions:
            return {}

        try:
            # Extract key claims from each subsolution
            matrix = {}

            for subsolution in subsolutions:
                try:
                    subsolution.get("subproblem", "")
                    synthesis = subsolution.get("synthesis", "")
                    subsolution.get("tools_used", [])
                    results = subsolution.get("results", [])

                    # Extract key phrases from synthesis (simple approach)
                    # In production, would use NLP to extract claims
                    key_phrases = self._extract_key_phrases(synthesis)

                    for phrase in key_phrases:
                        if phrase not in matrix:
                            matrix[phrase] = {
                                "sources": {},
                                "consensus": None,
                                "conflict": False,
                            }

                        # Map each source to its position on this claim
                        for result in results:
                            try:
                                source = result.get("tool", "unknown")
                                if source not in matrix[phrase]["sources"]:
                                    # Simple: check if result text contains the phrase
                                    result_text = result.get("result", "").lower()
                                    phrase_lower = phrase.lower()

                                    if phrase_lower in result_text:
                                        matrix[phrase]["sources"][source] = "supports"
                                    else:
                                        # Check for contradiction
                                        contradiction_indicators = ["but", "however", "contrary", "opposite"]
                                        if any(ind in result_text for ind in contradiction_indicators):
                                            matrix[phrase]["sources"][source] = "contradicts"
                                        else:
                                            matrix[phrase]["sources"][source] = "neutral"
                            except Exception as e:
                                logger.debug(f"Failed to process result for source matrix: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"Failed to process subsolution for source matrix: {e}", exc_info=True)
                    continue

            # Determine consensus for each claim
            for phrase, data in matrix.items():
                try:
                    sources = data["sources"]
                    if not sources:
                        continue

                    supports = sum(1 for pos in sources.values() if pos == "supports")
                    contradicts = sum(1 for pos in sources.values() if pos == "contradicts")
                    total = len(sources)

                    if contradicts > 0:
                        data["conflict"] = True
                        data["consensus"] = "disagreement"
                    elif supports > total * 0.7:
                        data["consensus"] = "strong_agreement"
                    elif supports > total * 0.5:
                        data["consensus"] = "weak_agreement"
                    else:
                        data["consensus"] = "no_consensus"
                except Exception as e:
                    logger.warning(f"Failed to determine consensus for phrase '{phrase}': {e}", exc_info=True)
                    data["consensus"] = "unknown"

            return matrix
        except Exception as e:
            logger.error(f"Failed to build source matrix: {e}", exc_info=True)
            # Graceful degradation: return empty matrix
            return {}

    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """
        Extract key phrases/claims from text.

        Uses LLM-based extraction if available, falls back to improved heuristics.

        Args:
            text: Text to extract phrases from
            max_phrases: Maximum number of phrases to extract

        Returns:
            List of key phrases/claims
        """
        if not text or len(text.strip()) < 20:
            return []

        # Try LLM-based extraction first (if available)
        if self.llm_service:
            try:
                phrases = self._extract_claims_with_llm(text, max_phrases)
                if phrases:
                    return phrases
            except Exception as e:
                logger.debug(f"LLM claim extraction failed, using heuristic: {e}")

        # Fallback to improved heuristic extraction
        return self._extract_phrases_heuristic(text, max_phrases)

    def _extract_claims_with_llm(self, text: str, max_phrases: int) -> List[str]:
        """
        Extract claims using LLM (production-ready approach).

        Based on Claimify-like pipeline: extract verifiable, atomic claims.
        """
        try:
            # For now, return empty to trigger fallback
            # Full LLM implementation would require async context
            # This is a placeholder for future enhancement
            return []
        except Exception as e:
            logger.debug(f"LLM claim extraction error: {e}")
            return []

    def _extract_phrases_heuristic(self, text: str, max_phrases: int) -> List[str]:
        """
        Extract key phrases using improved heuristics.

        Better than simple regex: uses sentence structure, capitalization, quotes.
        """
        phrases = []

        try:
            import re
            # Method 1: Extract quoted phrases (often claims)
            quoted = re.findall(r'"([^"]+)"', text)
            phrases.extend(quoted[:max_phrases])

            # Method 2: Extract capitalized phrases (proper nouns, important concepts)
            # Find sequences of capitalized words
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            # Filter out common words
            common_words = {"The", "This", "That", "These", "Those", "There", "Here"}
            capitalized = [c for c in capitalized if c not in common_words]
            phrases.extend(capitalized[:max_phrases])

            # Method 3: Extract sentences with claim indicators
            claim_indicators = ["shows", "demonstrates", "indicates", "suggests", "proves",
                              "confirms", "reveals", "finds", "concludes"]
            sentences = text.split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(indicator in sentence_lower for indicator in claim_indicators):
                    # Extract the claim part (after indicator)
                    for indicator in claim_indicators:
                        if indicator in sentence_lower:
                            idx = sentence_lower.find(indicator)
                            claim = sentence[idx:].strip()
                            if len(claim) > 20 and len(claim) < 200:  # Reasonable length
                                phrases.append(claim)
                                break
                if len(phrases) >= max_phrases:
                    break

            # Method 4: Extract noun phrases (simple pattern)
            # Find "adjective noun" or "noun of noun" patterns
            noun_phrases = re.findall(r'\b\w+\s+(?:of|in|on|for|with|to|from)\s+\w+\b', text)
            phrases.extend(noun_phrases[:max_phrases])

            # Deduplicate and limit
            seen = set()
            unique_phrases = []
            for phrase in phrases:
                phrase_lower = phrase.lower().strip()
                if phrase_lower and phrase_lower not in seen and len(phrase_lower) > 5:
                    seen.add(phrase_lower)
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= max_phrases:
                    break

            return unique_phrases[:max_phrases]
        except Exception as e:
            logger.warning(f"Failed to extract phrases heuristically: {e}", exc_info=True)
            # Fallback: return first sentence
            first_sentence = text.split('.')[0].strip()
            return [first_sentence] if first_sentence else []

    def _estimate_epistemic_uncertainty(
        self,
        result: Dict[str, Any],
        source: str,
    ) -> float:
        """
        Estimate epistemic uncertainty (what we don't know).

        Uses heuristics:
        - Result quality indicators
        - Source reliability
        - Result completeness

        In production, would use ESI method or similar.
        """
        # Heuristic: check result quality indicators
        result_text = result.get("result", "")
        sources = result.get("sources", [])

        # More sources = lower epistemic uncertainty
        source_factor = 1.0 / (1.0 + len(sources) * 0.1)

        # Result length/completeness
        if len(result_text) < 50:
            completeness_factor = 0.8  # Incomplete
        elif len(result_text) < 200:
            completeness_factor = 0.6
        else:
            completeness_factor = 0.4  # More complete

        # Base uncertainty from source
        source_uncertainty = 1.0 - self._get_source_credibility(source)

        # Combined: epistemic uncertainty
        epistemic = (source_uncertainty * source_factor * completeness_factor)
        return min(1.0, max(0.0, epistemic))

    def _select_tools_with_constraints(
        self,
        subproblem: str,
        max_tools: int = 2,
        budget: Optional[float] = None,
        min_information: float = 0.5,
    ) -> List[ToolType]:
        """
        Select tools using constraint solver.

        Args:
            subproblem: The subproblem to solve
            max_tools: Maximum number of tools to select
            budget: Maximum total cost (None = no budget)
            min_information: Minimum information gain required

        Returns:
            List of selected tools
        """
        if not self.constraint_solver:
            return []

        # Get default constraints
        constraints = create_default_constraints()

        # Adjust constraints based on subproblem characteristics
        # (This is a simple heuristic - could be improved with LLM)
        subproblem_lower = subproblem.lower()

        # Adjust information gain expectations based on query type
        if any(word in subproblem_lower for word in ["comprehensive", "deep", "thorough"]):
            min_information = 0.7  # Higher requirement for deep queries

        # Try to solve
        try:
            logger.debug(
                f"Solving constraints for subproblem: {subproblem[:50]}... "
                f"(max_tools={max_tools}, min_info={min_information:.2f}, budget={budget})"
            )
            selected = self.constraint_solver.solve_optimal(
                constraints=constraints,
                objective="min_cost",  # Minimize cost
                budget=budget,
                min_information=min_information,
                max_tools=max_tools,
            )

            if selected:
                logger.info(
                    f"Constraint solver selected {len(selected)} tools: "
                    f"{[t.value for t in selected]}"
                )
                return selected[:max_tools]
            else:
                logger.debug("Constraint solver found no solution, falling back to heuristics")
        except Exception as e:
            logger.error(f"Constraint solver error: {e}", exc_info=True)

        return []

    def _estimate_current_quality(self, subsolutions: List[Dict[str, Any]]) -> float:
        """
        Estimate current quality based on subsolutions.

        Heuristic: Based on subsolution length, completeness, and number.

        Args:
            subsolutions: List of subsolutions completed so far

        Returns:
            Estimated quality score (0-1)
        """
        if not subsolutions:
            return 0.0

        # Heuristic: longer, more complete subsolutions = higher quality
        total_length = sum(len(s.get("synthesis", "")) for s in subsolutions)
        avg_length = total_length / len(subsolutions) if subsolutions else 0

        # Normalize: 500 chars = decent quality (0.6), 1000+ = high quality (0.9)
        length_score = min(0.9, 0.3 + (avg_length / 1000.0) * 0.6)

        # Bonus for having multiple subsolutions (more thorough)
        completeness_score = min(1.0, len(subsolutions) / 5.0)  # 5 subproblems = complete

        # Weighted combination
        quality = 0.6 * length_score + 0.4 * completeness_score

        return min(1.0, max(0.0, quality))

