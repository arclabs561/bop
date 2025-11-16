# MCP Tool Credentials

This project uses credentials from `~/.cursor/mcp.json` for MCP (Model Context Protocol) tools.

## Available MCP Tools

The following tools are configured and available:

### Firecrawl
- **Purpose**: Web scraping and crawling
- **API Key**: Set via `FIRECRAWL_API_KEY` environment variable
- **Usage**: Scraping web pages, extracting content

### Perplexity
- **Purpose**: Deep research and reasoning
- **API Key**: Set via `PERPLEXITY_API_KEY` environment variable
- **Usage**: Deep research queries, reasoning tasks

### Tavily
- **Purpose**: Web search
- **API Key**: Set via `TAVILY_API_KEY` environment variable
- **Usage**: Fast web search queries

### Kagi
- **Purpose**: Web search and summarization
- **API Key**: Set via `KAGI_API_KEY` environment variable
- **Usage**: Search and content summarization

### SerpAPI
- **Purpose**: Google search results
- **API Key**: Set via `SERPAPI_API_KEY` environment variable
- **Usage**: Structured Google search results

### Context7
- **Purpose**: Documentation lookup
- **API Key**: Set via `CONTEXT7_API_KEY` environment variable
- **Usage**: Looking up library documentation

## Configuration

All credentials are automatically loaded from `.env` file, which is populated from `~/.cursor/mcp.json`.

## Speed Optimization

For speed-critical operations:
- Use **Groq** backend for LLM inference (fastest)
- Use **Tavily** for quick web searches
- Use **Perplexity Search** for fast research queries

For quality-critical operations:
- Use **Anthropic Claude** for best reasoning quality
- Use **Perplexity Deep Research** for comprehensive research
- Use **Firecrawl** for detailed web content extraction

