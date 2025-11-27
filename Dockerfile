FROM python:3.11-slim-bookworm

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# System Deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

# Deps
COPY pyproject.toml .
RUN uv sync --no-install-project

# Code
COPY . .

# Run
CMD ["uv", "run", "python", "-m", "src.main"]