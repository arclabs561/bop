# Quick Start Guide

## Installation

```bash
# Install dependencies
uv sync

# Or with dev dependencies
uv sync --dev
```

## Basic Usage

### Interactive Chat

Start an interactive chat session:

```bash
uv run bop chat
```

Commands available in chat:
- `help` - Show available commands
- `schemas` - List reasoning schemas
- `schema <name>` - Use a specific schema
- `research on/off` - Toggle research mode
- `history` - Show conversation history
- `clear` - Clear history
- `exit` - Quit chat

### List Schemas

View all available structured reasoning schemas:

```bash
uv run bop schemas
```

### Deep Research

Conduct research on a topic:

```bash
uv run bop research "What is structured reasoning?" --focus "LLM reasoning"
```

### Run Evaluations

Run the evaluation framework:

```bash
uv run bop eval
```

## Examples

### Using a Schema

```bash
# Start chat with chain-of-thought schema
uv run bop chat --schema chain_of_thought

# In chat, you can also switch schemas:
> schema iterative_elaboration
```

### Research Mode

```bash
# Start chat with research enabled
uv run bop chat --research

# Or toggle in chat:
> research on
> What are the latest developments in LLM reasoning?
```

## Configuration

Create a `.env` file for API keys (see `.env.example`):

```bash
PERPLEXITY_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Project Structure

- `src/bop/` - Main package
- `content/` - Knowledge base markdown files
- `tests/` - Test suite

## Next Steps

- Read `README.md` for full documentation
- See `MCP_INTEGRATION.md` for MCP tool integration
- Check `CONTRIBUTING.md` for development guidelines

