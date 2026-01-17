# Unified Planning Integration Analysis for BOP

## Executive Summary

Unified Planning (UP) offers a formal framework for modeling and solving sequential decision problems. BOP currently uses heuristic-based tool selection and sequential orchestration. UP could formalize this as a planning problem, enabling:

1. **Optimal tool sequencing** with cost/latency optimization
2. **Hierarchical planning** for decompose-and-synthesize schemas
3. **Temporal planning** for parallel tool calls and resource constraints
4. **Contingent planning** for handling uncertain tool results
5. **Multi-agent planning** if tools are modeled as agents

## Current State Analysis

### BOP's Current Approach

BOP uses:
- **Heuristic tool selection**: Keyword-based matching in `ToolSelector.select_tools()`
- **Sequential execution**: Tools called one-by-one per subproblem
- **Structured schemas**: Reasoning patterns (chain_of_thought, decompose_and_synthesize, etc.)
- **Topology analysis**: Clique complexes for context coherence

### Limitations

1. **No formal optimization**: Tool selection is heuristic, not optimal
2. **No parallelization**: Tools called sequentially even when independent
3. **No cost awareness**: Doesn't optimize for API costs or latency
4. **No uncertainty handling**: Doesn't plan for tool failures or uncertain results
5. **No resource constraints**: Doesn't model rate limits or budget constraints

## Unified Planning Integration Opportunities

### 1. Research Workflow Planning (Classical/Numeric Planning)

**Problem**: Given a research query, find optimal sequence of tool calls to answer it.

**Modeling**:
- **Fluents**:
  - `has_information(query_topic, completeness)` - Numeric fluent tracking information completeness
  - `tool_available(tool_type)` - Boolean fluent for tool availability
  - `api_budget_remaining(amount)` - Numeric fluent for cost tracking
  - `query_answered(query_id)` - Boolean fluent for goal state

- **Actions**:
  - `call_tool(tool_type, query)` with:
    - Preconditions: `tool_available(tool_type)`, `api_budget_remaining >= cost(tool_type)`
    - Effects: `has_information(query_topic, completeness + delta)`, `api_budget_remaining -= cost(tool_type)`
    - Cost: API cost + latency estimate

- **Goal**: `query_answered(query_id)` AND `has_information(query_topic, completeness) >= threshold`

**Benefits**:
- Optimal tool sequences considering costs
- Automatic handling of dependencies (e.g., search before scrape)
- Budget-aware planning

### 2. Hierarchical Planning for Decompose-and-Synthesize

**Problem**: The `decompose_and_synthesize` schema is inherently hierarchical - break into subproblems, solve each, then combine.

**Modeling**:
- **High-level tasks**:
  - `research_topic(topic)` - Abstract task to research a topic
  - `synthesize_results(subtopics)` - Abstract task to combine results

- **Methods**:
  - `research_topic` can be decomposed into:
    - `research_subtopic(subtopic_1)` AND `research_subtopic(subtopic_2)` AND ...
  - Each `research_subtopic` can be achieved by:
    - `call_tool(perplexity_deep, subtopic)` OR `call_tool(firecrawl_search, subtopic)` OR ...

- **Initial task network**: `research_topic(main_query)`

**Benefits**:
- Formalizes the hierarchical reasoning structure
- Enables alternative decomposition strategies
- Natural fit for UP's hierarchical planning support

### 3. Temporal Planning for Parallel Tool Calls

**Problem**: Some tools can be called in parallel, but current implementation is sequential.

**Modeling**:
- **Durative actions**:
  - `call_tool(tool_type, query)` with:
    - Duration: `latency(tool_type)` (estimated)
    - Conditions: `tool_available(tool_type)` at start
    - Effects: `has_information(topic, completeness)` at end

- **Temporal constraints**:
  - Some tools must be sequential (e.g., search before scrape)
  - Others can be parallel (e.g., multiple search tools)
  - Resource constraints: `api_rate_limit` prevents too many simultaneous calls

**Benefits**:
- Parallel tool calls where possible
- Respects dependencies and resource constraints
- Optimizes makespan (total time to answer query)

### 4. Contingent Planning for Uncertain Results

**Problem**: Tool results are uncertain - may fail, may be incomplete, may need follow-up queries.

**Modeling**:
- **Sensing actions**: `call_tool(tool_type, query)` observes `result_quality(tool_type, query)`
- **Non-deterministic initial state**: `tool_available(tool_type)` may be unknown (rate limited?)
- **Conditional effects**: If `result_quality < threshold`, then need to call additional tools

**Benefits**:
- Plans that adapt to tool failures
- Handles uncertainty in information completeness
- Can plan for verification steps

### 5. Multi-Agent Planning (Alternative Perspective)

**Problem**: If we model each tool as an agent with its own capabilities and constraints.

**Modeling**:
- **Agents**: `perplexity_agent`, `firecrawl_agent`, `tavily_agent`
- **Agent-specific fluents**: Each agent has `agent_available(agent)`, `agent_budget(agent)`
- **Agent-specific actions**: Each agent can only call its own tools
- **Shared environment**: `has_information(topic)` is shared across agents

**Benefits**:
- Models rate limits per tool/service
- Can handle privacy constraints (some tools can't access certain information)
- Natural fit for distributed tool orchestration

## Implementation Strategy

### Option A: Unified Planning (Full Planning Framework)

**Phase 1: Basic Planning Integration**

1. **Add UP dependency** (optional):
   ```toml
   [project.optional-dependencies]
   planning = [
       "unified-planning>=1.1.0",
   ]
   ```

2. **Create planning problem builder**:
   - `src/bop/planning.py` - Module for building UP problems from BOP queries
   - Convert research queries to planning problems
   - Model tool calls as actions

3. **Integrate with orchestrator**:
   - Option to use UP planner instead of heuristic tool selection
   - Fallback to heuristics if planning fails

### Option B: SAT/SMT Solvers (Lighter Weight)

**Phase 1: Constraint-Based Tool Selection**

1. **Add PySAT dependency** (optional):
   ```toml
   [project.optional-dependencies]
   planning = [
       "python-sat>=0.1.7",  # PySAT
       # Optional: "z3-solver>=4.12.0",  # Z3 for SMT
   ]
   ```

2. **Create constraint problem builder**:
   - `src/bop/constraints.py` - Module for building SAT/SMT problems
   - Encode tool availability, dependencies, costs as constraints
   - Use SAT solver to find valid tool sequences

3. **Integrate with orchestrator**:
   - Option to use SAT solver for constraint satisfaction
   - Fallback to heuristics if solving fails

### Recommendation: Start with SAT/SMT

**Rationale**:
- Lighter weight (PySAT is smaller, faster to install)
- More direct control over constraints
- Can encode simple planning problems as constraints
- Can upgrade to UP later if needed
- Many planning engines use SAT solvers internally anyway

**Migration Path**:
1. Start with PySAT for constraint satisfaction
2. If need planning semantics, add UP
3. Can use both: SAT for constraints, UP for planning

### Phase 2: Hierarchical Planning

1. **Model decompose_and_synthesize as HTN**:
   - High-level tasks for research subtopics
   - Methods for tool selection
   - Initial task network from query decomposition

2. **Integrate with schemas**:
   - Other schemas (chain_of_thought, etc.) could also benefit from planning

### Phase 3: Advanced Features

1. **Temporal planning** for parallelization
2. **Contingent planning** for uncertainty
3. **Cost optimization** using quality metrics
4. **Learning** from historical tool performance

## Example: Research Query as Planning Problem

```python
from unified_planning.shortcuts import *

# Problem: Research "structured reasoning in LLMs"
problem = Problem("research_query")

# Types
ToolType = UserType("ToolType")
QueryTopic = UserType("QueryTopic")

# Fluents
has_information = Fluent("has_information", RealType(0, 1), topic=QueryTopic)
tool_available = Fluent("tool_available", BoolType(), tool=ToolType)
api_budget = Fluent("api_budget", RealType(0, 100))  # Remaining budget
query_answered = Fluent("query_answered", BoolType(), topic=QueryTopic)

# Actions
call_perplexity = InstantaneousAction("call_perplexity", topic=QueryTopic)
t = call_perplexity.parameter("topic")
call_perplexity.add_precondition(tool_available(Object("perplexity", ToolType)))
call_perplexity.add_precondition(GE(api_budget, 0.1))  # Cost
call_perplexity.add_effect(has_information(t), Plus(has_information(t), 0.3))
call_perplexity.add_effect(api_budget, Minus(api_budget, 0.1))

call_firecrawl = InstantaneousAction("call_firecrawl", topic=QueryTopic)
t = call_firecrawl.parameter("topic")
call_firecrawl.add_precondition(tool_available(Object("firecrawl", ToolType)))
call_firecrawl.add_precondition(GE(api_budget, 0.05))
call_firecrawl.add_effect(has_information(t), Plus(has_information(t), 0.2))
call_firecrawl.add_effect(api_budget, Minus(api_budget, 0.05))

# Objects
main_topic = Object("structured_reasoning", QueryTopic)
perplexity_tool = Object("perplexity", ToolType)
firecrawl_tool = Object("firecrawl", ToolType)

# Initial state
problem.set_initial_value(has_information(main_topic), 0.0)
problem.set_initial_value(tool_available(perplexity_tool), True)
problem.set_initial_value(tool_available(firecrawl_tool), True)
problem.set_initial_value(api_budget, 1.0)
problem.set_initial_value(query_answered(main_topic), False)

# Goal: Have enough information and answer the query
problem.add_goal(GE(has_information(main_topic), 0.7))
problem.add_goal(query_answered(main_topic))

# Quality metric: Minimize cost (mbopmize remaining budget)
problem.add_quality_metric(MinimizeExpressionOnFinalState(Minus(FluentExp(api_budget))))

# Solve
with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    if result.plan:
        print(f"Optimal plan: {result.plan}")
```

## Alternative: SAT/SMT Solvers

### Overview

Instead of full planning frameworks, SAT/SMT solvers offer a lighter-weight alternative for constraint satisfaction and optimization:

- **PySAT**: Python toolkit unifying many SAT solvers (MiniSat, Glucose, Kissat, etc.)
- **SMT Solvers**: Z3, CVC5, Yices, Bitwuzla for theory reasoning
- **Painless**: Parallel/distributed SAT solving in Python

### When SAT/SMT Might Be Better

**Use SAT/SMT when**:
- Problem is primarily constraint satisfaction (tool availability, dependencies)
- Need lightweight solution (no full planning framework)
- Want direct control over constraint encoding
- Problem can be encoded as Boolean/SMT constraints

**Use Unified Planning when**:
- Need full planning semantics (actions, states, goals)
- Want hierarchical/temporal planning
- Need planning-specific features (contingent planning, etc.)
- Problem naturally fits planning paradigm

### Hybrid Approach

Many planning engines use SAT/SMT solvers internally. We could:
1. Use SAT/SMT directly for simple constraint problems
2. Use Unified Planning for complex planning problems
3. Let UP handle SAT/SMT internally for planning problems

## Trade-offs and Considerations

### Advantages

1. **Formal optimization**: Optimal tool sequences instead of heuristics
2. **Cost awareness**: Can optimize for API costs, latency, or information quality
3. **Dependency handling**: Automatic handling of tool dependencies
4. **Extensibility**: Easy to add new tools, constraints, or objectives
5. **Verification**: Can validate plans before execution

### Challenges

1. **Problem modeling complexity**: Need to model tool capabilities, costs, dependencies
2. **Planning overhead**: Planning itself takes time - may not be worth it for simple queries
3. **Uncertainty modeling**: Tool results are uncertain - need good estimates
4. **Engine selection**: Need to choose appropriate UP engines for problem type
5. **Integration complexity**: Need to bridge between UP plans and actual tool calls

### SAT/SMT vs. Planning Trade-offs

**SAT/SMT Advantages**:
- Lighter weight (PySAT is smaller than UP)
- Direct constraint encoding
- Fast for constraint satisfaction
- Many high-performance solvers available

**SAT/SMT Disadvantages**:
- Need to encode planning problems as constraints (more work)
- Less natural for sequential action problems
- No built-in planning semantics

**Planning Advantages**:
- Natural fit for sequential action problems
- Built-in planning semantics
- Rich feature set (hierarchical, temporal, contingent)

**Planning Disadvantages**:
- Heavier dependency
- More abstraction (less direct control)
- May use SAT/SMT internally anyway

### When to Use Planning vs. Heuristics

**Use Planning When**:
- Complex queries with many subproblems
- Cost/latency optimization is important
- Tool dependencies are complex
- Need to handle uncertainty or contingencies

**Use Heuristics When**:
- Simple, straightforward queries
- Planning overhead not justified
- Real-time constraints (planning too slow)
- Tool selection is obvious

## Recommendations

1. **Start with classical planning** for basic tool sequencing
2. **Add hierarchical planning** for decompose_and_synthesize schema
3. **Experiment with temporal planning** for parallelization
4. **Keep heuristics as fallback** - planning should enhance, not replace
5. **Learn from experience** - use historical data to improve problem models

## Next Steps

1. **Prototype**: Implement basic planning integration for simple queries
2. **Evaluate**: Compare planning-based vs. heuristic-based tool selection
3. **Iterate**: Refine problem models based on real usage
4. **Scale**: Add more sophisticated planning features as needed

## Maintenance Considerations

**See `MAINTENANCE_ANALYSIS.md` for detailed maintenance analysis.**

### Key Points

1. **Complexity Cost**: +25-50% codebase size, +1 major dependency
2. **Maintenance Burden**: 2-4 hours/month if planning is used
3. **Risk Mitigation**: Make planning optional, keep heuristics as default
4. **Exit Strategy**: Can be removed if not providing value

### Recommendation

**Proceed with Phase 1 (Prototype)** with clear exit criteria:
- Validate planning actually improves tool selection
- Measure planning overhead (should be <2s for complex queries)
- Assess maintenance burden
- Exit if not providing clear value

**Success Criteria**:
- Planning finds better sequences than heuristics for complex queries
- Planning overhead acceptable
- Problem modeling is manageable
- Real users benefit measurably

