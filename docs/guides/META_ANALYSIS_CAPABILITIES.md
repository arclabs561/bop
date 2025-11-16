# BOP Meta-Analysis Capabilities

**How BOP can analyze itself using available tools**

## Available Analysis Tools

### 1. MCP Research Tools

BOP has access to 8+ MCP tools for research and analysis:

#### Perplexity (3 tools)
- **`mcp_perplexity_deep_research`**: Deep research with focus areas
  - Best for: Comprehensive analysis of repository patterns, best practices research
  - Example: "What are best practices for Python repository organization?"
  
- **`mcp_perplexity_reason`**: Complex reasoning queries
  - Best for: Analyzing complex relationships, trade-offs, architectural decisions
  - Example: "What are the trade-offs between different commit message strategies?"
  
- **`mcp_perplexity_search`**: Quick factual search
  - Best for: Quick lookups, fact verification
  - Example: "What is conventional commits format?"

#### Firecrawl (3 tools)
- **`mcp_firecrawl-mcp_firecrawl_search`**: Web search
  - Best for: Finding relevant documentation, examples
  - Example: "Search for Python project structure best practices"
  
- **`mcp_firecrawl-mcp_firecrawl_scrape`**: Scrape specific URLs
  - Best for: Extracting content from documentation sites
  - Example: Scrape GitHub's best practices guide
  
- **`mcp_firecrawl-mcp_firecrawl_extract`**: Structured data extraction
  - Best for: Extracting structured information from web pages
  - Example: Extract commit message examples from a style guide

#### Tavily (2 tools)
- **`mcp_tavily-remote-mcp_tavily_search`**: Web search
  - Best for: Fast web searches
  - Example: "Best practices for git commit messages"
  
- **`mcp_tavily-remote-mcp_tavily_extract`**: Content extraction
  - Best for: Extracting content from URLs
  - Example: Extract content from a repository organization guide

### 2. Internal Analysis Tools

BOP can also use its own capabilities:

#### Structured Reasoning
- **Schema-based decomposition**: Break complex analysis into subproblems
- **Synthesis**: Combine multiple analysis perspectives
- **Topology analysis**: Analyze relationships between components

#### Code Analysis
- **File system access**: Read and analyze repository files
- **Pattern recognition**: Identify patterns in code structure
- **Quality metrics**: Evaluate code quality dimensions

#### Git Analysis
- **Commit history parsing**: Analyze git log output
- **Pattern detection**: Identify commit message patterns
- **Statistics**: Compute metrics on commit history

## Meta-Analysis Use Cases

### 1. Repository Structure Analysis

**Query**: "Analyze this repository's structure and suggest improvements"

**Tools Used**:
- File system access (read directory structure)
- Perplexity deep research (best practices)
- Structured reasoning (decompose into: organization, naming, documentation, tests)

**Example**:
```python
response = await agent.chat(
    message="Analyze this repository's structure and suggest improvements",
    use_schema="decompose_and_synthesize",
    use_research=True,  # Uses Perplexity to research best practices
)
```

### 2. Git History Quality Analysis

**Query**: "Analyze git commit history quality and identify issues"

**Tools Used**:
- Git commands (parse commit history)
- Perplexity search (conventional commits format)
- Structured reasoning (analyze: format, scope usage, frequency)

**Example**:
```python
response = await agent.chat(
    message="Analyze git commit history quality",
    use_schema="decompose_and_synthesize",
    use_research=True,  # Researches commit message best practices
)
```

### 3. Configuration Review

**Query**: "Review hookwise configuration and suggest improvements"

**Tools Used**:
- File reading (read config files)
- Perplexity reason (analyze trade-offs)
- Structured reasoning (evaluate: thresholds, rules, checks)

### 4. Code Quality Analysis

**Query**: "Analyze code quality and identify improvement areas"

**Tools Used**:
- File system access (read source files)
- Perplexity deep research (code quality best practices)
- Pattern recognition (identify anti-patterns)

### 5. Documentation Analysis

**Query**: "Review documentation organization and completeness"

**Tools Used**:
- File system access (scan docs directory)
- Perplexity search (documentation best practices)
- Structured reasoning (evaluate: organization, completeness, clarity)

## Enhanced Meta-Analysis Script

See `scripts/analyze_repo_with_bop.py` for a complete example that:

1. Uses BOP's agent to analyze multiple aspects
2. Leverages structured reasoning schemas
3. Optionally uses research tools for best practices
4. Provides progressive disclosure (summary → detailed)

## Tool Selection Strategy

BOP's orchestrator automatically selects tools based on query characteristics:

- **Deep analysis** → `PERPLEXITY_DEEP_RESEARCH`
- **Reasoning questions** → `PERPLEXITY_REASON`
- **Quick lookups** → `PERPLEXITY_SEARCH` + `TAVILY_SEARCH`
- **URL extraction** → `FIRECRAWL_SCRAPE`
- **Structured data** → `FIRECRAWL_EXTRACT`

## Research Integration

When `use_research=True`, BOP will:

1. Decompose the query using a reasoning schema
2. For each subproblem, select appropriate MCP tools
3. Conduct research using selected tools
4. Synthesize results with source citations
5. Provide trust metrics and source credibility

## Example: Full Meta-Analysis

```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent(enable_quality_feedback=True)

# Comprehensive repository analysis with research
response = await agent.chat(
    message="""
    Conduct a comprehensive analysis of this repository:
    1. Repository structure and organization
    2. Git commit history quality
    3. Configuration files (hookwise, etc.)
    4. Code quality patterns
    5. Documentation completeness
    
    Research best practices for each area and compare against
    this repository's current state.
    """,
    use_schema="decompose_and_synthesize",
    use_research=True,  # Enables MCP tool usage
)

# Access results
print(response["response"])  # Full analysis
print(response["response_tiers"]["summary"])  # Quick summary
print(response["research"]["topology"]["trust_summary"])  # Trust metrics
```

## Limitations

- MCP tools require API keys configured in `.env`
- Research adds latency (30s+ for deep research)
- Some tools may have rate limits
- File system access is limited to repository files

## Best Practices

1. **Use research for best practices**: Enable `use_research=True` when you want BOP to research best practices
2. **Use schemas for complex analysis**: `decompose_and_synthesize` breaks complex queries into manageable parts
3. **Progressive disclosure**: Use `response_tiers` to get quick summaries first
4. **Trust metrics**: Check `trust_summary` to evaluate research quality
5. **Source citations**: Review `research["subsolutions"]` for detailed source information

