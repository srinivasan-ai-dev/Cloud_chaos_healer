# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# Multi-stage build for Cloud Chaos Healer
ARG BASE_IMAGE=ghcr.io/meta-pytorch/openenv-base:latest
FROM ${BASE_IMAGE} AS builder

WORKDIR /app

# Install git for dependency resolution from VCS
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Build arguments for environment identification
ARG BUILD_MODE=standalone
ARG ENV_NAME=cc_healer

# Copy environment code to the builder stage
COPY . /app/env

WORKDIR /app/env

# Ensure the 'uv' package manager is available for optimized build
RUN if ! command -v uv >/dev/null 2>&1; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh && \
        mv /root/.local/bin/uv /usr/local/bin/uv && \
        mv /root/.local/bin/uvx /usr/local/bin/uvx; \
    fi

# Install dependencies into a virtual environment using caching to save time/resources
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project --no-editable; \
    else \
        uv sync --no-install-project --no-editable; \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-editable; \
    else \
        uv sync --no-editable; \
    fi

# --- Final Runtime Stage ---
FROM ${BASE_IMAGE}

WORKDIR /app

# Transfer the optimized virtual environment
COPY --from=builder /app/env/.venv /app/.venv

# Copy the environment source code
COPY --from=builder /app/env /app/env

# Set environment variables for clean pathing
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"

# Health check to satisfy the Hugging Face Space liveness probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Expose the standard Hugging Face Space port
EXPOSE 7860

# Start the SRE simulation server
CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 7860"]