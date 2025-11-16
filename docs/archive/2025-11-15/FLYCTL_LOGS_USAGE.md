# flyctl logs Usage Guide

## Important: Use --no-tail to Avoid Hanging

The `flyctl logs` command **streams logs by default**, which means it will hang and wait for new log entries forever. Always use `--no-tail` for non-interactive use.

## Correct Usage

### ✅ Good: Non-Streaming (Returns Immediately)
```bash
# Get recent logs and exit
flyctl logs -a bop-wispy-voice-3017 --no-tail

# Get last 50 lines
flyctl logs -a bop-wispy-voice-3017 --no-tail | tail -50

# Search for specific text
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale
```

### ❌ Bad: Streaming (Hangs Forever)
```bash
# This will hang and stream logs forever
flyctl logs -a bop-wispy-voice-3017

# This will also hang
flyctl logs -a bop-wispy-voice-3017 | grep something
```

## Common Patterns

### Get Recent Logs
```bash
# Last 30 lines
flyctl logs -a bop-wispy-voice-3017 --no-tail | tail -30
```

### Search Logs
```bash
# Search for errors
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i error

# Search for Tailscale
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale

# Search for startup
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i start
```

### Follow Logs (Interactive)
```bash
# Only use this in interactive terminal (Ctrl+C to exit)
flyctl logs -a bop-wispy-voice-3017 -f

# Or with grep (still streams)
flyctl logs -a bop-wispy-voice-3017 -f | grep -i error
```

## Command Options

- `--no-tail`: Get recent logs and exit (don't stream)
- `-f` or `--follow`: Stream logs (use only interactively)
- No flag: Streams by default (hangs in scripts)

## Best Practices

1. **In scripts**: Always use `--no-tail`
2. **For searching**: Use `--no-tail | grep`
3. **For monitoring**: Use `-f` in interactive terminal only
4. **For CI/CD**: Always use `--no-tail` with timeout

## Examples in This Project

All log commands in scripts and documentation should use `--no-tail`:

```bash
# ✅ Correct
flyctl logs -a bop-wispy-voice-3017 --no-tail | grep -i tailscale

# ❌ Wrong (will hang)
flyctl logs -a bop-wispy-voice-3017 | grep -i tailscale
```

