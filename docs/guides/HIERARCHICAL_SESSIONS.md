# Hierarchical Session-Based Persistence

## Overview

The system now implements hierarchical session-based persistence, inspired by research on hierarchical multi-task learning, persistent learning mechanisms, and knowledge retention strategies. This provides better organization, retrieval, and learning across temporal boundaries.

## Architecture

### Hierarchy Levels

```
SessionGroup (topics, time periods, users)
  └── Session (conversation/work session)
      └── EvaluationEntry (individual evaluations)
```

### Key Components

1. **SessionGroup**: Collections of sessions organized by:
   - Time period (day, week, month)
   - Topic/context
   - User ID
   - Custom metadata

2. **Session**: A bounded temporal window containing:
   - Multiple evaluations
   - Context/topic information
   - User identifier (optional)
   - Metadata
   - Statistics (mean score, quality issues, etc.)

3. **EvaluationEntry**: Individual evaluation with:
   - Query and response
   - Quality score and flags
   - Metadata (schema, research usage, etc.)
   - Timestamp

## Features

### Automatic Grouping

Sessions are automatically grouped by:
- **Day**: All sessions from the same day
- **Week**: All sessions from the same week
- **Month**: All sessions from the same month
- **Topic**: Sessions with the same context/topic
- **None**: No automatic grouping

### Session Management

- **Create sessions**: Automatically or manually
- **Add evaluations**: Evaluations are added to current session
- **List sessions**: Filter by group, user, or limit
- **Get statistics**: Session-level and aggregate statistics
- **Archive sessions**: Move old sessions to archive directory

### Persistence

- **Per-session files**: Each session stored as `{session_id}.json`
- **Groups file**: `groups.json` stores group metadata
- **Archive directory**: Old sessions moved to `sessions/archive/`
- **Auto-save**: Sessions saved immediately after creation/update

## Usage

### Programmatic

```python
from bop.quality_feedback import QualityFeedbackLoop
from bop.session_manager import HierarchicalSessionManager

# Quality feedback automatically uses sessions
feedback = QualityFeedbackLoop(use_sessions=True, session_context="my_topic")

# Or create session manager directly
manager = HierarchicalSessionManager(
    sessions_dir=Path("sessions"),
    auto_group_by="day",  # Group by day
)

# Create a session
session_id = manager.create_session(
    context="research_session",
    user_id="user123",
    metadata={"project": "bop"},
)

# Add evaluations (automatically added to current session)
manager.add_evaluation(
    query="What is trust?",
    response="Trust is...",
    response_length=100,
    score=0.8,
    judgment_type="relevance",
    quality_flags=[],
    reasoning="Good response",
    metadata={"schema": "chain_of_thought"},
)

# Get session statistics
session = manager.get_session(session_id)
stats = session.get_statistics()
print(f"Mean score: {stats['mean_score']}")

# List sessions
sessions = manager.list_sessions(user_id="user123", limit=10)

# Get aggregate statistics
agg_stats = manager.get_aggregate_statistics(group_id="day_2024-11-14")
```

### CLI

```bash
# List sessions
bop sessions --list

# List sessions with statistics
bop sessions --list --stats

# Filter by group
bop sessions --list --group day_2024-11-14

# Show aggregate statistics
bop sessions --stats
```

## Research Inspiration

### Hierarchical Multi-Task Learning

Inspired by HierSRec and Netflix FM-Intent systems that use hierarchical task structures where auxiliary tasks inform main tasks, creating richer representations and better generalization.

### Persistent Learning Mechanisms

Based on research on:
- **Experience replay**: Storing and replaying important experiences
- **Hippocampal-inspired replay**: Forward and reverse replay for consolidation
- **Hybrid neural networks**: Dual memory systems (fast episodic, slow semantic)

### Knowledge Retention

Incorporates principles from:
- **Spaced learning**: Organizing sessions temporally
- **Contextual organization**: Grouping by topic/context
- **Hierarchical compression**: Multiple levels of detail

## File Structure

```
sessions/
├── groups.json                    # Group metadata
├── {session_id_1}.json           # Individual session files
├── {session_id_2}.json
└── archive/                      # Archived sessions
    └── {old_session_id}.json
```

## Benefits

1. **Better Organization**: Sessions naturally group related evaluations
2. **Temporal Analysis**: Easy to analyze patterns over time
3. **Context Preservation**: Session context maintained with evaluations
4. **Scalability**: Can archive old sessions while keeping recent ones active
5. **Flexible Grouping**: Multiple grouping strategies for different analyses
6. **Hierarchical Learning**: Learn patterns at session and group levels

## Integration

The hierarchical session manager is integrated into:
- **QualityFeedbackLoop**: Automatically uses sessions when enabled
- **KnowledgeAgent**: Creates sessions with context "agent_session"
- **CLI**: New `sessions` command for session management

## Future Enhancements

Potential improvements:
- Session merging: Combine related sessions
- Cross-session learning: Learn patterns across sessions
- Session similarity: Find similar sessions
- Session recommendations: Suggest relevant past sessions
- Advanced grouping: ML-based grouping strategies

