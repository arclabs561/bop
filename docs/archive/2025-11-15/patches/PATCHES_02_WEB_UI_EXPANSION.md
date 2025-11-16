# Patch 2: Implement Web UI Expansion

## Issue
Web UI shows expand link but it doesn't work. No click handler, no state management.

## Research-Based Solution
Based on Marimo best practices: Use reactive execution with UI elements (checkbox/button), leverage `on_change` callbacks sparingly, use accordion for expandable content.

## Implementation

### File: `src/bop/web.py`

**Change 1: Add expansion state to message structure**
```python
# Around line 118-128, modify message storage:
messages.value[thinking_id] = {
    "role": "assistant",
    "content": formatted_response,
    "thinking": False,
    "quality_score": quality_score,
    "research_conducted": response.get("research_conducted", False),
    "schema_used": response.get("schema_used"),
    "response_tiers": response_tiers,  # Store tiers for expansion
    "full_response": response.get("response", ""),  # Store full response
    "expanded": False,  # NEW: Track expansion state
    "timestamp": asyncio.get_event_loop().time(),
}
```

**Change 2: Use accordion for progressive disclosure**
```python
# Replace the expand link approach (around line 93-99) with accordion:
# Use progressive disclosure: show summary first, allow expansion
response_tiers = response.get("response_tiers", {})
if response_tiers and response_tiers.get("summary"):
    # Use accordion for expandable content
    import marimo as mo
    response_text = mo.accordion({
        "Summary": mo.md(response_tiers["summary"]),
        "Detailed": mo.md(response_tiers.get("detailed", response.get("response", ""))),
        "Evidence": mo.md(response_tiers.get("evidence", "")) if response_tiers.get("evidence") else None,
    })
    # Remove None values
    accordion_dict = {k: v for k, v in response_text.items() if v is not None}
    response_text = mo.accordion(accordion_dict)
else:
    response_text = response.get("response", "No response generated.")
```

**Alternative: Reactive checkbox approach (if accordion doesn't work)**
```python
# Create expansion checkbox per message
# This requires restructuring to use reactive cells
# For now, simpler approach: use button with on_change

# In send_message function, after storing message:
# Add expansion button to message
expand_button = ui.button(
    label="Show Details",
    on_change=lambda _: expand_message(thinking_id)
)

# Add expand_message function:
def expand_message(message_id: int):
    """Toggle expansion state for a message."""
    if message_id < len(messages.value):
        msg = messages.value[message_id]
        msg["expanded"] = not msg.get("expanded", False)
        # Update display
        update_message_display(message_id)
```

**Change 3: Update display logic to respect expansion state**
```python
# In update_chat_display function (around line 148-178):
def update_chat_display():
    """Update chat display with messages."""
    if not messages.value:
        chat_display.value = "**Welcome to BOP**\n\nAsk me anything about knowledge structures, reasoning, or research."
        return
    
    chat_html = []
    for i, msg in enumerate(messages.value):
        if msg["role"] == "user":
            chat_html.append(f"### You\n{msg['content']}\n")
        else:
            if msg.get("thinking"):
                chat_html.append(f"### BOP\n*Thinking...*\n")
            elif msg.get("error"):
                chat_html.append(f"### BOP\n❌ {msg['content']}\n")
            else:
                # Progressive disclosure based on expansion state
                response_tiers = msg.get("response_tiers", {})
                if msg.get("expanded") and response_tiers:
                    # Show detailed tier
                    content = response_tiers.get("detailed", msg.get("full_response", msg["content"]))
                elif response_tiers and response_tiers.get("summary"):
                    # Show summary with expand option
                    content = response_tiers["summary"]
                    content += "\n\n*[Click to expand](#expand-{})*".format(i)
                else:
                    content = msg["content"]
                
                metadata = []
                if msg.get("research_conducted"):
                    metadata.append("🔍 Research")
                if msg.get("schema_used"):
                    metadata.append(f"📋 {msg['schema_used']}")
                if msg.get("quality_score"):
                    metadata.append(f"⭐ {msg['quality_score']:.2f}")
                
                if metadata:
                    content += f"\n\n*{' • '.join(metadata)}*"
                
                chat_html.append(f"### BOP\n{content}\n")
    
    chat_display.value = "\n".join(chat_html)
```

## Testing
Add to `tests/test_web_ui_integration.py` (create if doesn't exist):
```python
def test_web_ui_expansion():
    """Test that expansion works in web UI."""
    # Test that:
    # 1. Summary is shown by default
    # 2. Expansion button toggles state
    # 3. Detailed tier shown when expanded
    # 4. State persists across updates
    pass
```

## Notes
- Accordion is preferred (built-in expandable component)
- Fallback to reactive checkbox if accordion doesn't work
- State stored in message object
- Graceful fallback if tiers don't exist

