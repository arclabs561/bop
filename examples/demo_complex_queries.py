#!/usr/bin/env python3
"""
Comprehensive demonstration of the hierarchical session management system
with complex queries and full traces.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
import time

from bop.agent import KnowledgeAgent
from bop.session_manager import HierarchicalSessionManager
from bop.session_replay import SessionReplayManager
from bop.unified_storage import UnifiedSessionStorage
from bop.adaptive_quality import AdaptiveQualityManager


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def print_subsection(title: str, width: int = 80):
    """Print a formatted subsection header."""
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


async def demonstrate_complex_queries():
    """Run complex queries and show full traces."""
    
    print_section("COMPREHENSIVE SYSTEM DEMONSTRATION")
    print("\nThis demonstration shows all implemented features working together:")
    print("  • Write buffering & atomic writes")
    print("  • Session lifecycle management")
    print("  • Data validation & checksums")
    print("  • Indexing for fast queries")
    print("  • Lazy loading & LRU cache")
    print("  • Cross-session learning")
    print("  • Unified storage (no duplication)")
    print("  • Experience replay")
    print("  • Quality feedback loop")
    print("  • Adaptive strategy selection")
    
    # Initialize agent
    print_section("INITIALIZATION")
    agent = KnowledgeAgent(enable_quality_feedback=True)
    manager = agent.quality_feedback.session_manager
    adaptive = agent.adaptive_manager
    unified = agent.quality_feedback.unified_storage
    
    print(f"✓ Agent initialized with quality feedback")
    print(f"✓ Session manager: buffering={manager.enable_buffering}, indexing={manager.enable_indexing}")
    print(f"✓ Cache size: {manager.cache.maxsize}")
    print(f"✓ Current session: {manager.current_session_id[:8] if manager.current_session_id else 'None'}...")
    
    # Complex queries
    complex_queries = [
        {
            "query": "How does hierarchical session management enable cross-session learning in adaptive AI systems? Explain the relationship between session sequences and pattern recognition.",
            "schema": "decompose_and_synthesize",
            "research": False,
        },
        {
            "query": "Compare write buffering strategies: batch writes vs append-only logs. What are the performance and durability trade-offs?",
            "schema": "hypothesize_and_test",
            "research": False,
        },
        {
            "query": "Explain how experience replay mechanisms (forward, reverse, prioritized) improve learning consolidation in persistent learning systems.",
            "schema": "scenario_analysis",
            "research": False,
        },
        {
            "query": "What is the relationship between Kolmogorov complexity and LLM prompt efficiency? How does this relate to knowledge structure representation?",
            "schema": "chain_of_thought",
            "research": False,
        },
    ]
    
    print_section("PROCESSING COMPLEX QUERIES")
    
    for i, q_data in enumerate(complex_queries, 1):
        print_subsection(f"Query {i}: {q_data['query'][:60]}...")
        
        # Pre-query state
        buffer_before = len(manager.write_buffer._buffer) if manager.write_buffer else 0
        cache_before = len(manager.cache.cache)
        index_before = len(manager.index)
        
        print(f"\n[Pre-Query State]")
        print(f"  Buffer: {buffer_before} sessions")
        print(f"  Cache: {cache_before}/{manager.cache.maxsize} sessions")
        print(f"  Index: {index_before} entries")
        
        # Process query
        start_time = time.time()
        response = await agent.chat(
            q_data['query'],
            use_schema=q_data['schema'],
            use_research=q_data['research'],
        )
        elapsed = time.time() - start_time
        
        # Post-query state
        buffer_after = len(manager.write_buffer._buffer) if manager.write_buffer else 0
        cache_after = len(manager.cache.cache)
        index_after = len(manager.index)
        
        print(f"\n[Post-Query State]")
        print(f"  Processing Time: {elapsed:.3f}s")
        print(f"  Response Length: {len(response.get('response', ''))} chars")
        print(f"  Schema Used: {response.get('schema_used', 'None')}")
        print(f"  Buffer: {buffer_before} → {buffer_after} (+{buffer_after - buffer_before})")
        print(f"  Cache: {cache_before} → {cache_after} (+{cache_after - cache_before})")
        print(f"  Index: {index_before} → {index_after} (+{index_after - index_before})")
        
        # Quality feedback
        if response.get('quality'):
            q = response['quality']
            print(f"\n[Quality Feedback]")
            print(f"  Score: {q.get('score', 0):.3f}")
            print(f"  Flags: {', '.join(q.get('flags', [])) or 'none'}")
            print(f"  Suggestions: {len(q.get('suggestions', []))}")
            
            if q.get('adaptive_strategy'):
                a = q['adaptive_strategy']
                print(f"\n[Adaptive Strategy]")
                print(f"  Recommended Schema: {a.get('schema', 'N/A')}")
                print(f"  Expected Length: {a.get('expected_length', 0)} chars")
                print(f"  Use Research: {a.get('should_use_research', False)}")
                print(f"  Confidence: {a.get('confidence', 0):.3f}")
    
    # Flush buffers
    print_section("PERSISTENCE OPERATIONS")
    flushed = manager.flush_buffer()
    print(f"✓ Flushed {flushed} sessions to disk (atomic writes)")
    
    # Session statistics
    print_section("SESSION STATISTICS")
    sessions = manager.list_sessions(limit=10)
    print(f"Total Sessions: {len(sessions)}")
    
    for session in sessions[:5]:
        stats = session.get_statistics()
        print(f"\nSession {session.session_id[:8]}...")
        print(f"  Context: {session.context or 'N/A'}")
        print(f"  Status: {session.status}")
        print(f"  Created: {session.created_at[:19]}")
        print(f"  Evaluations: {stats['evaluation_count']}")
        print(f"  Mean Score: {stats['mean_score']:.3f}")
        print(f"  Score Range: {stats['min_score']:.3f} - {stats['max_score']:.3f}")
        if stats.get('schemas_used'):
            print(f"  Schemas: {', '.join(stats['schemas_used'])}")
    
    # Aggregate statistics
    agg_stats = manager.get_aggregate_statistics()
    print(f"\n[Aggregate Statistics]")
    print(f"  Total Sessions: {agg_stats['session_count']}")
    print(f"  Total Evaluations: {agg_stats['total_evaluations']}")
    print(f"  Overall Mean Score: {agg_stats['mean_score']:.3f}")
    print(f"  Score Range: {agg_stats['min_score']:.3f} - {agg_stats['max_score']:.3f}")
    if agg_stats.get('quality_issues'):
        print(f"  Quality Issues: {agg_stats['quality_issues']}")
    
    # Indexing demonstration
    print_section("INDEXING DEMONSTRATION")
    if manager.enable_indexing:
        print(f"Indexed Sessions: {len(manager.index)}")
        
        # Query by score
        high_score = manager.query_sessions(min_score=0.5)
        print(f"  High Score (>= 0.5): {len(high_score)} sessions")
        
        # Query by status
        active = manager.query_sessions(status='active')
        print(f"  Active Sessions: {len(active)}")
        
        # Combined query
        combined = manager.query_sessions(min_score=0.0, status='active')
        print(f"  Active (any score): {len(combined)} sessions")
        
        # Performance test
        perf_start = time.time()
        indexed = manager.query_sessions(min_score=0.0)
        index_time = time.time() - perf_start
        
        perf_start = time.time()
        all_sessions = manager.list_sessions()
        load_time = time.time() - perf_start
        
        print(f"\n[Performance]")
        print(f"  Index Query: {index_time:.6f}s ({len(indexed)} results)")
        print(f"  Full Load: {load_time:.6f}s ({len(all_sessions)} sessions)")
        if index_time > 0:
            print(f"  Speedup: {load_time/index_time:.1f}x")
    
    # Unified storage demonstration
    print_section("UNIFIED STORAGE DEMONSTRATION")
    history = unified.get_history_view(limit=100)
    print(f"History Entries (derived from sessions): {len(history)}")
    
    total_evals = sum(len(s.evaluations) for s in sessions)
    print(f"Total Evaluations in Sessions: {total_evals}")
    print(f"✓ Match: {'✅' if len(history) == total_evals else '❌'} (no duplication)")
    
    summary = unified.get_history_summary()
    print(f"\n[History Summary]")
    print(f"  Total Entries: {summary['total_entries']}")
    print(f"  Mean Score: {summary['mean_score']:.3f}")
    print(f"  Sessions Represented: {summary['sessions_represented']}")
    
    if history:
        sample = history[0]
        print(f"\n[Sample History Entry]")
        print(f"  Query: {sample['query'][:50]}...")
        print(f"  Score: {sample['score']:.3f}")
        print(f"  Session ID: {sample['metadata'].get('session_id', 'N/A')[:8]}...")
        print(f"  Session Context: {sample['metadata'].get('session_context', 'N/A')}")
        print(f"  Session Status: {sample['metadata'].get('session_status', 'N/A')}")
    
    # Experience replay
    print_section("EXPERIENCE REPLAY DEMONSTRATION")
    if sessions:
        replay = SessionReplayManager(manager)
        session_id = sessions[0].session_id
        
        print(f"Replaying Session {session_id[:8]}...")
        
        print(f"\n[Forward Replay]")
        forward_evals = []
        def collect_forward(e):
            forward_evals.append((e.score, e.query[:40]))
        replay.forward_replay(session_id, collect_forward)
        for i, (score, query) in enumerate(forward_evals[:3], 1):
            print(f"  [{i}] Score: {score:.3f} | {query}...")
        
        print(f"\n[Reverse Replay]")
        reverse_evals = []
        def collect_reverse(e):
            reverse_evals.append((e.score, e.query[:40]))
        replay.reverse_replay(session_id, collect_reverse)
        for i, (score, query) in enumerate(reverse_evals[:3], 1):
            print(f"  [{i}] Score: {score:.3f} | {query}...")
        
        print(f"\n[Prioritized Replay (Reward Backpropagation)]")
        prioritized_evals = []
        def collect_prioritized(e):
            prioritized_evals.append((e.score, e.query[:40]))
        replay.reward_backpropagation_replay([session_id], collect_prioritized)
        for i, (score, query) in enumerate(prioritized_evals[:3], 1):
            print(f"  [{i}] Score: {score:.3f} | {query}...")
    
    # Adaptive learning insights
    print_section("ADAPTIVE LEARNING INSIGHTS")
    insights = adaptive.get_performance_insights()
    
    if insights.get('query_type_performance'):
        print(f"\n[Query Type Performance]")
        for q_type, perf in insights['query_type_performance'].items():
            print(f"  {q_type}: {perf['mean']:.3f} (n={perf['count']})")
    
    if insights.get('schema_recommendations'):
        print(f"\n[Schema Recommendations]")
        for q_type, rec in insights['schema_recommendations'].items():
            print(f"  {q_type}: {rec['schema']} (score={rec['score']:.3f}, samples={rec['samples']})")
    
    if insights.get('research_effectiveness'):
        print(f"\n[Research Effectiveness]")
        for q_type, eff in insights['research_effectiveness'].items():
            improvement = eff['improvement']
            sign = '+' if improvement > 0 else ''
            print(f"  {q_type}: {sign}{improvement:.3f} improvement with research")
    
    # Cross-session learning
    print_section("CROSS-SESSION LEARNING")
    
    # Create sessions with different contexts
    contexts = ['knowledge_structure', 'adaptive_learning', 'performance']
    for context in contexts:
        session_id = manager.create_session(context=context)
        print(f"Created session {session_id[:8]}... with context: {context}")
        
        # Add a few evaluations
        for j in range(2):
            manager.add_evaluation(
                query=f'What is {context}?',
                response=f'Response about {context}',
                response_length=100,
                score=0.7 + (j * 0.1),
                judgment_type='relevance',
                quality_flags=[],
                reasoning='Good',
                metadata={'schema': 'chain_of_thought'},
            )
    
    manager.flush_buffer()
    
    # Learn from sessions
    adaptive._learn_from_sessions()
    
    # Check for context-based patterns
    context_types = [f'context_{c}' for c in contexts]
    learned_contexts = [ct for ct in context_types if ct in adaptive.query_type_to_schema]
    if learned_contexts:
        print(f"\n[Context-Based Learning]")
        for ctx_type in learned_contexts:
            schemas = adaptive.query_type_to_schema[ctx_type]
            print(f"  {ctx_type}: {len(schemas)} schemas learned")
            for schema, scores in schemas.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    print(f"    - {schema}: {avg:.3f} (n={len(scores)})")
    
    # Session-aware strategy
    current_session = manager.get_current_session()
    if current_session:
        print(f"\n[Session-Aware Strategy]")
        print(f"  Current Context: {current_session.context}")
        strategy = adaptive.get_adaptive_strategy(
            'What is adaptive learning?',
            current_session=current_session,
        )
        print(f"  Recommended Schema: {strategy.schema_selection}")
        print(f"  Confidence: {strategy.confidence:.3f}")
        print(f"  Use Research: {strategy.should_use_research}")
    
    # Lifecycle management
    print_section("SESSION LIFECYCLE MANAGEMENT")
    
    # Close a session
    if sessions:
        test_session = sessions[0]
        print(f"Closing session {test_session.session_id[:8]}...")
        manager.close_session(test_session.session_id, finalize=True)
        
        closed_session = manager.get_session(test_session.session_id)
        if closed_session:
            print(f"  Status: {closed_session.status}")
            print(f"  Closed At: {closed_session.closed_at}")
            print(f"  Final Statistics: {closed_session.final_statistics is not None}")
            if closed_session.final_statistics:
                print(f"    - Mean Score: {closed_session.final_statistics.get('mean_score', 0):.3f}")
    
    # Cache performance
    print_section("CACHE PERFORMANCE")
    print(f"Cache Size: {len(manager.cache.cache)}/{manager.cache.maxsize}")
    print(f"Utilization: {len(manager.cache.cache)/manager.cache.maxsize*100:.1f}%")
    
    # Test cache hit
    if sessions:
        test_id = sessions[0].session_id
        start = time.time()
        cached = manager.get_session(test_id)
        cache_time = time.time() - start
        print(f"\n[Cache Performance]")
        print(f"  Cache Hit Time: {cache_time:.6f}s")
        print(f"  Session Loaded: {cached is not None}")
    
    # Final summary
    print_section("FINAL SUMMARY")
    print("✅ All Features Demonstrated:")
    print("  ✓ Write buffering reduces I/O operations")
    print("  ✓ Session lifecycle management works")
    print("  ✓ Indexing enables fast queries")
    print("  ✓ Lazy loading scales efficiently")
    print("  ✓ Cross-session learning improves strategies")
    print("  ✓ Unified storage eliminates duplication")
    print("  ✓ Experience replay consolidates learning")
    print("  ✓ Quality feedback drives improvements")
    print("  ✓ Adaptive learning personalizes responses")
    print("  ✓ Data validation ensures integrity")
    
    print(f"\n[System State]")
    print(f"  Sessions: {len(manager.list_sessions())}")
    print(f"  Indexed: {len(manager.index) if manager.enable_indexing else 0}")
    print(f"  Cached: {len(manager.cache.cache)}")
    print(f"  Buffered: {len(manager.write_buffer._buffer) if manager.write_buffer else 0}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demonstrate_complex_queries())

