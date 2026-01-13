"""Modern web UI for mobile-friendly chat interface."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Template

router = APIRouter()

# Load template from file
TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "chat.html"
_template_content = None


def get_template():
    """Load template content."""
    global _template_content
    if _template_content is None:
        if TEMPLATE_PATH.exists():
            _template_content = TEMPLATE_PATH.read_text()
        else:
            # Fallback minimal template
            _template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>BOP - Knowledge Structure Research Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 1rem; }
        .chat { margin: 1rem 0; }
        .message { padding: 0.5rem; margin: 0.5rem 0; border-radius: 0.5rem; }
        .user { background: #f0f0f0; }
        .assistant { background: #e8f5e9; }
        input { width: 100%; padding: 0.5rem; margin: 0.5rem 0; }
        button { padding: 0.5rem 1rem; background: #10a37f; color: white; border: none; border-radius: 0.25rem; }
    </style>
</head>
<body>
    <h1>🧠 BOP - Knowledge Structure Research Agent</h1>
    <div id="chat"></div>
    <input type="text" id="message" placeholder="Ask me anything...">
    <button onclick="sendMessage()">Send</button>
    <script>
        async function sendMessage() {
            const msg = document.getElementById('message').value;
            const chat = document.getElementById('chat');
            chat.innerHTML += '<div class="message user">' + msg + '</div>';
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg, research: true})
            });
            const data = await res.json();
            chat.innerHTML += '<div class="message assistant">' + data.response + '</div>';
            document.getElementById('message').value = '';
        }
    </script>
</body>
</html>
"""
    return Template(_template_content)


@router.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Serve the main chat interface."""
    template = get_template()
    return HTMLResponse(content=template.render(request=request))


@router.get("/chat", response_class=HTMLResponse)
async def chat_ui_alt(request: Request):
    """Alternative route for chat interface."""
    return await chat_ui(request)

