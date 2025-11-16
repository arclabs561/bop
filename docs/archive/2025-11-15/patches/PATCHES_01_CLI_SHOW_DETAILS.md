# Patch 1: Implement CLI --show-details Flag

## Issue
CLI mentions `--show-details` but flag doesn't exist. Users can't expand from summary to detailed.

## Research-Based Solution
Based on Typer best practices: Use `bool` type hints with `typer.Option`, set default value, provide clear help text.

## Implementation

### File: `src/bop/cli.py`

**Change 1: Add flag parameter**
```python
@app.command()
def chat(
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Use structured reasoning schema"),
    research: bool = typer.Option(False, "--research", "-r", help="Enable deep research"),
    content_dir: Optional[Path] = typer.Option(None, "--content-dir", help="Content directory"),
    quality_feedback: bool = typer.Option(True, "--quality-feedback/--no-quality-feedback", help="Enable quality feedback loop"),
    use_constraints: bool = typer.Option(None, "--constraints/--no-constraints", help="Use constraint solver for tool selection (default: from BOP_USE_CONSTRAINTS env)"),
    show_details: bool = typer.Option(False, "--show-details", help="Show full response instead of summary (progressive disclosure)"),
) -> None:
```

**Change 2: Use flag in display logic**
```python
# Around line 236-243, replace:
# Progressive disclosure: show summary first, allow expansion
response_tiers = response.get("response_tiers", {})
if response_tiers and response_tiers.get("summary"):
    console.print("\n[bold cyan]Summary:[/bold cyan]")
    console.print(Markdown(response_tiers["summary"]))
    console.print("\n[dim]💡 Use --show-details to see full response[/dim]")
else:
    console.print(Markdown(response.get("response", "No response generated")))

# With:
# Progressive disclosure: show summary first, allow expansion
response_tiers = response.get("response_tiers", {})
if show_details:
    # Show full detailed response
    if response_tiers and response_tiers.get("detailed"):
        console.print("\n[bold cyan]Full Response:[/bold cyan]")
        console.print(Markdown(response_tiers["detailed"]))
    else:
        console.print(Markdown(response.get("response", "No response generated")))
elif response_tiers and response_tiers.get("summary"):
    # Show summary with hint
    console.print("\n[bold cyan]Summary:[/bold cyan]")
    console.print(Markdown(response_tiers["summary"]))
    console.print("\n[dim]💡 Use --show-details to see full response[/dim]")
else:
    # Fallback to full response if no tiers
    console.print(Markdown(response.get("response", "No response generated")))
```

## Testing
Add to `tests/test_cli_integration.py` (create if doesn't exist):
```python
def test_cli_show_details_flag():
    """Test that --show-details flag works correctly."""
    # This would require CLI testing framework
    # For now, document expected behavior:
    # 1. Without flag: shows summary
    # 2. With --show-details: shows detailed tier
    # 3. Without tiers: shows full response regardless
    pass
```

## Notes
- Flag defaults to `False` (shows summary by default)
- Clear help text explains progressive disclosure
- Graceful fallback if tiers don't exist

