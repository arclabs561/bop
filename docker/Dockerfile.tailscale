# BOP Service Dockerfile with Tailscale for Fly.io
FROM python:3.11-slim

# Install system dependencies including Tailscale
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files and source (needed for package discovery)
COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY src/ ./src/

# Install dependencies (including constraint solver)
# Source is needed for hatchling to discover the package
RUN uv sync --frozen --extra constraints --extra llm-all

# Copy content directory
COPY content/ ./content/

# Copy Tailscale startup script
COPY scripts/tailscale-start.sh /usr/local/bin/tailscale-start.sh
RUN chmod +x /usr/local/bin/tailscale-start.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV BOP_USE_CONSTRAINTS=true
ENV PORT=8080

# Expose port (Fly.io uses PORT env var)
EXPOSE 8080

# Health check (uses PORT env var)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "python -c \"import urllib.request, os; urllib.request.urlopen('http://localhost:' + os.getenv('PORT', '8080') + '/health')\""

# Start Tailscale and then the server
CMD ["/usr/local/bin/tailscale-start.sh"]

