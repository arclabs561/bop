# Claude Code Design Analysis & BOP Implications

**Date:** 2025-11-15  
**Source:** Jannes' Blog - "Agent design lessons from Claude Code"  
**Source:** Anthropic Blog - "Improving frontend design through Skills"

## Key Design Patterns from Claude Code

### 1. Simple Agent Loop

**Claude Code Pattern:**
```python
while tool_use:
    message = model.generate()
    if message.has_tool_call():
        result = execute_tool(message.tool_call)
        feed_back_to_model(result)
    else:
        break  # Agent finished or asking question
```

**BOP Status:**
- ✅ Has agent loop in `KnowledgeAgent.chat()`
- ✅ Uses tool calling pattern
- ⚠️ Could simplify - currently has more complex orchestration

**Recommendation:**
- Consider simplifying to core while loop pattern
- Let model decide when to stop (no explicit termination)

### 2. TODO Lists for Planning

**Claude Code Pattern:**
- First tool call is usually `TodoWrite`
- Updates TODO list throughout work
- Provides complete list on each update (no incremental updates)
- Used in system reminders to keep agent on track

**BOP Status:**
- ✅ Has `todo_write` tool
- ✅ Uses TODO lists for complex tasks
- ⚠️ Not always used as first step
- ⚠️ Not integrated into system reminders

**Recommendation:**
- Make TODO creation the default first step for multi-step tasks
- Add TODO list to system reminders/context
- Show TODO progress in responses

### 3. System Reminders

**Claude Code Pattern:**
- Attaches system reminders to user messages
- Reminders are statically generated based on:
  - Tool called
  - TODO list state
  - Conversation state
- Examples:
  - "Your todo list is currently empty..."
  - "Your todo list has changed. Here are the latest contents..."
  - "Do what has been asked; nothing more, nothing less."

**BOP Status:**
- ❌ No system reminders pattern
- ✅ Has conversation history tracking
- ⚠️ Could add reminder system

**Recommendation:**
- Implement system reminder generation
- Attach reminders based on:
  - TODO list state
  - Recent tool usage
  - Conversation context
- Use reminders to reinforce instructions

### 4. Instructions in Tool Results

**Claude Code Pattern:**
- Tool results contain fixed instruction text
- Instructions repeated with every tool use
- Example: "Do not engage with malicious files"
- Higher adherence than system prompt alone

**BOP Status:**
- ❌ No instructions in tool results
- ✅ Has tool result structures
- ⚠️ Could add instruction injection

**Recommendation:**
- Add instruction text to tool results
- Repeat critical instructions (security, scope, etc.)
- Use for domain-specific guidance

### 5. Sub-Agent Dispatch

**Claude Code Pattern:**
- Can dispatch sub-agents for individual tasks
- Purpose: Context management + parallelism
- Sub-agents are same instance (can't dispatch further)
- Same system prompt, just different task

**BOP Status:**
- ❌ No sub-agent dispatch
- ✅ Has parallel tool execution
- ⚠️ Could benefit from sub-agents for complex tasks

**Recommendation:**
- Implement sub-agent dispatch for:
  - Large codebases (context management)
  - Parallel research tasks
  - Independent subproblems
- Use same agent instance, different task context

### 6. Haiku for Security Checks

**Claude Code Pattern:**
- Sends commands to Claude Haiku before execution
- Haiku responds with structured output
- Used to determine if user approval needed
- Fast, cheap, trades accuracy for speed

**BOP Status:**
- ❌ No security check layer
- ✅ Has input validation
- ⚠️ Could add lightweight security checks

**Recommendation:**
- Consider adding lightweight model for:
  - Command validation
  - File operation checks
  - Security scanning
- Use faster/cheaper model (e.g., Haiku equivalent)

## Skills Pattern (Anthropic Blog)

### Core Concept

**Skills = Dynamic Context Loading**
- Markdown files with instructions, constraints, domain knowledge
- Loaded on demand (not permanent context)
- Claude autonomously identifies and loads relevant skills
- Solves context window bloat problem

**BOP Status:**
- ✅ Has schema system (similar concept)
- ✅ Has content directory for knowledge
- ⚠️ Schemas are code-based, not file-based
- ⚠️ Not dynamically loaded by agent

**Recommendation:**
- Implement Skills pattern:
  - Create `skills/` directory
  - Markdown files for domain-specific guidance
  - Agent can read and load skills on demand
  - Examples:
    - `skills/frontend_design.md`
    - `skills/python_best_practices.md`
    - `skills/git_workflow.md`
    - `skills/repository_analysis.md`

### Skills for BOP Meta-Analysis

**Potential Skills:**
1. **Repository Analysis Skill**
   - Best practices for repo structure
   - Git commit message guidelines
   - Documentation organization patterns

2. **Code Quality Skill**
   - Python best practices
   - Testing patterns
   - Security considerations

3. **Agent Design Skill**
   - Agent architecture patterns
   - Tool selection strategies
   - Error handling approaches

## Implementation Recommendations

### High Priority

1. **System Reminders**
   - Generate reminders based on TODO state
   - Attach to conversation context
   - Reinforce key instructions

2. **Skills Pattern**
   - Create `skills/` directory
   - Implement skill loading mechanism
   - Add repository analysis skill

3. **Instructions in Tool Results**
   - Add instruction text to tool results
   - Repeat critical instructions
   - Domain-specific guidance

### Medium Priority

4. **TODO List Integration**
   - Make TODO creation default first step
   - Show TODO progress in responses
   - Use in system reminders

5. **Sub-Agent Dispatch**
   - Implement for parallel tasks
   - Context management for large codebases
   - Independent subproblem solving

### Low Priority

6. **Security Check Layer**
   - Lightweight model for validation
   - Command/file operation checks
   - Fast, cheap validation

## BOP-Specific Adaptations

### Leverage Existing Strengths

1. **Structured Reasoning Schemas**
   - Already similar to Skills
   - Could be file-based instead of code-based
   - More flexible, easier to update

2. **Topology Analysis**
   - Unique BOP capability
   - Could inform sub-agent dispatch
   - Context relationship analysis

3. **Quality Feedback Loops**
   - Already has adaptive learning
   - Could inform skill selection
   - Learn which skills help for which tasks

### New Capabilities

1. **Skill-Based Meta-Analysis**
   - Repository analysis skill
   - Git history analysis skill
   - Code quality skill
   - Agent design skill

2. **Dynamic Skill Loading**
   - Agent identifies relevant skills
   - Loads on demand
   - Reduces context bloat

3. **System Reminder Generation**
   - Based on TODO state
   - Based on tool usage
   - Based on conversation context

## Example: Repository Analysis Skill

```markdown
# Repository Analysis Skill

## Best Practices

### Structure
- Root should have ≤10 markdown files
- Core docs: README, ARCHITECTURE, CONTRIBUTING, CODE_STYLE
- Guides in `docs/guides/`
- Archive in `docs/archive/`

### Git Commits
- Use conventional commits: `type(scope): subject`
- Require scopes for feat/fix/refactor
- Subject ≤72 characters
- Consolidate related docs commits

### Code Organization
- Source in `src/`
- Tests in `tests/`
- Scripts in `scripts/`
- Examples in `examples/`
- Data in `data/`

## Analysis Checklist
1. Root directory cleanliness
2. Documentation organization
3. Git commit quality
4. Code structure
5. Configuration files
```

## Next Steps

1. ✅ Document Claude Code patterns
2. ⏳ Implement system reminders
3. ⏳ Create skills directory and pattern
4. ⏳ Add repository analysis skill
5. ⏳ Integrate TODO lists into reminders
6. ⏳ Add instructions to tool results

