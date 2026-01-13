"""Adaptive quality improvements based on feedback loop insights."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    pass
import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .quality_feedback import QualityFeedbackLoop

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveStrategy:
    """Strategy for adapting system behavior based on quality feedback."""

    schema_selection: str  # Best schema for this query type
    expected_length: int  # Expected response length
    should_use_research: bool  # Whether research improves quality
    tool_preferences: List[str]  # Preferred tools for this query type
    confidence: float  # Confidence in this strategy
    reasoning_depth: int = 3  # Estimated minimum reasoning depth (subproblems)
    early_stop_threshold: Optional[float] = None  # Quality threshold for early stopping


class AdaptiveQualityManager:
    """
    Manages adaptive improvements based on quality feedback.

    Learns from quality feedback to:
    - Select optimal schemas for query types
    - Determine optimal response length
    - Decide when research helps vs hurts
    - Suggest tool preferences
    - Adapt system behavior automatically

    Persistence: Learning structures can be saved/loaded for faster initialization.
    """

    def __init__(
        self,
        quality_feedback: QualityFeedbackLoop,
        learning_data_path: Optional[Path] = None,
    ):
        """
        Initialize adaptive quality manager.

        Args:
            quality_feedback: Quality feedback loop to learn from
            learning_data_path: Optional path to persist/load learning data
        """
        self.quality_feedback = quality_feedback
        self.learning_data_path = learning_data_path or Path("data/results/adaptive_learning.json")

        # Learning data structures
        self.query_type_to_schema: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.query_type_to_length: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self.research_impact: Dict[str, List[Tuple[bool, float]]] = defaultdict(list)
        self.tool_performance: Dict[str, List[float]] = defaultdict(list)
        # NEW: Track reasoning depth thresholds
        self.query_type_to_depth: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        # Format: (num_subproblems, quality_score)

        # Try to load persisted learning data, otherwise rebuild from history
        if not self._load_learning():
            self._learn_from_history()
            # Also learn from sessions if available
            if hasattr(quality_feedback, 'session_manager') and quality_feedback.session_manager:
                self._learn_from_sessions()

    def _load_learning(self) -> bool:
        """
        Load persisted learning data.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.learning_data_path.exists():
            return False

        try:
            data = json.loads(self.learning_data_path.read_text())

            # Load query_type_to_schema (convert back to defaultdict)
            schema_data = data.get("query_type_to_schema", {})
            for q_type, schemas in schema_data.items():
                for schema, scores in schemas.items():
                    self.query_type_to_schema[q_type][schema].extend(scores)

            # Load query_type_to_length
            length_data = data.get("query_type_to_length", {})
            for q_type, lengths in length_data.items():
                self.query_type_to_length[q_type].extend([tuple(l) for l in lengths])

            # Load research_impact
            research_data = data.get("research_impact", {})
            for q_type, impacts in research_data.items():
                self.research_impact[q_type].extend([tuple(i) for i in impacts])

            # Load tool_performance
            tool_data = data.get("tool_performance", {})
            for tool, scores in tool_data.items():
                self.tool_performance[tool].extend(scores)

            # Load query_type_to_depth
            depth_data = data.get("query_type_to_depth", {})
            for q_type, depths in depth_data.items():
                self.query_type_to_depth[q_type].extend([tuple(d) for d in depths])

            return True
        except Exception:
            return False

    def _save_learning(self):
        """Save learning data to disk."""
        data = {
            "version": "1.0",
            "query_type_to_schema": {
                q_type: {
                    schema: scores
                    for schema, scores in schemas.items()
                }
                for q_type, schemas in self.query_type_to_schema.items()
            },
            "query_type_to_length": {
                q_type: [list(l) for l in lengths]
                for q_type, lengths in self.query_type_to_length.items()
            },
            "research_impact": {
                q_type: [list(i) for i in impacts]
                for q_type, impacts in self.research_impact.items()
            },
            "tool_performance": {
                tool: scores
                for tool, scores in self.tool_performance.items()
            },
            "query_type_to_depth": {
                q_type: [list(d) for d in depths]
                for q_type, depths in self.query_type_to_depth.items()
            },
        }

        self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_data_path.write_text(json.dumps(data, indent=2))

    def _learn_from_history(self):
        """Learn patterns from existing quality feedback history."""
        for entry in self.quality_feedback.history:
            score = entry.get("score", 0)
            metadata = entry.get("metadata", {})
            query = entry.get("query", "")

            # Learn schema performance by query characteristics
            schema = metadata.get("schema")
            if schema:
                # Analyze query to determine type
                query_type = self._classify_query(query)
                self.query_type_to_schema[query_type][schema].append(score)

            # Learn response length preferences
            # Prefer explicit length if available, otherwise use response length
            response_length = entry.get("response_length")
            if response_length is None:
                response = entry.get("response", "")
                response_length = len(response) if response else 0

            if response_length > 0:
                query_type = self._classify_query(query)
                self.query_type_to_length[query_type].append((response_length, score))

            # Learn research impact
            used_research = metadata.get("research", False)
            query_type = self._classify_query(query)
            self.research_impact[query_type].append((used_research, score))

    def _learn_from_sessions(self):
        """Learn patterns from hierarchical session structures."""
        if not hasattr(self.quality_feedback, 'session_manager') or not self.quality_feedback.session_manager:
            return

        session_manager = self.quality_feedback.session_manager

        # Get recent sessions
        sessions = session_manager.list_sessions(limit=100)

        if not sessions:
            return

        # Learn session-level patterns
        for session in sessions:
            stats = session.get_statistics()
            stats.get("mean_score", 0.0)
            context = session.context

            # Learn: sessions with context X perform better
            if context:
                query_type = f"context_{context}"
                # Use session score as proxy for all evaluations in session
                for eval_entry in session.evaluations:
                    schema = eval_entry.metadata.get("schema")
                    if schema:
                        self.query_type_to_schema[query_type][schema].append(eval_entry.score)

        # Learn: session sequences (session B after session A)
        if len(sessions) >= 2:
            for i in range(len(sessions) - 1):
                prev_session = sessions[i]
                next_session = sessions[i + 1]

                # Learn patterns in session transitions
                prev_score = prev_session.get_statistics().get("mean_score", 0.0)
                next_score = next_session.get_statistics().get("mean_score", 0.0)

                # If next session improves, learn from transition
                if next_score > prev_score:
                    # Context transition pattern
                    if prev_session.context and next_session.context:
                        transition_type = f"transition_{prev_session.context}_to_{next_session.context}"
                        for eval_entry in next_session.evaluations:
                            schema = eval_entry.metadata.get("schema")
                            if schema:
                                self.query_type_to_schema[transition_type][schema].append(eval_entry.score)

        # Learn: session-level quality trends
        if len(sessions) >= 3:
            recent_scores = [
                s.get_statistics().get("mean_score", 0.0)
                for s in sessions[-3:]
            ]
            trend = self._calculate_trend(recent_scores)

            # Use trend for predictions
            if trend == "improving":
                # Sessions are improving - can be more aggressive
                for session in sessions[-1:]:  # Most recent
                    for eval_entry in session.evaluations:
                        schema = eval_entry.metadata.get("schema")
                        if schema:
                            # Boost scores for improving trend
                            self.query_type_to_schema["trend_improving"][schema].append(eval_entry.score * 1.1)
            elif trend == "declining":
                # Sessions declining - use conservative approach
                for session in sessions[-1:]:
                    for eval_entry in session.evaluations:
                        schema = eval_entry.metadata.get("schema")
                        if schema:
                            self.query_type_to_schema["trend_declining"][schema].append(eval_entry.score * 0.9)

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend from score sequence."""
        if len(scores) < 2:
            return "stable"

        # Simple trend detection
        if scores[-1] > scores[0] + 0.1:
            return "improving"
        elif scores[-1] < scores[0] - 0.1:
            return "declining"
        else:
            return "stable"

    def estimate_reasoning_depth(
        self,
        query: str,
        query_type: Optional[str] = None,
    ) -> int:
        """
        Estimate minimum reasoning depth (number of subproblems) for query.

        ## Theoretical Foundation: Serial Scaling Hypothesis (SSH)

        The Serial Scaling Hypothesis (SSH) formalizes that certain problems require sequential
        computational depth that cannot be parallelized. Research shows that:
        1. Problems have minimum reasoning token thresholds
        2. Additional depth beyond the threshold provides diminishing returns
        3. Different query types require different minimum depths

        ## Why This Matters

        BOP uses schema-based decomposition (e.g., "decompose_and_synthesize") which breaks
        queries into subproblems. Without adaptive depth allocation:
        - Simple queries waste compute on unnecessary subproblems
        - Complex queries may not get enough depth for quality answers
        - Fixed depth (e.g., always 5 subproblems) is suboptimal

        ## Learning Approach

        We learn from historical performance: if queries of type X achieved high quality
        (score > 0.7) with N subproblems, then N is likely the minimum threshold for that
        query type. This aligns with SSH's insight that problems have minimum depth requirements.

        ## Implementation

        Based on learned patterns: queries that achieved high quality with N subproblems
        suggest N is the minimum threshold. We use:
        - Median of high-quality depths (score > 0.7) as the threshold
        - Fallback to minimum decent-quality depth (score > 0.6)
        - Default to 3 subproblems if no learning data

        Args:
            query: User query
            query_type: Optional pre-classified query type

        Returns:
            Estimated minimum reasoning depth (number of subproblems)
        """
        if query_type is None:
            query_type = self._classify_query(query)

        depth_data = self.query_type_to_depth.get(query_type, [])
        if not depth_data:
            # Default: use schema-based heuristic
            return 3  # Default decompose_and_synthesize uses 3-5

        # Find depth associated with high quality (score > 0.7)
        high_quality_depths = [depth for depth, score in depth_data if score > 0.7]
        if high_quality_depths:
            # Use median of high-quality depths as threshold
            return int(statistics.median(high_quality_depths))

        # Fallback: use minimum depth that achieved decent quality
        decent_depths = [depth for depth, score in depth_data if score > 0.6]
        if decent_depths:
            return min(decent_depths)

        return 3  # Default

    def should_early_stop(
        self,
        current_quality: float,
        query_type: str,
        num_subproblems_completed: int,
    ) -> bool:
        """
        Determine if reasoning should stop early (threshold met).

        ## Theoretical Foundation: SSH and Diminishing Returns

        SSH research shows that problems have minimum reasoning thresholds, but additional
        depth beyond the threshold provides diminishing returns. Test-time scaling research
        demonstrates that once quality reaches a certain level, more reasoning tokens don't
        significantly improve outcomes.

        ## Why Early Stopping Matters

        Without early stopping, BOP always completes all subproblems from decomposition,
        even when:
        - Quality threshold is already met
        - Additional subproblems won't improve quality
        - Compute is being wasted on unnecessary depth

        Early stopping optimizes the resource triple (depth-width-coordination) by avoiding
        unnecessary depth when quality is sufficient.

        ## Conservative Threshold

        We use 95% of the learned quality threshold to be conservative:
        - Prevents stopping too early (might miss important information)
        - Accounts for uncertainty in quality estimation
        - Balances efficiency with quality

        Returns True if:
        1. Current quality exceeds learned threshold for this query type
        2. Additional subproblems unlikely to improve quality significantly

        Args:
            current_quality: Current quality score (0-1)
            query_type: Query type classification
            num_subproblems_completed: Number of subproblems already completed

        Returns:
            True if should stop early, False otherwise
        """
        depth_data = self.query_type_to_depth.get(query_type, [])
        if not depth_data:
            return False  # No data, continue

        # Find quality threshold for this depth
        matching_depths = [
            (depth, score) for depth, score in depth_data
            if depth == num_subproblems_completed
        ]
        if not matching_depths:
            return False

        # If current quality exceeds learned threshold, can stop
        avg_threshold = statistics.mean([score for _, score in matching_depths])
        if current_quality >= avg_threshold * 0.95:  # 95% of threshold
            return True

        return False

    def _get_early_stop_threshold(self, query_type: str) -> Optional[float]:
        """
        Get early stop threshold for query type.

        Args:
            query_type: Query type classification

        Returns:
            Early stop threshold (0-1) or None if no data
        """
        depth_data = self.query_type_to_depth.get(query_type, [])
        if not depth_data:
            return None

        # Find average quality for minimum depth that achieved high quality
        high_quality_depths = [
            (depth, score) for depth, score in depth_data if score > 0.7
        ]
        if high_quality_depths:
            min_depth = min(depth for depth, _ in high_quality_depths)
            matching = [score for depth, score in high_quality_depths if depth == min_depth]
            if matching:
                return statistics.mean(matching) * 0.95  # 95% of threshold

        return None

    def _classify_query(self, query: str) -> str:
        """Classify query into a type for learning."""
        query_lower = query.lower()

        # Classification order matters - check more specific patterns first
        # Evaluative (most specific)
        if any(word in query_lower for word in ["analyze", "evaluate", "assess"]):
            return "evaluative"
        # Comparative
        elif any(word in query_lower for word in ["compare", "contrast", "difference", "versus", "vs"]):
            return "comparative"
        # Analytical (check "why" before "is" to avoid false matches)
        elif any(word in query_lower for word in ["why", "reason", "because"]):
            return "analytical"
        # Procedural
        elif any(word in query_lower for word in ["how", "explain", "process", "steps"]):
            return "procedural"
        # Factual (check "what" and "define" before "is" to be more specific)
        elif any(word in query_lower for word in ["what", "define", "who", "when", "where"]):
            return "factual"
        # Generic "is" questions (fallback)
        elif "is" in query_lower and len(query_lower.split()) <= 5:
            return "factual"
        else:
            return "general"

    def get_adaptive_strategy(
        self,
        query: str,
        current_session: Optional[Any] = None,
    ) -> AdaptiveStrategy:
        """
        Get adaptive strategy for a query based on learned patterns.

        Args:
            query: User query

        Returns:
            AdaptiveStrategy with recommendations
        """
        query_type = self._classify_query(query)

        # Find best schema for this query type
        schema_scores = self.query_type_to_schema.get(query_type, {})
        best_schema = None
        best_score = 0.0
        for schema, scores in schema_scores.items():
            if scores:
                avg_score = statistics.mean(scores)
                if avg_score > best_score:
                    best_score = avg_score
                    best_schema = schema

        # If no specific schema found, use overall best
        if not best_schema:
            best_schema = self.quality_feedback.get_best_schema_for_query(query)

        # Determine expected length
        length_data = self.query_type_to_length.get(query_type, [])
        expected_length = 200  # Default
        if length_data:
            # Find length associated with highest scores
            high_score_lengths = [length for length, score in length_data if score > 0.7]
            if high_score_lengths:
                expected_length = int(statistics.median(high_score_lengths))

        # Determine if research helps
        research_data = self.research_impact.get(query_type, [])
        should_use_research = False
        if research_data:
            with_research = [score for used, score in research_data if used]
            without_research = [score for used, score in research_data if not used]
            if with_research and without_research:
                avg_with = statistics.mean(with_research)
                avg_without = statistics.mean(without_research)
                should_use_research = avg_with > avg_without + 0.1  # 10% improvement threshold

        # Tool preferences (placeholder - would need tool tracking)
        tool_preferences = []

        # Calculate confidence
        confidence = 0.5  # Default
        if schema_scores and best_schema:
            scores = schema_scores[best_schema]
            if len(scores) >= 3:  # Need at least 3 samples
                confidence = min(1.0, len(scores) / 10.0)  # More samples = higher confidence

        # Enhance with session context if available
        if current_session:
            try:
                session_stats = current_session.get_statistics()
                session_score = session_stats.get("mean_score", 0.5)

                # Adjust strategy based on session performance
                if session_score < 0.5:
                    # Session struggling - use more conservative approach
                    confidence *= 0.8
                elif session_score > 0.8:
                    # Session doing well - can be more aggressive
                    confidence = min(1.0, confidence * 1.1)

                # Use session context for query type if available
                if current_session.context:
                    context_query_type = f"context_{current_session.context}"
                    context_schema_scores = self.query_type_to_schema.get(context_query_type, {})
                    if context_schema_scores:
                        # Prefer context-specific schema
                        for schema, scores in context_schema_scores.items():
                            if scores:
                                avg_score = statistics.mean(scores)
                                if avg_score > best_score:
                                    best_score = avg_score
                                    best_schema = schema
                                    confidence = min(1.0, len(scores) / 10.0)
            except Exception as e:
                logger.warning(f"Error using session context: {e}")

        # Estimate reasoning depth
        reasoning_depth = self.estimate_reasoning_depth(query, query_type)

        # Determine early stop threshold
        early_stop_threshold = self._get_early_stop_threshold(query_type)

        return AdaptiveStrategy(
            schema_selection=best_schema or "chain_of_thought",
            expected_length=expected_length,
            should_use_research=should_use_research,
            tool_preferences=tool_preferences,
            confidence=confidence,
            reasoning_depth=reasoning_depth,
            early_stop_threshold=early_stop_threshold,
        )

    def update_from_evaluation(
        self,
        query: str,
        schema: Optional[str],
        used_research: bool,
        response_length: int,
        quality_score: float,
        tools_used: Optional[List[str]] = None,
        num_subproblems: Optional[int] = None,
    ):
        """
        Update learning from a new evaluation.

        Args:
            query: The query
            schema: Schema used
            used_research: Whether research was used
            response_length: Length of response
            quality_score: Quality score from evaluation
            tools_used: Optional list of tools used
            num_subproblems: Optional number of subproblems used (for reasoning depth tracking)
        """
        query_type = self._classify_query(query)

        # Update schema performance
        if schema:
            self.query_type_to_schema[query_type][schema].append(quality_score)

        # Update length preferences
        self.query_type_to_length[query_type].append((response_length, quality_score))

        # Update research impact
        self.research_impact[query_type].append((used_research, quality_score))

        # Update tool performance
        if tools_used:
            for tool in tools_used:
                self.tool_performance[tool].append(quality_score)

        # NEW: Track reasoning depth
        if num_subproblems is not None:
            self.query_type_to_depth[query_type].append((num_subproblems, quality_score))
            # Keep only last 50 entries per query type
            if len(self.query_type_to_depth[query_type]) > 50:
                self.query_type_to_depth[query_type] = self.query_type_to_depth[query_type][-50:]

        # Auto-save learning data periodically (every 10 updates)
        if len(self.quality_feedback.history) % 10 == 0:
            self._save_learning()

    def get_improvement_suggestions(self, query: str, current_score: float) -> List[Dict[str, Any]]:
        """
        Get specific improvement suggestions based on learned patterns.

        Args:
            query: The query
            current_score: Current quality score

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        strategy = self.get_adaptive_strategy(query)
        query_type = self._classify_query(query)

        # Schema suggestion
        if strategy.schema_selection and strategy.confidence > 0.6:
            suggestions.append({
                "type": "schema",
                "message": f"For {query_type} queries, '{strategy.schema_selection}' performs best (confidence: {strategy.confidence:.2f})",
                "action": f"use_schema='{strategy.schema_selection}'",
                "expected_improvement": f"{strategy.confidence * 0.2:.2f}",
                "priority": "medium",
            })

        # Research suggestion
        if strategy.should_use_research:
            suggestions.append({
                "type": "research",
                "message": f"Research typically improves quality for {query_type} queries",
                "action": "use_research=True",
                "expected_improvement": "0.1-0.2",
                "priority": "low",
            })

        # Length suggestion
        if current_score < 0.6:
            length_data = self.query_type_to_length.get(query_type, [])
            if length_data:
                high_score_lengths = [length for length, score in length_data if score > 0.7]
                if high_score_lengths:
                    target_length = int(statistics.median(high_score_lengths))
                    suggestions.append({
                        "type": "length",
                        "message": f"High-quality {query_type} responses are typically {target_length} characters",
                        "action": f"Generate response of ~{target_length} characters",
                        "expected_improvement": "0.1-0.15",
                        "priority": "low",
                    })

        return suggestions

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights about system performance patterns."""
        insights = {
            "query_type_performance": {},
            "schema_recommendations": {},
            "research_effectiveness": {},
            "length_preferences": {},
        }

        # Query type performance
        for query_type, schema_scores in self.query_type_to_schema.items():
            all_scores = []
            for scores in schema_scores.values():
                all_scores.extend(scores)
            if all_scores:
                insights["query_type_performance"][query_type] = {
                    "mean": statistics.mean(all_scores),
                    "count": len(all_scores),
                }

        # Schema recommendations by query type
        for query_type, schema_scores in self.query_type_to_schema.items():
            best_schema = None
            best_score = 0.0
            for schema, scores in schema_scores.items():
                if scores:
                    avg = statistics.mean(scores)
                    if avg > best_score:
                        best_score = avg
                        best_schema = schema
            if best_schema:
                insights["schema_recommendations"][query_type] = {
                    "schema": best_schema,
                    "score": best_score,
                    "samples": len(schema_scores[best_schema]),
                }

        # Research effectiveness
        for query_type, research_data in self.research_impact.items():
            with_research = [score for used, score in research_data if used]
            without_research = [score for used, score in research_data if not used]
            if with_research and without_research:
                insights["research_effectiveness"][query_type] = {
                    "with_research": statistics.mean(with_research),
                    "without_research": statistics.mean(without_research),
                    "improvement": statistics.mean(with_research) - statistics.mean(without_research),
                }

        # Length preferences
        for query_type, length_data in self.query_type_to_length.items():
            if length_data:
                high_score_lengths = [length for length, score in length_data if score > 0.7]
                if high_score_lengths:
                    insights["length_preferences"][query_type] = {
                        "optimal_length": int(statistics.median(high_score_lengths)),
                        "range": (min(high_score_lengths), max(high_score_lengths)),
                    }

        return insights

    def save_learning(self, path: Optional[Path] = None):
        """
        Manually save learning data.

        Args:
            path: Optional custom path (uses learning_data_path if not provided)
        """
        if path:
            self.learning_data_path = path
        self._save_learning()

    def load_learning(self, path: Optional[Path] = None) -> bool:
        """
        Manually load learning data.

        Args:
            path: Optional custom path (uses learning_data_path if not provided)

        Returns:
            True if loaded successfully
        """
        if path:
            self.learning_data_path = path
        return self._load_learning()
