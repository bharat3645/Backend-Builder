# Build from the repository root, e.g.:
#   docker build -f core/Dockerfile -t backend-builder-core .
# (docker-compose.yml already does this for you). Building from the repo
# root - rather than from ./core alone - lets this image also bundle
# ../templates, which core/generators/*.py load at runtime.
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY core/requirements.txt ./core/requirements.txt
RUN pip install --no-cache-dir -r core/requirements.txt

# Copy application code, code-generation templates, and DSL examples
COPY core ./core
COPY templates ./templates
COPY dsl ./dsl

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/core

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "app.py"]
