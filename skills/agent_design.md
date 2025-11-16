# Agent Design Skill

**Purpose:** Guide BOP in designing and implementing effective agent architectures.

**Tags:** agent, architecture, design-patterns, best-practices

## Core Principles

### Simplicity
- **Simple agent loop:** `while(tool_use)` pattern
- **Minimal components:** Avoid over-engineering
- **Clear interfaces:** Well-defined tool contracts
- **Single responsibility:** Each component does one thing well

### Planning and Tracking
- **TODO lists:** Use for multi-step tasks
- **Create TODO first:** Usually the first tool call
- **Update regularly:** Keep TODO list current
- **Show progress:** Display TODO state to user

### Context Management
- **System reminders:** Keep agent on track during long sessions
- **Progressive disclosure:** Summary → detailed → evidence
- **Skills pattern:** Dynamic context loading (on-demand)
- **Sub-agents:** For parallelism and context management

### Tool Design
- **Instructions in results:** Repeat critical instructions
- **Clear error handling:** Graceful degradation
- **Tool coherence:** Message matches changed files
- **Security checks:** Validate before execution

## Agent Patterns

### Pattern 1: Simple Agent Loop
```python
while tool_use:
    message = model.generate()
    if message.has_tool_call():
        result = execute_tool(message.tool_call)
        feed_back_to_model(result)
    else:
        break  # Agent finished or asking question
```

### Pattern 2: TODO-Based Planning
- Create TODO list at start of multi-step tasks
- Update TODO list as work progresses
- Use TODO state in system reminders
- Show TODO progress to user

### Pattern 3: System Reminders
- Generate reminders based on:
  - TODO list state
  - Tool usage patterns
  - Conversation context
- Inject reminders into LLM context
- Don't mention reminders to user explicitly

### Pattern 4: Skills Pattern
- Load skills on demand based on query
- Skills are markdown files with domain guidance
- Automatic relevance matching
- Reduces context window bloat

## Best Practices

### Tool Selection
- **Right tool for the job:** Match tool to task
- **Tool chaining:** Use multiple tools when needed
- **Error handling:** Always have fallbacks
- **Performance:** Consider tool latency

### Response Generation
- **Progressive disclosure:** Multiple detail levels
- **Source citations:** Always cite sources
- **Trust metrics:** Show confidence levels
- **Evidence synthesis:** Combine multiple sources

### Error Handling
- **Graceful degradation:** Continue if tools fail
- **Clear error messages:** Help user understand issues
- **Retry logic:** For transient failures
- **Fallback strategies:** Alternative approaches

### Long Sessions
- **System reminders:** Prevent drift
- **TODO tracking:** Keep focus
- **Context management:** Avoid window bloat
- **Sub-agents:** For complex tasks

## Anti-Patterns to Avoid

### Over-Engineering
- ❌ Complex multi-agent hierarchies
- ❌ Sophisticated memory systems (unless needed)
- ❌ Critic patterns (usually unnecessary)
- ❌ Role-playing (not needed for most tasks)

### Context Bloat
- ❌ Loading all context upfront
- ❌ Keeping all history in context
- ❌ Including irrelevant information
- ❌ Not using dynamic loading (Skills)

### Poor Planning
- ❌ No TODO list for complex tasks
- ❌ Not tracking progress
- ❌ Losing focus during long sessions
- ❌ Not using system reminders

## Usage

This skill should be loaded when:
- Designing new agent architectures
- Reviewing agent implementations
- Analyzing agent patterns
- Providing agent design recommendations

