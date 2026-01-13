"""Tests for MCP tool integration."""

import pytest

from bop.mcp_tools import TOOL_PARAM_MAP, call_mcp_tool


@pytest.mark.asyncio
async def test_call_mcp_tool_valid():
    """Test calling MCP tool with valid parameters."""
    result = await call_mcp_tool("mcp_perplexity_search", query="test query")

    assert "tool" in result
    assert result["tool"] == "mcp_perplexity_search"
    assert "args" in result
    assert result["args"]["query"] == "test query"


@pytest.mark.asyncio
async def test_call_mcp_tool_missing_required():
    """Test calling MCP tool with missing required parameters."""
    result = await call_mcp_tool("mcp_perplexity_search")

    assert "error" in result
    assert "Missing required parameters" in result["error"]
    assert "required" in result


@pytest.mark.asyncio
async def test_call_mcp_tool_unknown_tool():
    """Test calling unknown MCP tool."""
    result = await call_mcp_tool("unknown_tool", query="test")

    assert "error" in result
    assert "Unknown MCP tool" in result["error"]


@pytest.mark.asyncio
async def test_call_mcp_tool_with_optional_params():
    """Test calling MCP tool with optional parameters."""
    result = await call_mcp_tool(
        "mcp_perplexity_deep_research",
        query="test",
        focus_areas=["area1", "area2"]
    )

    assert "tool" in result
    assert "args" in result
    assert "focus_areas" in result["args"]


@pytest.mark.asyncio
async def test_call_mcp_tool_filters_extra_params():
    """Test that extra parameters are filtered out."""
    result = await call_mcp_tool(
        "mcp_perplexity_search",
        query="test",
        max_results=5,
        extra_param="should be filtered"
    )

    assert "args" in result
    assert "query" in result["args"]
    assert "max_results" in result["args"]
    assert "extra_param" not in result["args"]


@pytest.mark.asyncio
async def test_all_tool_param_mappings():
    """Test that all tools in TOOL_PARAM_MAP can be called."""
    for tool_name in TOOL_PARAM_MAP:
        param_spec = TOOL_PARAM_MAP[tool_name]
        # Create minimal valid kwargs
        kwargs = {param: "test" for param in param_spec["required"]}

        result = await call_mcp_tool(tool_name, **kwargs)

        assert "tool" in result
        assert result["tool"] == tool_name
        # Should not have parameter errors
        assert "error" not in result or "Missing required" not in result.get("error", "")


@pytest.mark.asyncio
async def test_firecrawl_scrape_url_detection():
    """Test that Firecrawl scrape handles URL parameter correctly."""
    result = await call_mcp_tool("mcp_firecrawl-mcp_firecrawl_scrape", url="https://example.com")

    assert "tool" in result
    assert "args" in result
    assert result["args"]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_firecrawl_extract_urls_list():
    """Test that Firecrawl extract handles URLs list."""
    urls = ["https://example.com", "https://test.com"]
    result = await call_mcp_tool("mcp_firecrawl-mcp_firecrawl_extract", urls=urls)

    assert "tool" in result
    assert "args" in result
    assert result["args"]["urls"] == urls


@pytest.mark.asyncio
async def test_tavily_extract_urls_list():
    """Test that Tavily extract handles URLs list."""
    urls = ["https://example.com"]
    result = await call_mcp_tool("mcp_tavily-remote-mcp_tavily_extract", urls=urls)

    assert "tool" in result
    assert "args" in result
    assert isinstance(result["args"]["urls"], list)

