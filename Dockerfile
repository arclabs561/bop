# BOP - Agentic Research and Orchestration
# Multi-stage build for lean production image

# ============================================================
# Stage 1: Rust Builder
# ============================================================
FROM rust:1.85-slim-bookworm AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace files
COPY . .

# Build BOP CLI
RUN cargo build --release -p pran-cli

# ============================================================
# Stage 2: Runtime Image
# ============================================================
FROM debian:bookworm-slim AS runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /build/target/release/pran /usr/local/bin/pran

# Create data directory
RUN mkdir -p /data && chmod 755 /data

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash agent && \
    chown -R agent:agent /app /data

USER agent

# Default: show version
CMD ["pran", "--version"]
