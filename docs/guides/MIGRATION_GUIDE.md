# Migration Guide: Knowledge Display Enhancements

## Overview

This guide helps you migrate to the new knowledge display features. All changes are **backwards compatible** - existing code will continue to work, but you can now access new features.

## What's New

### New Response Fields

The `chat()` method now returns additional optional fields:

```python
response = await agent.chat("Your query", use_research=True)

# NEW: Progressive disclosure tiers
response["response_tiers"] = {
    "summary": "...",      # 1-2 sentence summary
    "structured": "...",   # Organized breakdown
    "detailed": "...",     # Full response
    "evidence": "...",     # Full research synthesis
}

# NEW: Extracted user beliefs (if any were stated)
response["prior_beliefs"] = [
    {"text": "I think X", "source": "user_statement"}
]

# ENHANCED: Research results now include more topology data
if response.get("research"):
    research = response["research"]
    
    # NEW: Source agreement/disagreement matrix
    research["source_matrix"] = {...}
    
    # ENHANCED: Topology now includes more metrics
    topology = research["topology"]
    topology["source_credibility"] = {...}  # NEW
    topology["verification_info"] = {...}   # NEW
    topology["cliques"] = [...]              # NEW (detailed)
```

### Backwards Compatibility

**All existing code continues to work**:
- `response["response"]` still exists and works as before
- `response["research"]` still exists with all existing fields
- `response["quality"]` still exists
- All existing fields are unchanged

**New fields are optional**:
- `response_tiers` is always present (but may be empty if no research)
- `prior_beliefs` is only present if beliefs were extracted
- Enhanced topology fields are only present if research was conducted

## Migration Steps

### Step 1: No Changes Required

Your existing code will continue to work without any changes:

```python
# This still works exactly as before
response = await agent.chat("What is trust?", use_research=True)
print(response["response"])
```

### Step 2: Access New Features (Optional)

If you want to use new features, access them conditionally:

```python
response = await agent.chat("What is trust?", use_research=True)

# Use progressive disclosure
if response.get("response_tiers"):
    summary = response["response_tiers"].get("summary")
    if summary:
        print("Summary:", summary)
    else:
        print(response["response"])  # Fallback to full response

# Access trust metrics
if response.get("research") and response["research"].get("topology"):
    topology = response["research"]["topology"]
    if "source_credibility" in topology:
        print("Source credibility:", topology["source_credibility"])
```

### Step 3: Update Display Code (Optional)

If you have custom display code, you can enhance it:

```python
# Before
print(response["response"])

# After (with progressive disclosure)
tiers = response.get("response_tiers", {})
if tiers.get("summary"):
    print("Summary:", tiers["summary"])
    print("\n[Show more details]")
else:
    print(response["response"])
```

## API Changes

### KnowledgeAgent

**No breaking changes**:
- `chat()` method signature unchanged
- All existing parameters work as before
- New state variables (`prior_beliefs`, `recent_queries`) are internal

**New optional features**:
- Belief extraction happens automatically (no API change)
- Context adaptation happens automatically (no API change)
- Progressive disclosure created automatically (no API change)

### StructuredOrchestrator

**New optional parameter**:
```python
# Before
result = await orchestrator.research_with_schema(query, schema_name)

# After (optional - works without it)
result = await orchestrator.research_with_schema(
    query,
    schema_name,
    prior_beliefs=[...]  # NEW: Optional parameter
)
```

**Backwards compatible**: If you don't pass `prior_beliefs`, it defaults to `None` and works as before.

### Server API

**New optional fields in ChatResponse**:
```python
class ChatResponse(BaseModel):
    # ... existing fields ...
    response_tiers: Optional[Dict[str, str]] = None      # NEW
    prior_beliefs: Optional[List[Dict[str, Any]]] = None  # NEW
    source_matrix: Optional[Dict[str, Dict]] = None     # NEW
```

**Backwards compatible**: All fields are optional, existing API clients continue to work.

## CLI Changes

**No breaking changes**:
- All existing commands work as before
- New display features are automatically shown when research is conducted
- No new command-line options required

**Enhanced output**:
- Trust metrics table shown automatically
- Source credibility displayed automatically
- Progressive disclosure (summary first) shown automatically

## Web UI Changes

**No breaking changes**:
- Existing web UI continues to work
- New features integrated automatically

**Enhanced display**:
- Progressive disclosure (summary first)
- Trust metrics shown
- Source references included

## Testing Your Migration

### Verify Backwards Compatibility

```python
# Test that existing code still works
response = await agent.chat("Test", use_research=False)
assert "response" in response
assert isinstance(response["response"], str)
```

### Test New Features

```python
# Test that new features are available
response = await agent.chat("Test", use_research=True)
assert "response_tiers" in response
assert "summary" in response["response_tiers"]
```

## Common Patterns

### Pattern 1: Gradual Migration

Start using new features gradually:

```python
# Phase 1: Keep existing code
print(response["response"])

# Phase 2: Add progressive disclosure
tiers = response.get("response_tiers", {})
if tiers.get("summary"):
    print(tiers["summary"])
else:
    print(response["response"])

# Phase 3: Add trust metrics
if response.get("research"):
    topology = response["research"].get("topology", {})
    if "trust_summary" in topology:
        print(f"Trust: {topology['trust_summary']['avg_trust']:.2f}")
```

### Pattern 2: Feature Detection

Check for features before using:

```python
# Check if new features are available
has_tiers = "response_tiers" in response
has_trust = response.get("research", {}).get("topology", {}).get("trust_summary")

if has_tiers:
    # Use progressive disclosure
    pass

if has_trust:
    # Use trust metrics
    pass
```

### Pattern 3: Fallback Handling

Always provide fallbacks:

```python
# Progressive disclosure with fallback
tiers = response.get("response_tiers", {})
display_text = tiers.get("summary") or response.get("response", "No response")
print(display_text)
```

## Breaking Changes

**None**. All changes are additive and backwards compatible.

## Deprecations

**None**. No features are deprecated.

## See Also

- `AGENTS.md` - Agent usage patterns with new features
- `KNOWLEDGE_DISPLAY_GUIDE.md` - Guide to new display features
- `TRUST_AND_UNCERTAINTY_USER_GUIDE.md` - Guide to trust metrics

