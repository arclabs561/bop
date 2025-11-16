"""Track knowledge learned across sessions for temporal evolution."""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path
import json
import re
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class ConceptLearning:
    """Tracks when and how a concept was learned."""
    concept: str
    first_learned_at: str  # ISO timestamp
    last_updated_at: str  # ISO timestamp
    session_ids: List[str] = field(default_factory=list)  # Sessions where concept appeared
    query_count: int = 0  # Number of queries about this concept
    # Removed: response_count (never incremented), contexts (never used), confidence_scores (memory leak)
    # Keep only essential data to prevent memory leak
    recent_confidence: Optional[float] = None  # Most recent confidence (single value, not list)
    
    def add_occurrence(self, session_id: str, timestamp: str, confidence: Optional[float] = None):
        """Add a new occurrence of this concept."""
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)
        
        self.query_count += 1
        self.last_updated_at = timestamp
        
        # Store only most recent confidence to prevent memory leak
        if confidence is not None:
            self.recent_confidence = confidence


@dataclass
class SessionKnowledge:
    """Knowledge learned in a specific session."""
    session_id: str
    session_start: str
    session_end: Optional[str] = None
    concepts_learned: Set[str] = field(default_factory=set)
    concepts_refined: Set[str] = field(default_factory=set)  # Concepts that were already known
    query_count: int = 0  # Count only, not full queries (memory optimization)
    # Removed: queries (memory leak), key_insights (never populated), metadata (unused)


class KnowledgeTracker:
    """Tracks knowledge learned across sessions for temporal evolution."""
    
    # Common concept keywords for extraction
    CONCEPT_KEYWORDS = {
        "d-separation": ["d-separation", "d separation", "dsep", "conditional independence"],
        "trust": ["trust", "credibility", "confidence", "reliability"],
        "uncertainty": ["uncertainty", "epistemic", "aleatoric", "doubt"],
        "knowledge": ["knowledge", "information", "understanding", "comprehension"],
        "structure": ["structure", "organization", "architecture", "topology"],
        "causality": ["causality", "causal", "cause", "effect"],
        "information_geometry": ["information geometry", "fisher information", "statistical manifold"],
        "topology": ["topology", "clique", "graph", "network"],
        "reasoning": ["reasoning", "inference", "logic", "deduction"],
        "belief": ["belief", "prior", "evidence", "alignment"],
    }
    
    # Limits to prevent memory leak
    MAX_CONCEPTS = 1000  # Maximum concepts to track
    MAX_SESSIONS = 500   # Maximum sessions to track
    MAX_SESSION_IDS_PER_CONCEPT = 100  # Limit session_ids list size
    
    def __init__(self, persistence_path: Optional[Path] = None, auto_save_interval: int = 10):
        """
        Initialize knowledge tracker.
        
        Args:
            persistence_path: Optional path to save/load knowledge state
            auto_save_interval: Save after N queries (0 = disable auto-save)
        """
        # Concept -> ConceptLearning mapping
        self.concept_learning: Dict[str, ConceptLearning] = {}
        
        # Session ID -> SessionKnowledge mapping
        self.session_knowledge: Dict[str, SessionKnowledge] = {}
        
        # Persistence
        self.persistence_path = persistence_path
        self.auto_save_interval = auto_save_interval
        self.query_count_since_save = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Load existing state if available
        if self.persistence_path and self.persistence_path.exists():
            self._load_state()
    
    def extract_concepts(self, text: str) -> Set[str]:
        """
        Extract concepts from text using keyword matching.
        
        Note: This is a simple heuristic. For production, consider using
        embeddings or better NLP for semantic understanding.
        """
        if not text:
            return set()
        
        concepts = set()
        text_lower = text.lower()
        
        # Simple keyword matching (case-insensitive)
        for concept, keywords in self.CONCEPT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                concepts.add(concept)
        
        return concepts
    
    def track_query(
        self,
        session_id: str,
        query: str,
        response: str,
        timestamp: str,
        confidence: Optional[float] = None,
    ):
        """
        Track concepts learned from a query-response pair.
        
        Thread-safe and includes memory limits to prevent unbounded growth.
        """
        with self._lock:
            # Extract concepts from both query and response
            query_concepts = self.extract_concepts(query)
            response_concepts = self.extract_concepts(response)
            all_concepts = query_concepts | response_concepts
            
            if not all_concepts:
                # No concepts extracted - skip tracking to avoid empty entries
                return
            
            # Enforce session limit
            if len(self.session_knowledge) >= self.MAX_SESSIONS:
                # Remove oldest session (simple FIFO)
                oldest_session_id = min(
                    self.session_knowledge.keys(),
                    key=lambda sid: self.session_knowledge[sid].session_start
                )
                del self.session_knowledge[oldest_session_id]
            
            # Get or create session knowledge
            if session_id not in self.session_knowledge:
                self.session_knowledge[session_id] = SessionKnowledge(
                    session_id=session_id,
                    session_start=timestamp,
                )
            
            session_knowledge = self.session_knowledge[session_id]
            session_knowledge.query_count += 1
            session_knowledge.session_end = timestamp
            
            # Track each concept
            for concept in all_concepts:
                # Enforce concept limit
                if len(self.concept_learning) >= self.MAX_CONCEPTS:
                    # Remove least recently updated concept
                    oldest_concept = min(
                        self.concept_learning.keys(),
                        key=lambda c: self.concept_learning[c].last_updated_at
                    )
                    del self.concept_learning[oldest_concept]
                
                was_known = concept in self.concept_learning
                
                if concept not in self.concept_learning:
                    # New concept - first time learning
                    self.concept_learning[concept] = ConceptLearning(
                        concept=concept,
                        first_learned_at=timestamp,
                        last_updated_at=timestamp,
                    )
                    session_knowledge.concepts_learned.add(concept)
                else:
                    # Existing concept - refinement
                    session_knowledge.concepts_refined.add(concept)
                
                # Add occurrence
                learning = self.concept_learning[concept]
                learning.add_occurrence(
                    session_id=session_id,
                    timestamp=timestamp,
                    confidence=confidence,
                )
                
                # Enforce session_ids limit per concept
                if len(learning.session_ids) > self.MAX_SESSION_IDS_PER_CONCEPT:
                    # Keep most recent session_ids
                    learning.session_ids = learning.session_ids[-self.MAX_SESSION_IDS_PER_CONCEPT:]
            
            # Auto-save periodically
            self.query_count_since_save += 1
            if self.auto_save_interval > 0 and self.query_count_since_save >= self.auto_save_interval:
                self._save_state()
                self.query_count_since_save = 0
    
    def get_concept_evolution(self, concept: str) -> Optional[Dict[str, Any]]:
        """Get evolution of a specific concept across sessions."""
        with self._lock:
            if concept not in self.concept_learning:
                return None
            
            learning = self.concept_learning[concept]
            
            return {
                "concept": concept,
                "first_learned_at": learning.first_learned_at,
                "last_updated_at": learning.last_updated_at,
                "session_count": len(learning.session_ids),
                "query_count": learning.query_count,
                "recent_confidence": learning.recent_confidence,
                "sessions": learning.session_ids[:20],  # Limit for response size
            }
    
    def get_session_evolution(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge evolution for a specific session."""
        with self._lock:
            if session_id not in self.session_knowledge:
                return None
            
            session = self.session_knowledge[session_id]
            
            return {
                "session_id": session_id,
                "session_start": session.session_start,
                "session_end": session.session_end,
                "concepts_learned": list(session.concepts_learned),
                "concepts_refined": list(session.concepts_refined),
                "query_count": session.query_count,
            }
    
    def get_cross_session_evolution(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get evolution of concepts across all sessions."""
        with self._lock:
            # Cache sorted results to avoid recomputing
            if not hasattr(self, '_cached_evolution') or not hasattr(self, '_evolution_cache_time'):
                self._cached_evolution = None
                self._evolution_cache_time = None
            
            # Simple cache: recompute if concept_learning changed
            # (In production, could use hash of concept_learning to detect changes)
            evolution = []
            
            for concept, learning in sorted(
                self.concept_learning.items(),
                key=lambda x: x[1].last_updated_at,
                reverse=True
            )[:limit]:
                evolution.append({
                    "concept": concept,
                    "first_learned_at": learning.first_learned_at,
                    "last_updated_at": learning.last_updated_at,
                    "session_count": len(learning.session_ids),
                    "query_count": learning.query_count,
                    "recent_confidence": learning.recent_confidence,
                })
            
            return evolution
    
    def get_concepts_by_session(self, session_id: str) -> Dict[str, Any]:
        """Get all concepts that appeared in a session with their evolution."""
        with self._lock:
            if session_id not in self.session_knowledge:
                return {"concepts": [], "session_id": session_id}
            
            session = self.session_knowledge[session_id]
            all_concepts = session.concepts_learned | session.concepts_refined
            
            concepts_evolution = []
            for concept in all_concepts:
                if concept in self.concept_learning:
                    learning = self.concept_learning[concept]
                    concepts_evolution.append({
                        "concept": concept,
                        "first_learned_at": learning.first_learned_at,
                        "last_updated_at": learning.last_updated_at,
                        "was_new": concept in session.concepts_learned,
                        "was_refined": concept in session.concepts_refined,
                        "total_sessions": len(learning.session_ids),
                    })
            
            return {
                "session_id": session_id,
                "session_start": session.session_start,
                "concepts": concepts_evolution,
            }
    
    def _save_state(self) -> None:
        """Save knowledge tracker state to disk (atomic write)."""
        if not self.persistence_path:
            return
        
        try:
            temp_file = self.persistence_path.with_suffix('.json.tmp')
            data = {
                "concept_learning": {
                    concept: {
                        "concept": learning.concept,
                        "first_learned_at": learning.first_learned_at,
                        "last_updated_at": learning.last_updated_at,
                        "session_ids": learning.session_ids,
                        "query_count": learning.query_count,
                        "recent_confidence": learning.recent_confidence,
                    }
                    for concept, learning in self.concept_learning.items()
                },
                "session_knowledge": {
                    session_id: {
                        "session_id": session.session_id,
                        "session_start": session.session_start,
                        "session_end": session.session_end,
                        "concepts_learned": list(session.concepts_learned),
                        "concepts_refined": list(session.concepts_refined),
                        "query_count": session.query_count,
                    }
                    for session_id, session in self.session_knowledge.items()
                },
            }
            
            temp_file.write_text(json.dumps(data, indent=2))
            temp_file.replace(self.persistence_path)
            logger.debug(f"Saved knowledge tracker state to {self.persistence_path}")
        except Exception as e:
            logger.error(f"Failed to save knowledge tracker state: {e}")
    
    def _load_state(self) -> None:
        """Load knowledge tracker state from disk."""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            data = json.loads(self.persistence_path.read_text())
            
            # Load concept learning
            for concept, learning_data in data.get("concept_learning", {}).items():
                self.concept_learning[concept] = ConceptLearning(
                    concept=learning_data["concept"],
                    first_learned_at=learning_data["first_learned_at"],
                    last_updated_at=learning_data["last_updated_at"],
                    session_ids=learning_data.get("session_ids", []),
                    query_count=learning_data.get("query_count", 0),
                    recent_confidence=learning_data.get("recent_confidence"),
                )
            
            # Load session knowledge
            for session_id, session_data in data.get("session_knowledge", {}).items():
                self.session_knowledge[session_id] = SessionKnowledge(
                    session_id=session_data["session_id"],
                    session_start=session_data["session_start"],
                    session_end=session_data.get("session_end"),
                    concepts_learned=set(session_data.get("concepts_learned", [])),
                    concepts_refined=set(session_data.get("concepts_refined", [])),
                    query_count=session_data.get("query_count", 0),
                )
            
            logger.debug(f"Loaded knowledge tracker state from {self.persistence_path}")
        except Exception as e:
            logger.warning(f"Failed to load knowledge tracker state: {e}")
    
    def save(self, path: Optional[Path] = None) -> None:
        """Manually save state to disk."""
        if path:
            self.persistence_path = path
        self._save_state()
    
    def cleanup_old_data(self, max_age_days: int = 90) -> int:
        """
        Clean up old data beyond max_age_days.
        
        Returns number of concepts/sessions removed.
        """
        with self._lock:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
            removed = 0
            
            # Remove old concepts
            old_concepts = [
                concept for concept, learning in self.concept_learning.items()
                if learning.last_updated_at < cutoff
            ]
            for concept in old_concepts:
                del self.concept_learning[concept]
                removed += 1
            
            # Remove old sessions
            old_sessions = [
                session_id for session_id, session in self.session_knowledge.items()
                if session.session_end and session.session_end < cutoff
            ]
            for session_id in old_sessions:
                del self.session_knowledge[session_id]
                removed += 1
            
            if removed > 0:
                self._save_state()
            
            return removed

