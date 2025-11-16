# Skills & System Reminders Harmonization Analysis

**Date:** 2025-11-15  
**Status:** Integration gaps identified, harmonization plan created

## Current State Analysis

### ✅ What's Working

1. **Feature Flags**: Consistent with BOP's opt-in pattern
   - `enable_skills` (default False)
   - `enable_system_reminders` (default False)
   - Follows same pattern as `enable_quality_feedback`, `use_constraints`

2. **Skills Implementation**: 
   - Separate module (`skills.py`)
   - Auto-discovery from `skills/` directory
   - Relevance matching works

3. **System Reminders**: 
   - Basic implementation exists
   - TODO list tracking

### ⚠️ Integration Gaps

#### 1. Context Injection Ordering (Inconsistent)

**Current Flow:**
```
1. Experience context → research_query (if research)
2. Experience context → message_with_context (if no research)
3. Skills context → message_with_context (prepended)
4. System reminders → message (inside _generate_response, prepended)
```

**Problem**: System reminders are injected AFTER skills, but they should be highest priority (keep agent on track).

**BOP Pattern**: Context should follow priority order:
- System instructions (highest priority)
- Domain guidance (skills)
- Learned patterns (experience)
- User query

#### 2. CLI Integration Missing

**Current**: CLI doesn't expose `enable_skills` or `enable_system_reminders`

**BOP Pattern**: All features should be accessible via CLI flags

#### 3. Server Integration Missing

**Current**: 
- `ChatRequest` model doesn't include skills/reminders flags
- Server initialization doesn't support these features
- Request-scoped agent doesn't propagate these flags

**BOP Pattern**: Server should support all agent features

#### 4. Architecture Documentation Missing

**Current**: Skills and reminders not documented in `ARCHITECTURE.md`

**BOP Pattern**: All context injection mechanisms should be documented

#### 5. Meta-Learning Integration Missing

**Current**: Skills usage not tracked in `meta_learner` for reflection

**BOP Pattern**: All context sources should be tracked for learning

#### 6. Context Topology Integration Missing

**Current**: Skills not considered in context topology analysis

**BOP Pattern**: All context sources should be part of topology

## Harmonization Plan

### Priority 1: Context Injection Ordering

**Fix**: Standardize context injection order to match BOP's priority model:

```python
# Correct order (highest to lowest priority):
1. System reminders (keep agent on track)
2. Skills context (domain guidance)
3. Experience context (learned patterns)
4. User message
```

**Implementation**:
- Move system reminders injection to BEFORE skills
- Use consistent prepending pattern
- Document priority order

### Priority 2: CLI Integration

**Add CLI flags**:
```python
@app.command()
def chat(
    ...
    enable_skills: bool = typer.Option(False, "--skills/--no-skills", help="Enable Skills pattern"),
    enable_reminders: bool = typer.Option(False, "--reminders/--no-reminders", help="Enable system reminders"),
):
    agent = KnowledgeAgent(
        ...
        enable_skills=enable_skills,
        enable_system_reminders=enable_reminders,
    )
```

### Priority 3: Server Integration

**Update ChatRequest**:
```python
class ChatRequest(BaseModel):
    ...
    enable_skills: bool = False
    enable_system_reminders: bool = False
```

**Update server initialization**:
```python
agent = KnowledgeAgent(
    enable_quality_feedback=True,
    enable_skills=os.getenv("BOP_ENABLE_SKILLS", "false").lower() == "true",
    enable_system_reminders=os.getenv("BOP_ENABLE_SYSTEM_REMINDERS", "false").lower() == "true",
)
```

### Priority 4: Architecture Documentation

**Add to ARCHITECTURE.md**:
- Skills pattern as context injection mechanism
- System reminders as instruction reinforcement
- Context injection priority order
- Integration with meta-learning

### Priority 5: Meta-Learning Integration

**Track skills usage**:
```python
# In meta_learner reflection
tools_used_for_reflection = []
if self.enable_skills and skills_context:
    tools_used_for_reflection.append(f"skill:{skill.name}")
```

### Priority 6: Context Topology Integration

**Consider skills in topology**:
- Skills as context nodes (optional)
- Track which skills were used
- Analyze skill effectiveness

## Implementation Checklist

- [ ] Fix context injection ordering (system reminders → skills → experience → message)
- [ ] Add CLI flags for skills and reminders
- [ ] Update ChatRequest model
- [ ] Update server initialization
- [ ] Update RequestScopedAgent to propagate flags
- [ ] Document in ARCHITECTURE.md
- [ ] Track skills usage in meta_learner
- [ ] Add skills to context topology (optional)
- [ ] Test all integration points
- [ ] Update AGENTS.md with harmonized flow

## Expected Outcome

After harmonization:
- ✅ Consistent context injection ordering
- ✅ CLI access to all features
- ✅ Server API support
- ✅ Architecture documentation complete
- ✅ Meta-learning integration
- ✅ Follows BOP's design patterns throughout

