# System Coexistence Strategy for BOP

**Date:** 2025-11-15  
**Purpose:** Guide for integrating new patterns (Skills, system reminders, etc.) without breaking existing functionality

## Core Principles

### 1. Modularity and Loose Coupling

**Strategy:**
- Isolate new features in separate modules/components
- Use clear, well-defined interfaces
- Minimize dependencies between new and old code

**BOP Application:**
- Skills system: Separate `skills/` directory, loaded on demand
- System reminders: Optional feature flag, doesn't affect core agent loop
- Sub-agents: New dispatch mechanism, existing agent unchanged

**Implementation:**
```python
# New features are opt-in
agent = KnowledgeAgent(
    enable_skills=True,  # Optional, defaults to False
    enable_system_reminders=True,  # Optional
    enable_sub_agents=False,  # Optional
)
```

### 2. Gradual Adoption (Strangler Pattern)

**Strategy:**
- Introduce new patterns alongside existing ones
- Route subset of operations to new code
- Expand coverage as confidence builds

**BOP Application:**
- Phase 1: Skills available but not required
- Phase 2: Agent can use Skills when relevant
- Phase 3: Skills become default for certain tasks
- Keep existing schema system working

**Migration Path:**
1. **Parallel Systems:** Skills and schemas coexist
2. **Feature Flags:** Enable/disable new features
3. **Gradual Migration:** Move tasks to new system incrementally
4. **Fallback:** Always fall back to existing system if new one fails

### 3. Backward Compatibility

**Strategy:**
- Maintain existing APIs and interfaces
- Version new interfaces if breaking changes needed
- Provide adapters/bridges between old and new

**BOP Application:**
- Existing `agent.chat()` API unchanged
- New parameters are optional with defaults
- Existing schemas continue to work
- Skills are additive, not replacement

**Example:**
```python
# Old code still works
response = await agent.chat("query")

# New features are opt-in
response = await agent.chat(
    "query",
    use_skills=True,  # New, optional
    use_system_reminders=True,  # New, optional
)
```

### 4. Comprehensive Testing

**Strategy:**
- Automated tests for new patterns
- Regression tests for existing functionality
- Integration tests for coexistence

**BOP Application:**
- Test Skills loading doesn't break existing flows
- Test system reminders are optional
- Test backward compatibility
- Test fallback mechanisms

**Test Strategy:**
```python
# Test existing functionality still works
def test_existing_agent_unchanged():
    agent = KnowledgeAgent()
    response = await agent.chat("test")
    assert response is not None

# Test new features are opt-in
def test_skills_optional():
    agent = KnowledgeAgent(enable_skills=False)
    # Should work without Skills
    response = await agent.chat("test")
    assert response is not None

# Test coexistence
def test_skills_and_schemas_coexist():
    agent = KnowledgeAgent(enable_skills=True)
    # Both should work
    response = await agent.chat("test", use_schema="decompose_and_synthesize")
    assert response is not None
```

### 5. Error Handling and Monitoring

**Strategy:**
- Proactive error handling for new patterns
- Comprehensive logging at integration points
- Quick rollback if issues detected

**BOP Application:**
- Skills loading failures: Fall back to schemas
- System reminder failures: Continue without reminders
- Sub-agent failures: Fall back to main agent
- Log all integration points

**Error Handling Pattern:**
```python
try:
    skill = load_skill(skill_name)
    context.append(skill.content)
except SkillNotFoundError:
    logger.warning(f"Skill {skill_name} not found, continuing without it")
    # Continue with existing behavior
except Exception as e:
    logger.error(f"Error loading skill: {e}")
    # Fall back gracefully
```

### 6. Feature Flags

**Strategy:**
- Use feature flags to enable/disable new features
- Allow per-request or per-session control
- Easy rollback if issues occur

**BOP Application:**
```python
# Environment-based flags
BOP_ENABLE_SKILLS=true
BOP_ENABLE_SYSTEM_REMINDERS=true
BOP_ENABLE_SUB_AGENTS=false

# Per-request flags
response = await agent.chat(
    "query",
    use_skills=os.getenv("BOP_ENABLE_SKILLS", "false") == "true",
)
```

### 7. Versioning and Rollback

**Strategy:**
- Semantic versioning for new features
- Maintain parallel code paths
- Quick rollback mechanism

**BOP Application:**
- Version Skills API: `skills/v1/`
- Keep old schema system: `schemas/`
- Configuration-based rollback

## Implementation Plan for BOP

### Phase 1: Foundation (Current)

**Status:** ✅ Complete
- Skills directory created
- Repository analysis skill added
- Documentation created
- No breaking changes

### Phase 2: Optional Integration

**Goal:** Make Skills available but optional

**Steps:**
1. Add `enable_skills` parameter to `KnowledgeAgent`
2. Implement skill loading mechanism (opt-in)
3. Add skill discovery (read `skills/` directory)
4. Test backward compatibility

**Code:**
```python
class KnowledgeAgent:
    def __init__(
        self,
        enable_skills: bool = False,  # Opt-in
        skills_dir: Path = Path("skills"),
        ...
    ):
        self.enable_skills = enable_skills
        self.skills_dir = skills_dir
        if enable_skills:
            self.skills = self._load_skills()
        else:
            self.skills = {}
```

### Phase 3: System Reminders

**Goal:** Add system reminders without breaking existing flow

**Steps:**
1. Add `enable_system_reminders` parameter
2. Implement reminder generation (optional)
3. Inject reminders into context (non-breaking)
4. Test existing behavior unchanged

**Code:**
```python
def _generate_system_reminders(self, context: Dict) -> List[str]:
    if not self.enable_system_reminders:
        return []
    
    reminders = []
    # Generate based on TODO state, tool usage, etc.
    if self.todo_list:
        reminders.append(f"Your todo list: {self.todo_list}")
    return reminders
```

### Phase 4: Sub-Agent Dispatch

**Goal:** Add sub-agents for parallelism

**Steps:**
1. Add `enable_sub_agents` parameter
2. Implement dispatch mechanism
3. Test fallback to main agent
4. Monitor performance

### Phase 5: Instructions in Tool Results

**Goal:** Add instructions to tool results

**Steps:**
1. Add instruction templates to tools
2. Inject instructions into results
3. Test backward compatibility
4. Monitor effectiveness

## Coexistence Patterns

### Pattern 1: Adapter Pattern

**Use:** Bridge between old and new systems

```python
class SkillAdapter:
    """Adapts Skills to work with existing schema system"""
    
    def to_schema_format(self, skill: Skill) -> Dict:
        # Convert skill to schema-like format
        return {
            "name": skill.name,
            "instructions": skill.content,
            "type": "skill",
        }
```

### Pattern 2: Facade Pattern

**Use:** Simplify interface while maintaining backward compatibility

```python
class AgentFacade:
    """Simplified interface that uses both old and new systems"""
    
    def chat(self, message: str, **kwargs):
        # Route to appropriate system
        if kwargs.get("use_skills"):
            return self._chat_with_skills(message, **kwargs)
        else:
            return self._chat_with_schemas(message, **kwargs)
```

### Pattern 3: Strategy Pattern

**Use:** Allow switching between old and new approaches

```python
class ReasoningStrategy:
    """Strategy for reasoning approach"""
    
    def reason(self, query: str):
        raise NotImplementedError

class SchemaStrategy(ReasoningStrategy):
    """Existing schema-based reasoning"""
    ...

class SkillStrategy(ReasoningStrategy):
    """New skill-based reasoning"""
    ...
```

## Testing Strategy

### Unit Tests
- Test new features in isolation
- Test backward compatibility
- Test error handling

### Integration Tests
- Test coexistence of old and new
- Test fallback mechanisms
- Test feature flags

### Regression Tests
- Ensure existing functionality unchanged
- Test all existing tests still pass
- Test performance not degraded

## Monitoring and Observability

### Metrics to Track
- Feature adoption (Skills usage, reminders, etc.)
- Error rates (new vs. old paths)
- Performance (new vs. old)
- Fallback frequency

### Logging
- Log when new features are used
- Log when fallbacks occur
- Log errors in new systems
- Log performance differences

### Alerts
- Alert on high error rates in new features
- Alert on frequent fallbacks
- Alert on performance degradation

## Rollback Plan

### Immediate Rollback
1. Disable feature flags
2. Revert to previous version
3. Monitor for stability

### Gradual Rollback
1. Reduce feature usage percentage
2. Monitor impact
3. Continue rollback if needed

### Data Preservation
- Skills remain in `skills/` directory
- No data loss on rollback
- Configuration preserved

## Communication Plan

### Documentation
- Update AGENTS.md with new features
- Add migration guide
- Document coexistence patterns

### Team Communication
- Announce new features
- Provide training
- Share best practices

### User Communication
- Document opt-in nature
- Provide examples
- Explain benefits

## Success Criteria

### Phase 1 (Foundation)
- ✅ Skills directory created
- ✅ First skill added
- ✅ Documentation complete

### Phase 2 (Optional Integration)
- [ ] Skills can be enabled/disabled
- [ ] Backward compatibility maintained
- [ ] Tests pass

### Phase 3 (System Reminders)
- [ ] Reminders optional
- [ ] Existing behavior unchanged
- [ ] Performance acceptable

### Phase 4 (Sub-Agents)
- [ ] Sub-agents work correctly
- [ ] Fallback tested
- [ ] Performance improved

### Phase 5 (Tool Instructions)
- [ ] Instructions in results
- [ ] Backward compatible
- [ ] Effective

## Risk Mitigation

### Risks
1. **Breaking Changes:** Mitigated by opt-in features
2. **Performance Degradation:** Mitigated by feature flags
3. **Complexity Increase:** Mitigated by modular design
4. **Team Confusion:** Mitigated by documentation

### Mitigation Strategies
- Always provide fallback
- Comprehensive testing
- Gradual rollout
- Clear documentation
- Monitoring and alerts

## Conclusion

By following these principles:
- **Modularity:** New features isolated
- **Gradual Adoption:** Phased rollout
- **Backward Compatibility:** Existing code works
- **Testing:** Comprehensive coverage
- **Monitoring:** Track adoption and issues
- **Rollback:** Quick recovery if needed

BOP can integrate new patterns (Skills, system reminders, sub-agents) while maintaining stability and backward compatibility.

