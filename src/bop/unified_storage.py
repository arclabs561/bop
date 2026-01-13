"""Unified storage where sessions are primary, history is derived."""

import logging
from typing import Any, Dict, List, Optional

from .session_manager import HierarchicalSessionManager

logger = logging.getLogger(__name__)


class UnifiedSessionStorage:
    """
    Storage where sessions are primary, history is derived.

    Eliminates data duplication by making sessions the single source of truth
    and deriving flat history views on demand.
    """

    def __init__(self, session_manager: HierarchicalSessionManager):
        self.session_manager = session_manager

    def get_history_view(
        self,
        limit: int = 1000,
        session_ids: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Derive flat history from sessions.

        Args:
            limit: Maximum number of entries to return
            session_ids: Optional list of session IDs to include
            date_from: Optional start date (ISO format)
            date_to: Optional end date (ISO format)

        Returns:
            List of history entries (flat format)
        """
        if session_ids is None:
            # Get recent sessions
            sessions = self.session_manager.list_sessions(limit=limit)
        else:
            sessions = [
                self.session_manager.get_session(sid)
                for sid in session_ids
            ]
            sessions = [s for s in sessions if s is not None]

        # Flatten evaluations from sessions
        history = []
        for session in sessions:
            # Filter by date if specified
            if date_from:
                session_date = session.created_at
                if session_date < date_from:
                    continue
            if date_to:
                session_date = session.created_at
                if session_date > date_to:
                    continue

            for eval_entry in session.evaluations:
                history.append({
                    "query": eval_entry.query,
                    "response": eval_entry.response,
                    "response_length": eval_entry.response_length,
                    "score": eval_entry.score,
                    "judgment_type": eval_entry.judgment_type,
                    "quality_flags": eval_entry.quality_flags,
                    "reasoning": eval_entry.reasoning,
                    "metadata": {
                        **eval_entry.metadata,
                        "session_id": session.session_id,
                        "session_context": session.context,
                        "session_status": session.status,
                    },
                    "timestamp": eval_entry.timestamp,
                })

        # Sort by timestamp, limit
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]

    def get_history_summary(self) -> Dict[str, Any]:
        """Get summary statistics from history view."""
        history = self.get_history_view(limit=10000)  # Get larger sample

        if not history:
            return {
                "total_entries": 0,
                "mean_score": 0.0,
                "sessions_represented": 0,
            }

        scores = [e["score"] for e in history]
        session_ids = set(e["metadata"].get("session_id") for e in history)

        return {
            "total_entries": len(history),
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "sessions_represented": len(session_ids),
            "date_range": {
                "earliest": min(e["timestamp"] for e in history),
                "latest": max(e["timestamp"] for e in history),
            },
        }

