"""Experience replay mechanisms for session learning."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .session_manager import EvaluationEntry, HierarchicalSessionManager, Session

logger = logging.getLogger(__name__)


class SessionReplayManager:
    """
    Replay mechanisms for session learning.

    Supports:
    - Forward replay (chronological)
    - Reverse replay (outcome-to-start)
    - Prioritized replay (based on importance)
    - Reward backpropagation replay
    """

    def __init__(self, session_manager: HierarchicalSessionManager):
        self.session_manager = session_manager

    def forward_replay(
        self,
        session_id: str,
        callback: Callable[[EvaluationEntry], None],
    ):
        """Replay session evaluations in chronological order."""
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for forward replay")
            return

        for eval_entry in session.evaluations:
            callback(eval_entry)

    def reverse_replay(
        self,
        session_id: str,
        callback: Callable[[EvaluationEntry], None],
    ):
        """Replay session evaluations in reverse order."""
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for reverse replay")
            return

        for eval_entry in reversed(session.evaluations):
            callback(eval_entry)

    def prioritized_replay(
        self,
        session_ids: List[str],
        priority_fn: Callable[[Session, EvaluationEntry], float],
        callback: Callable[[EvaluationEntry], None],
    ):
        """Replay evaluations prioritized by importance."""
        # Collect all evaluations with priorities
        prioritized = []
        for sid in session_ids:
            session = self.session_manager.get_session(sid)
            if not session:
                continue
            for eval_entry in session.evaluations:
                priority = priority_fn(session, eval_entry)
                prioritized.append((priority, eval_entry, session))

        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: x[0], reverse=True)

        # Replay in priority order
        for _, eval_entry, session in prioritized:
            callback(eval_entry)

    def reward_backpropagation_replay(
        self,
        session_ids: List[str],
        callback: Callable[[EvaluationEntry], None],
        high_priority_threshold: float = 0.8,
        decay_factor: float = 0.5,
    ):
        """
        Replay with reward backpropagation priority.

        High priority for terminal/high-score evaluations, with priority
        propagating backward through the session.
        """
        def priority_fn(session: Session, eval_entry: EvaluationEntry) -> float:
            # High priority for high scores or non-error evaluations
            base_priority = 1.0
            if eval_entry.score > high_priority_threshold:
                base_priority = 10.0
            elif "error" not in eval_entry.quality_flags:
                base_priority = 5.0

            # Find position in session
            try:
                idx = session.evaluations.index(eval_entry)
                # Apply decay based on distance from end (reward backpropagation)
                distance_from_end = len(session.evaluations) - idx - 1
                priority = base_priority * (decay_factor ** distance_from_end)
            except ValueError:
                priority = base_priority

            return priority

        self.prioritized_replay(session_ids, priority_fn, callback)

    def replay_session_sequence(
        self,
        session_ids: List[str],
        callback: Callable[[Session, EvaluationEntry], None],
        forward: bool = True,
    ):
        """Replay a sequence of sessions in order."""
        sessions = [
            self.session_manager.get_session(sid)
            for sid in session_ids
        ]
        sessions = [s for s in sessions if s is not None]

        if not forward:
            sessions = list(reversed(sessions))

        for session in sessions:
            for eval_entry in session.evaluations:
                callback(session, eval_entry)


class AppendOnlySessionLog:
    """
    Append-only log for session updates with compaction.

    Provides efficient writes and can replay log for recovery.
    """

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = self.log_dir / "session_log.jsonl"
        self.compacted_log = self.log_dir / "session_log_compacted.jsonl"

    def append_evaluation(
        self,
        session_id: str,
        evaluation: EvaluationEntry,
    ):
        """Append evaluation to log."""
        entry = {
            "session_id": session_id,
            "evaluation": {
                "query": evaluation.query,
                "response": evaluation.response[:1000],  # Truncate
                "response_length": evaluation.response_length,
                "score": evaluation.score,
                "judgment_type": evaluation.judgment_type,
                "quality_flags": evaluation.quality_flags,
                "reasoning": evaluation.reasoning,
                "metadata": evaluation.metadata,
                "timestamp": evaluation.timestamp,
                "evaluation_id": evaluation.evaluation_id,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Append to log file
        with self.current_log.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def compact(self, active_session_ids: Optional[set] = None):
        """
        Compact log, keeping only entries for active sessions.

        Args:
            active_session_ids: Set of session IDs to keep. If None, keeps all.
        """
        if not self.current_log.exists():
            return

        # Read all entries
        entries = []
        with self.current_log.open() as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue  # Skip invalid lines

        # Filter entries
        if active_session_ids is not None:
            filtered_entries = [
                e for e in entries
                if e["session_id"] in active_session_ids
            ]
        else:
            # Keep all entries if no filter specified
            filtered_entries = entries

        # Write compacted log
        with self.compacted_log.open("w") as f:
            for entry in filtered_entries:
                f.write(json.dumps(entry) + "\n")

        # Replace current log with compacted
        if self.current_log.exists():
            self.current_log.unlink()
        self.compacted_log.rename(self.current_log)

        logger.info(f"Compacted log: {len(entries)} -> {len(filtered_entries)} entries")

    def replay(
        self,
        callback: Callable[[str, Dict[str, Any]], None],
        session_id: Optional[str] = None,
    ):
        """
        Replay log entries.

        Args:
            callback: Function to call for each entry (session_id, evaluation_data)
            session_id: Optional filter by session ID
        """
        log_file = self.current_log if self.current_log.exists() else self.compacted_log

        if not log_file.exists():
            return

        with log_file.open() as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if session_id is None or entry["session_id"] == session_id:
                        callback(entry["session_id"], entry["evaluation"])
                except json.JSONDecodeError:
                    continue  # Skip invalid lines

