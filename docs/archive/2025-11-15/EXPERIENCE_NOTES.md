# Experience Notes: Testing the System

## What I Tested

1. **Topology Features** ✓
   - Confidence updates work
   - Clique computation works
   - Attractor basins work
   - Trust summary includes calibration error
   - Schema consistency checking works

2. **Orchestrator** ⚠️
   - Returns structured results
   - But MCP tools return placeholders (`needs_mcp_call: True`)
   - Topology integration works
   - Decomposition works (fallback to simple)

3. **Agent Chat** ⚠️
   - Works but LLM service needs API key
   - Falls back gracefully
   - Research integration works

## Issues Found

### 1. MCP Tools Not Actually Called
**Problem**: `call_mcp_tool()` always returns `needs_mcp_call: True` placeholder
**Impact**: Research results are placeholders, not real data
**Solution**: Need to actually call MCP tools when available

### 2. LLM Service Requires API Key
**Problem**: LLM service fails without OPENAI_API_KEY
**Impact**: Responses are fallback text, not LLM-generated
**Solution**: Already handles gracefully, but should document better

### 3. Tool Selection Could Be Smarter
**Problem**: Tool selection is keyword-based heuristics
**Impact**: May select wrong tools for some queries
**Solution**: Could use LLM to select tools based on query understanding

### 4. Topology Metrics Not Used in Decision Making
**Problem**: We compute topology metrics but don't use them to guide tool selection
**Impact**: Missing opportunity to optimize based on information geometry
**Solution**: Use topology metrics to rank/select tools

## What Works Well

1. **Trust/Uncertainty Integration** ✓
   - Confidence updates work smoothly
   - Calibration tracking is implemented
   - Schema validation is in place

2. **Topology Analysis** ✓
   - Clique computation is fast
   - Impact analysis works
   - Trust-aware filtering works

3. **Error Handling** ✓
   - Graceful degradation everywhere
   - No crashes on missing dependencies
   - Clear error messages

4. **Modular Design** ✓
   - Components are decoupled
   - Easy to test in isolation
   - Clear interfaces

## Decisions Based on Experience

### 1. Make MCP Tools Actually Work
- Need to call real MCP functions when available
- Should fall back to placeholders only when tools truly unavailable
- Consider using the tool calling interface directly

### 2. Improve Tool Selection
- Use topology to influence tool selection (already started)
- Consider LLM-based tool selection for complex queries
- Track which tools work best for which query types

### 3. Use Topology Metrics More
- Use Fisher Information to guide information gathering
- Use attractor basins to identify knowledge gaps
- Use d-separation to avoid redundant queries

### 4. Better Feedback
- Show topology metrics in CLI output
- Show which tools were selected and why
- Show trust scores for results

### 5. Testing Strategy
- Need integration tests with real MCP calls (when available)
- Need tests for LLM integration (with mock API)
- Need tests for topology-guided tool selection

## Next Steps

1. Fix MCP tool calling to use real tools when available
2. Add topology-guided tool selection improvements
3. Add better CLI feedback showing topology metrics
4. Add integration tests for full workflow
5. Document the experience and improvements

