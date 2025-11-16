#!/bin/bash
# Setup script to export .env for hookwise CLI usage
# Makes API keys available for npx hookwise ask and other CLI commands

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "⚠️  .env file not found at $ENV_FILE"
  exit 1
fi

echo "📄 Loading .env for hookwise CLI usage..."
echo ""

# Load .env and export
set -a
. "$ENV_FILE" 2>/dev/null || {
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      \#*|'') continue ;;
    esac
    export "$line" 2>/dev/null || true
  done < "$ENV_FILE"
}
set +a

# Verify API keys are loaded
if [ -n "$GEMINI_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
  echo "✅ LLM API keys loaded"
  echo ""
  echo "You can now use:"
  echo "  npx hookwise ask 'question'"
  echo "  npx hookwise garden"
  echo ""
  echo "To use in current shell, run:"
  echo "  source $0"
else
  echo "⚠️  No LLM API keys found in .env"
  echo "   Add GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
fi

