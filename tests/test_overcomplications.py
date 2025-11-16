"""Tests to identify over-complications and unnecessary complexity."""

import pytest
from bop.knowledge_tracking import KnowledgeTracker
from bop.agent import KnowledgeAgent


def test_concept_extraction_overcomplicated():
    """OVERCOMPLICATION: Concept extraction uses regex for capitalized terms but doesn't help."""
    tracker = KnowledgeTracker()
    
    # The regex extraction of capitalized terms is overcomplicated
    # It extracts "D Separation" but then checks if it matches keywords
    # This is redundant - if it matches keywords, the keyword matching already found it
    
    text = "D-Separation is important"
    concepts = tracker.extract_concepts(text)
    
    # The regex finds "D-Separation" but keyword matching already found "d-separation"
    # So the regex step is unnecessary complexity


def test_session_knowledge_duplicates_concept_learning():
    """OVERCOMPLICATION: SessionKnowledge duplicates information already in ConceptLearning."""
    tracker = KnowledgeTracker()
    
    tracker.track_query(
        session_id="session1",
        query="What is trust?",
        response="Trust is...",
        timestamp="2025-01-01T00:00:00Z",
    )
    
    # SessionKnowledge stores concepts_learned and concepts_refined
    # But ConceptLearning already tracks which sessions a concept appeared in
    # This is duplicate information - could derive session concepts from ConceptLearning
    
    session = tracker.session_knowledge["session1"]
    learning = tracker.concept_learning.get("trust")
    
    if learning:
        # We can derive session concepts from learning.session_ids
        # So storing in SessionKnowledge is redundant
        pass


def test_cross_session_evolution_recomputes_every_time():
    """OVERCOMPLICATION: Cross-session evolution recomputes on every call."""
    tracker = KnowledgeTracker()
    
    # Track many concepts
    for i in range(100):
        tracker.track_query(
            session_id=f"session_{i}",
            query=f"Query about concept_{i}",
            response=f"Response",
            timestamp="2025-01-01T00:00:00Z",
        )
    
    # Every call to get_cross_session_evolution() sorts all concepts
    # This is O(n log n) every time
    # Should cache or only recompute when data changes
    
    evolution1 = tracker.get_cross_session_evolution()
    evolution2 = tracker.get_cross_session_evolution()  # Recomputes unnecessarily


def test_concept_learning_stores_unused_data():
    """OVERCOMPLICATION: ConceptLearning stores data that's never used."""
    tracker = KnowledgeTracker()
    
    tracker.track_query(
        session_id="session1",
        query="Query",
        response="Response",
        timestamp="2025-01-01T00:00:00Z",
        context="Context",
    )
    
    learning = tracker.concept_learning.get("trust")  # If trust extracted
    
    if learning:
        # contexts list is stored but never used in any query
        # response_count is stored but never incremented
        # This is dead data - overcomplicated storage


def test_agent_tracks_even_when_not_needed():
    """OVERCOMPLICATION: Agent tracks knowledge even when quality feedback disabled."""
    # Actually, agent only tracks if quality_feedback and session_manager exist
    # So this is fine
    
    # But what if user doesn't want session-level tracking?
    # No way to disable it - always tracks if sessions enabled
    # This is forced complexity
    pass


def test_knowledge_tracker_no_cleanup_mechanism():
    """OVERCOMPLICATION: No way to clean up old data."""
    tracker = KnowledgeTracker()
    
    # Track many old sessions
    for i in range(1000):
        tracker.track_query(
            session_id=f"old_session_{i}",
            query="Old query",
            response="Old response",
            timestamp="2020-01-01T00:00:00Z",  # Old timestamp
        )
    
    # All old data still in memory
    # No cleanup mechanism
    # No TTL (time-to-live)
    # No limits
    # This is overcomplicated because it accumulates forever


def test_response_count_field_unused():
    """BUG/OVERCOMPLICATION: response_count field exists but is never incremented."""
    tracker = KnowledgeTracker()
    
    tracker.track_query(
        session_id="session1",
        query="Query",
        response="Response",
        timestamp="2025-01-01T00:00:00Z",
    )
    
    learning = tracker.concept_learning.get("trust")
    
    if learning:
        # response_count is initialized to 0 but never incremented
        assert learning.response_count == 0  # Always 0!
        
        # This is either:
        # 1. A bug (should be incremented)
        # 2. Overcomplicated (field shouldn't exist if not used)


def test_concept_extraction_keyword_list_hardcoded():
    """OVERCOMPLICATION: Concept keywords are hardcoded - not extensible."""
    tracker = KnowledgeTracker()
    
    # CONCEPT_KEYWORDS is a class variable - hardcoded
    # Can't add new concepts without modifying code
    # Should be configurable or learnable
    
    # Also, the list is domain-specific to BOP's theoretical concepts
    # But what if user asks about "Python" or "machine learning"?
    # Won't be tracked - too narrow


def test_session_knowledge_key_insights_unused():
    """OVERCOMPLICATION: SessionKnowledge has key_insights field but it's never populated."""
    tracker = KnowledgeTracker()
    
    tracker.track_query(
        session_id="session1",
        query="Query",
        response="Response",
        timestamp="2025-01-01T00:00:00Z",
    )
    
    session = tracker.session_knowledge["session1"]
    
    # key_insights is always empty - never populated
    assert len(session.key_insights) == 0
    
    # This is dead code / overcomplicated field


def test_tracking_happens_even_with_empty_concepts():
    """OVERCOMPLICATION: Tracking happens even when no concepts extracted."""
    tracker = KnowledgeTracker()
    
    # Query with no extractable concepts
    tracker.track_query(
        session_id="session1",
        query="Hello, how are you?",
        response="I'm fine, thanks!",
        timestamp="2025-01-01T00:00:00Z",
    )
    
    # Still creates SessionKnowledge entry even though no concepts
    # This is unnecessary overhead

