# bop

Research agent CLI. Agents bop around exploring and synthesizing.

## Install

```bash
cargo install --path bop-cli
```

## Usage

```bash
# Single query
bop query "What causes aurora borealis?"

# Research (multi-step)
bop research "transformer architectures" -o notes.md

# Interactive chat (with readline, history)
bop chat

# Session management
bop session list
bop session show <id>

# JSON output for scripting
bop --json query "capital of France"

# Shell completions
bop completions zsh >> ~/.zshrc
```

## Configuration

Set API keys via environment or `.env` file:

```bash
export ANTHROPIC_API_KEY='...'
# or
export OPENAI_API_KEY='...'
```

bop searches for `.env` in: current dir, parent dirs, `~/.bop/.env`, repo root.

## Providers

```bash
bop query "..."                 # auto-detect from available keys
bop query -p openrouter "..."   # OpenRouter (unified API)
bop query -p anthropic "..."    # Anthropic Claude
bop query -p openai "..."       # OpenAI GPT
bop query -p local "..."        # Ollama (localhost:11434)
```

Auto-detection priority: `OPENROUTER_API_KEY` > `ANTHROPIC_API_KEY` > `OPENAI_API_KEY`

### OpenRouter Models

```bash
bop query -p openrouter -m anthropic/claude-sonnet-4 "..."
bop query -p openrouter -m openai/gpt-4o "..."
bop query -p openrouter -m meta-llama/llama-3.1-70b-instruct "..."
```

## TUI (optional)

```bash
cargo install --path bop-cli --features tui
bop tui
```

## Architecture

```
bop-core/    Core agent, LLM, MCP, session
bop-cli/     CLI binary
```

Part of the Scholar Stack: hop (ingestion) + bop (agents).
