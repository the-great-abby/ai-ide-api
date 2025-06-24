#!/bin/bash
# External Project Worker Setup Script
# Generated on 2025-06-23 09:24:11
# Project: ai-ide-api_internal
# API Base: http://localhost:9103

set -e

echo "🚀 Setting up ai-ide-api_internal workers..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required files exist
if [ ! -f ".apitoken" ]; then
    echo "❌ .apitoken file not found. Please run the onboarding script first."
    exit 1
fi

# Set the API token for workers
export MEMORY_API_TOKEN=$(cat .apitoken)
echo "✅ API token loaded for workers"

# Detect environment
if [ -f /.dockerenv ] || [ "$RUNNING_IN_DOCKER" = "1" ]; then
    echo "🐳 Detected: Running inside Docker container"
    echo "   Workers will use host.docker.internal for API access"
else
    echo "🖥️  Detected: Running on host machine"
    echo "   Workers will use localhost for API access"
fi

echo "🌐 API Configuration:"
echo "   API Base: http://localhost:9103"
echo ""

# Create worker directory if it doesn't exist
mkdir -p worker

# Copy worker files if they don't exist
if [ ! -f "worker/Dockerfile" ]; then
    echo "📋 Creating worker Dockerfile..."
    cat > worker/Dockerfile << 'EOF'
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run worker
CMD ["python", "worker/main.py"]
EOF
fi

if [ ! -f "worker/requirements.txt" ]; then
    echo "📋 Creating worker requirements.txt..."
    cat > worker/requirements.txt << 'EOF'
requests>=2.31.0
aio-pika>=9.3.0
asyncio-mqtt>=0.16.0
psycopg2-binary>=2.9.7
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
fastapi>=0.100.0
structlog>=23.0.0
EOF
fi

# Start the services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.external.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if docker-compose -f docker-compose.external.yml ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📊 Service Status:"
    docker-compose -f docker-compose.external.yml ps
    echo ""
    echo "🌐 RabbitMQ Management UI: http://localhost:15672"
    echo "   Username: user"
    echo "   Password: password"
    echo ""
    echo "🔗 API Connections:"
    echo "   AI-IDE-API: http://localhost:9103"
    echo ""
    echo "📝 To view logs:"
    echo "   docker-compose -f docker-compose.external.yml logs -f worker"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose -f docker-compose.external.yml down"
else
    echo "❌ Services failed to start properly."
    echo "Check logs with: docker-compose -f docker-compose.external.yml logs"
    exit 1
fi
