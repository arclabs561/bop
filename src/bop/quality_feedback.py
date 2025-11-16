"""Quality feedback loop that uses semantic evaluation to improve responses."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json
from pathlib import Path
import logging

from .semantic_eval import SemanticEvaluator, SemanticJudgment

logger = logging.getLogger(__name__)


@dataclass
class QualityInsights:
    """Insights derived from semantic evaluations."""
    
    overall_score: float
    quality_issues: List[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    schema_performance: Dict[str, float] = field(default_factory=dict)
    query_type_performance: Dict[str, float] = field(default_factory=dict)
    common_failures: List[str] = field(default_factory=list)


class QualityFeedbackLoop:
    """
    Feedback loop that uses semantic evaluation to improve system behavior.
    
    Integrates evaluation results into the system to:
    - Adjust response generation based on quality insights
    - Suggest schema selection based on performance
    - Identify and fix common quality issues
    - Track improvements over time
    """
    
    def __init__(
        self,
        evaluation_history_path: Optional[Path] = None,
        use_sessions: bool = True,
        session_context: Optional[str] = None,
    ):
        """
        Initialize quality feedback loop.
        
        Args:
            evaluation_history_path: Path to store evaluation history
            use_sessions: Whether to use hierarchical session management
            session_context: Optional context for the current session
        """
        self.evaluation_history_path = evaluation_history_path or Path("data/results/quality_history.json")
        self.evaluator = SemanticEvaluator()
        self.history: List[Dict[str, Any]] = []
        
        # Session management (lazy import to avoid circular dependency)
        self.use_sessions = use_sessions
        if self.use_sessions:
            from .session_manager import HierarchicalSessionManager
            from .unified_storage import UnifiedSessionStorage
            
            sessions_dir = self.evaluation_history_path.parent / "sessions"
            self.session_manager = HierarchicalSessionManager(
                sessions_dir=sessions_dir,
                auto_group_by="day",  # Group sessions by day
                enable_buffering=True,  # Enable write buffering
                enable_indexing=True,  # Enable indexing
            )
            if session_context:
                self.session_manager.create_session(context=session_context)
            
            # Unified storage: sessions are primary, history is derived
            self.unified_storage = UnifiedSessionStorage(self.session_manager)
        else:
            self.session_manager = None
            self.unified_storage = None
        
        # Performance tracking (initialize before loading history)
        self.schema_scores: Dict[str, List[float]] = defaultdict(list)
        self.query_type_scores: Dict[str, List[float]] = defaultdict(list)
        self.quality_issue_counts = Counter()
        
        # Load history (derived from sessions if using unified storage)
        self._load_history()
        
    def _load_history(self):
        """Load evaluation history from disk or derive from sessions."""
        if self.use_sessions and self.unified_storage:
            # Derive history from sessions (single source of truth)
            self.history = self.unified_storage.get_history_view(limit=1000)
        elif self.evaluation_history_path.exists():
            # Fallback: load from flat history file
            try:
                data = json.loads(self.evaluation_history_path.read_text())
                self.history = data.get("history", [])
            except Exception:
                self.history = []
        
        # Rebuild performance tracking from history
        for entry in self.history:
            schema = entry.get("metadata", {}).get("schema")
            query_type = entry.get("metadata", {}).get("query_type")
            if schema:
                self.schema_scores[schema].append(entry.get("score", 0))
            if query_type:
                self.query_type_scores[query_type].append(entry.get("score", 0))
            for flag in entry.get("quality_flags", []):
                self.quality_issue_counts[flag] += 1
    
    def _save_history(self):
        """Save evaluation history to disk (only if not using unified storage)."""
        if self.use_sessions and self.unified_storage:
            # History is derived from sessions, no need to save separately
            # Could save a snapshot for quick access if needed
            return
        
        # Fallback: save flat history file
        data = {
            "history": self.history[-1000:],  # Keep last 1000 evaluations
            "summary": self.get_performance_summary(),
        }
        self.evaluation_history_path.parent.mkdir(parents=True, exist_ok=True)
        self.evaluation_history_path.write_text(json.dumps(data, indent=2))
    
    def evaluate_and_learn(
        self,
        query: str,
        response: str,
        schema: Optional[str] = None,
        research: bool = False,
        expected_concepts: Optional[List[str]] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a response and learn from it to improve future responses.
        
        Returns evaluation result with improvement suggestions.
        """
        # Evaluate relevance (always applicable)
        # Include validation issues in metadata for semantic evaluator
        eval_metadata = {
            "schema": schema,
            "research": research,
        }
        if metadata and "validation_issues" in metadata:
            eval_metadata["validation_issues"] = metadata["validation_issues"]
        
        relevance_judgment = self.evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata=eval_metadata,
        )
        
        # Evaluate accuracy if concepts provided
        accuracy_judgment = None
        if expected_concepts:
            accuracy_judgment = self.evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=expected_concepts,
                metadata={
                    "schema": schema,
                    "research": research,
                },
            )
        
        # Evaluate completeness if context provided
        completeness_judgment = None
        if context:
            completeness_judgment = self.evaluator.evaluate_completeness(
                query=query,
                response=response,
                content_context=context,
                metadata={
                    "schema": schema,
                    "research": research,
                },
            )
        
        # Store in history
        judgments = [relevance_judgment]
        if accuracy_judgment:
            judgments.append(accuracy_judgment)
        if completeness_judgment:
            judgments.append(completeness_judgment)
        
        for judgment in judgments:
            # Add to session (primary storage)
            if self.session_manager:
                self.session_manager.add_evaluation(
                    query=query,
                    response=response,
                    response_length=len(response),
                    score=judgment.score,
                    judgment_type=judgment.judgment_type,
                    quality_flags=judgment.quality_flags,
                    reasoning=judgment.reasoning,
                    metadata=judgment.metadata,
                )
            
            # Update performance tracking
            if schema:
                self.schema_scores[schema].append(judgment.score)
            query_type = judgment.query_characteristics.get("complexity") if judgment.query_characteristics else None
            if query_type:
                self.query_type_scores[query_type].append(judgment.score)
            for flag in judgment.quality_flags:
                self.quality_issue_counts[flag] += 1
        
        # Refresh history from sessions (if using unified storage)
        if self.use_sessions and self.unified_storage:
            self.history = self.unified_storage.get_history_view(limit=1000)
        else:
            # Fallback: add to flat history
            for judgment in judgments:
                entry = {
                    "query": query,
                    "response": response[:1000],
                    "response_length": len(response),
                    "score": judgment.score,
                    "judgment_type": judgment.judgment_type,
                    "quality_flags": judgment.quality_flags,
                    "reasoning": judgment.reasoning,
                    "metadata": judgment.metadata,
                    "timestamp": judgment.timestamp,
                }
                self.history.append(entry)
        
        self._save_history()
        
        # Flush buffer if using sessions
        if self.session_manager and hasattr(self.session_manager, 'flush_buffer'):
            self.session_manager.flush_buffer()
        
        # Generate insights and suggestions
        insights = self._generate_insights(relevance_judgment, accuracy_judgment, completeness_judgment)
        suggestions = self._generate_suggestions(insights, query, schema)
        
        return {
            "relevance": relevance_judgment.score,
            "accuracy": accuracy_judgment.score if accuracy_judgment else None,
            "completeness": completeness_judgment.score if completeness_judgment else None,
            "quality_flags": relevance_judgment.quality_flags,
            "insights": insights,
            "suggestions": suggestions,
            "judgments": {
                "relevance": relevance_judgment,
                "accuracy": accuracy_judgment,
                "completeness": completeness_judgment,
            },
        }
    
    def _generate_insights(
        self,
        relevance: SemanticJudgment,
        accuracy: Optional[SemanticJudgment],
        completeness: Optional[SemanticJudgment],
    ) -> QualityInsights:
        """Generate insights from judgments."""
        scores = [relevance.score]
        if accuracy:
            scores.append(accuracy.score)
        if completeness:
            scores.append(completeness.score)
        
        overall_score = sum(scores) / len(scores)
        
        # Collect quality issues
        quality_issues = list(set(relevance.quality_flags))
        if accuracy:
            quality_issues.extend(accuracy.quality_flags)
        if completeness:
            quality_issues.extend(completeness.quality_flags)
        quality_issues = list(set(quality_issues))
        
        # Identify strengths
        strengths = []
        if relevance.score > 0.7:
            strengths.append("Good relevance to query")
        if accuracy and accuracy.score > 0.7:
            strengths.append("Accurate concept coverage")
        if completeness and completeness.score > 0.7:
            strengths.append("Complete response")
        if not quality_issues:
            strengths.append("No quality issues detected")
        
        # Identify weaknesses
        weaknesses = []
        if relevance.score < 0.5:
            weaknesses.append("Low relevance to query")
        if accuracy and accuracy.score < 0.5:
            weaknesses.append("Missing expected concepts")
        if completeness and completeness.score < 0.5:
            weaknesses.append("Incomplete coverage")
        if "placeholder" in quality_issues:
            weaknesses.append("Placeholder response (LLM service may not be configured)")
        if "error" in quality_issues:
            weaknesses.append("Error in response generation")
        if "too_short" in quality_issues:
            weaknesses.append("Response too short for query complexity")
        
        # Generate recommendations
        recommendations = []
        if "placeholder" in quality_issues:
            recommendations.append("Configure LLM service (set OPENAI_API_KEY)")
        if "error" in quality_issues:
            recommendations.append("Check system configuration and error handling")
        if relevance.score < 0.5:
            recommendations.append("Improve query-response relevance")
        if accuracy and accuracy.score < 0.5:
            recommendations.append("Ensure response includes expected concepts")
        if completeness and completeness.score < 0.5:
            recommendations.append("Expand response to cover more context")
        
        # Schema performance
        schema_performance = {}
        for schema, scores_list in self.schema_scores.items():
            if scores_list:
                schema_performance[schema] = sum(scores_list) / len(scores_list)
        
        # Query type performance
        query_type_performance = {}
        for q_type, scores_list in self.query_type_scores.items():
            if scores_list:
                query_type_performance[q_type] = sum(scores_list) / len(scores_list)
        
        # Common failures
        common_failures = [
            flag for flag, count in self.quality_issue_counts.most_common(3)
        ]
        
        return QualityInsights(
            overall_score=overall_score,
            quality_issues=quality_issues,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            schema_performance=schema_performance,
            query_type_performance=query_type_performance,
            common_failures=common_failures,
        )
    
    def _generate_suggestions(
        self,
        insights: QualityInsights,
        query: str,
        current_schema: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Generate actionable suggestions for improvement."""
        suggestions = []
        
        # Schema suggestion
        if insights.schema_performance and current_schema:
            # Find best performing schema
            best_schema = max(
                insights.schema_performance.items(),
                key=lambda x: x[1]
            )[0]
            
            if best_schema != current_schema and insights.schema_performance[best_schema] > insights.schema_performance.get(current_schema, 0) + 0.1:
                suggestions.append({
                    "type": "schema_selection",
                    "message": f"Consider using '{best_schema}' schema (performs {insights.schema_performance[best_schema]:.2f} vs {insights.schema_performance.get(current_schema, 0):.2f})",
                    "action": f"use_schema='{best_schema}'",
                    "priority": "medium",
                })
        
        # Quality issue suggestions
        if "placeholder" in insights.quality_issues:
            suggestions.append({
                "type": "configuration",
                "message": "LLM service not configured - responses are placeholders",
                "action": "Set OPENAI_API_KEY environment variable",
                "priority": "high",
            })
        
        if "too_short" in insights.quality_issues:
            suggestions.append({
                "type": "response_length",
                "message": "Response too short for query complexity",
                "action": "Generate longer, more detailed response",
                "priority": "medium",
            })
        
        # Query type specific suggestions
        query_chars = self.evaluator._analyze_query_characteristics(query)
        if query_chars.get("is_multi_part") and insights.overall_score < 0.6:
            suggestions.append({
                "type": "query_handling",
                "message": "Multi-part query may need decomposition",
                "action": "Consider using 'decompose_and_synthesize' schema",
                "priority": "low",
            })
        
        if query_chars.get("is_procedural") and insights.overall_score < 0.6:
            suggestions.append({
                "type": "query_handling",
                "message": "Procedural query may need step-by-step structure",
                "action": "Ensure response includes procedural indicators (step, first, then, etc.)",
                "priority": "low",
            })
        
        return suggestions
    
    def get_best_schema_for_query(self, query: str) -> Optional[str]:
        """
        Suggest best schema based on historical performance for similar queries.
        
        Returns:
            Schema name or None if no data available
        """
        if not self.schema_scores:
            return None
        
        # Find schema with highest average score
        schema_avgs = {
            schema: sum(scores) / len(scores)
            for schema, scores in self.schema_scores.items()
            if scores
        }
        
        if not schema_avgs:
            return None
        
        return max(schema_avgs.items(), key=lambda x: x[1])[0]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance over time."""
        if not self.history:
            return {"error": "No evaluation history"}
        
        recent_scores = [e["score"] for e in self.history[-50:]]
        
        return {
            "total_evaluations": len(self.history),
            "recent_mean_score": sum(recent_scores) / len(recent_scores) if recent_scores else 0,
            "schema_performance": {
                schema: sum(scores) / len(scores)
                for schema, scores in self.schema_scores.items()
                if scores
            },
            "quality_issue_frequency": dict(self.quality_issue_counts.most_common(5)),
            "trend": "improving" if len(recent_scores) >= 10 and recent_scores[-10:] > recent_scores[:10] else "stable",
        }
    
    def should_retry_with_different_schema(
        self,
        query: str,
        current_schema: Optional[str],
        score: float,
    ) -> bool:
        """
        Determine if response should be retried with different schema.
        
        Returns:
            True if retry recommended
        """
        if score > 0.6:
            return False  # Good enough
        
        if not current_schema:
            return True  # No schema used, try one
        
        # Check if better schema available
        best_schema = self.get_best_schema_for_query(query)
        if best_schema and best_schema != current_schema:
            best_score = sum(self.schema_scores[best_schema]) / len(self.schema_scores[best_schema])
            if best_score > score + 0.15:  # At least 15% better
                return True
        
        return False

