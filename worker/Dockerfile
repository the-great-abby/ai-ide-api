# External Project Worker Dockerfile
# Generated on 2025-06-23 09:24:11
# Project: ai-ide-api_internal

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY worker/ ./worker/
COPY utils/ ./utils/
COPY scripts/ ./scripts/
COPY misc_scripts/ ./misc_scripts/

# Set environment variables
ENV PYTHONPATH=/app:/app/scripts:/code
ENV RUNNING_IN_DOCKER=1
ENV PROJECT_NAME=ai-ide-api_internal

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run worker
CMD ["python", "worker/main.py"]
