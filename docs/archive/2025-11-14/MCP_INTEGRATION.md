# MCP Integration Guide

## Overview

BOP is designed to integrate with MCP (Model Context Protocol) tools for deep research capabilities. The current implementation provides hooks for MCP integration.

## Available MCP Tools

The following MCP tools are available for integration:

### Perplexity Deep Research
- `mcp_perplexity_deep_research` - Comprehensive research using Perplexity's Sonar Deep Research model
- `mcp_perplexity_reason` - Complex reasoning tasks
- `mcp_perplexity_search` - Quick search queries

### Firecrawl
- `mcp_firecrawl-mcp_firecrawl_search` - Web search
- `mcp_firecrawl-mcp_firecrawl_scrape` - Single page scraping
- `mcp_firecrawl-mcp_firecrawl_crawl` - Multi-page crawling
- `mcp_firecrawl-mcp_firecrawl_extract` - Structured data extraction

### Tavily
- `mcp_tavily-remote-mcp_tavily_search` - Web search
- `mcp_tavily-remote-mcp_tavily_extract` - Content extraction
- `mcp_tavily-remote-mcp_tavily_crawl` - Website crawling

## Integration Points

### Research Agent

The `ResearchAgent` class in `src/bop/research.py` is designed to integrate MCP tools:

```python
def deep_research(
    self,
    query: str,
    focus_areas: Optional[List[str]] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    # Integration point for mcp_perplexity_deep_research
    pass
```

### Implementation Example

To integrate MCP tools, modify `research.py`:

```python
# Example integration with Perplexity
def deep_research(self, query: str, focus_areas: Optional[List[str]] = None):
    # Call MCP tool
    result = mcp_perplexity_deep_research(
        query=query,
        focus_areas=focus_areas or [],
    )
    return {
        "query": query,
        "summary": result.summary,
        "sources": result.sources,
        "mcp_used": True,
    }
```

## Configuration

MCP tools typically require API keys. Configure them in `.env`:

```bash
PERPLEXITY_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

## Future Enhancements

- [ ] Direct MCP tool integration in `research.py`
- [ ] Automatic tool selection based on query type
- [ ] Result caching and deduplication
- [ ] Multi-tool research synthesis

