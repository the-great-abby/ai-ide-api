#!/usr/bin/env python3
"""
Generate Docker Compose file for external projects

This script generates a Docker Compose file for external projects that includes:
- RabbitMQ for message queuing
- Worker containers for background processing
- Proper networking to connect to the AI-IDE-API

Usage:
    python scripts/generate_external_docker_compose.py --project-name <name> --output <filename>
    python scripts/generate_external_docker_compose.py --help
"""

import argparse
import os
import sys
from datetime import datetime

def generate_docker_compose(project_name: str, api_base: str = "http://localhost:9103", output_file: str = "docker-compose.external.yml") -> str:
    """Generate a Docker Compose file for external project workers."""
    
    # Sanitize project name for Docker network
    network_name = f"{project_name}-memory-rabbitmq"
    
    # Extract host and port from API base URL for container networking
    if api_base.startswith("http://"):
        api_host_port = api_base[7:]  # Remove "http://"
    elif api_base.startswith("https://"):
        api_host_port = api_base[8:]  # Remove "https://"
    else:
        api_host_port = api_base
    
    # For container-to-host communication, use host.docker.internal
    if "localhost" in api_host_port or "127.0.0.1" in api_host_port:
        container_api_url = api_host_port.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
    else:
        # For remote APIs, use the original host
        container_api_url = api_host_port
    
    docker_compose_content = f'''# External Project Docker Compose for AI IDE API Workers
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}
# API Base: {api_base}
# Container API URL: {container_api_url}

version: '3.8'

services:
  # RabbitMQ for message queuing
  rabbitmq:
    image: rabbitmq:3-management
    container_name: {project_name}-rabbitmq
    ports:
      - "5672:5672"      # AMQP
      - "15672:15672"    # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: user
      RABBITMQ_DEFAULT_PASS: password
    networks:
      - {network_name}
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Worker for background processing
  worker:
    build:
      context: .
      dockerfile: worker/Dockerfile
    container_name: {project_name}-worker
    environment:
      - RUNNING_IN_DOCKER=1
      - RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
      - MEMORY_API_URL=http://{container_api_url}/memory
      - API_BASE_URL=http://{container_api_url}
      - MEMORY_API_TOKEN
      - PYTHONPATH=/app:/app/scripts:/code
      - PROJECT_NAME={project_name}
    depends_on:
      rabbitmq:
        condition: service_healthy
    networks:
      - {network_name}
    volumes:
      - ./worker:/app/worker
      - ./utils:/app/utils
      - ./scripts:/app/scripts
      - ./misc_scripts:/app/misc_scripts
      - .:/code
      - ./.git:/code/.git
      - ./.apitoken:/code/.apitoken
      - ./.api_admin_token:/code/.api_admin_token
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for caching (if needed)
  redis:
    image: redis:7-alpine
    container_name: {project_name}-redis
    ports:
      - "6379:6379"
    networks:
      - {network_name}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  {network_name}:
    driver: bridge
    name: {network_name}

volumes:
  {project_name}_rabbitmq_data:
    driver: local
  {project_name}_redis_data:
    driver: local
'''
    
    return docker_compose_content

def generate_worker_dockerfile(project_name: str, output_file: str = "worker/Dockerfile.external") -> str:
    """Generate a Dockerfile for the external worker."""
    
    dockerfile_content = f'''# External Project Worker Dockerfile
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
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
ENV PROJECT_NAME={project_name}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Run worker
CMD ["python", "worker/main.py"]
'''
    
    return dockerfile_content

def generate_worker_requirements(output_file: str = "worker/requirements.external.txt") -> str:
    """Generate requirements.txt for the external worker."""
    
    requirements_content = '''# External Worker Requirements
# Generated for AI IDE API worker

# Core dependencies
requests>=2.31.0
aio-pika>=9.3.0
asyncio-mqtt>=0.16.0

# Database
psycopg2-binary>=2.9.7
sqlalchemy>=2.0.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
fastapi>=0.100.0

# Logging
structlog>=23.0.0

# Optional: Add any project-specific dependencies here
'''
    
    return requirements_content

def generate_setup_script(project_name: str, api_base: str = "http://localhost:9103", output_file: str = "setup-workers.sh") -> str:
    """Generate a setup script for the external workers."""
    
    setup_script_content = f'''#!/bin/bash
# External Project Worker Setup Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}
# API Base: {api_base}

set -e

echo "🚀 Setting up {project_name} workers..."

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
echo "   API Base: {api_base}"
echo ""

# Create worker directory if it doesn't exist
mkdir -p worker

# Copy worker files if they don't exist
if [ ! -f "worker/Dockerfile" ]; then
    echo "📋 Creating worker Dockerfile..."
    cat > worker/Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
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
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
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
    echo "   AI-IDE-API: {api_base}"
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
'''
    
    return setup_script_content

def generate_external_worker_main(project_name: str, output_file: str = "worker/main.py") -> str:
    """Generate a modified worker main.py for external projects."""
    
    worker_main_content = f'''#!/usr/bin/env python3
# External Project Worker Main
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project_name}
# Note: External workers use API endpoints instead of direct Ollama Functions access

print('=== EXTERNAL WORKER MAIN.PY EXECUTING ===')
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('worker').info('=== EXTERNAL WORKER MAIN.PY EXECUTING ===')

import json
import os
import time
import asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase
import requests

# Import worker modules (these should be copied from the main project)
try:
    from worker.progress_report_worker import process_progress_report_job
    from scripts.memory_cleanup_worker import process_memory_cleanup_job
    from scripts.memory_enrichment_worker import process_enrichment_job
    from scripts.memory_similarity_pruning_worker import process_similarity_pruning_job
    from scripts.git_history_worker import process_git_history_analysis_job
except ImportError as e:
    print(f"Warning: Could not import worker modules: {{e}}")
    print("Some worker functionality may not be available")

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:9103")
MEMORY_API_TOKEN = os.environ.get("MEMORY_API_TOKEN", "")

PROGRESS_QUEUE = "progress.report"
MEMORY_CLEANUP_QUEUE = "memory.cleanup"
MEMORY_ENRICHMENT_QUEUE = "memory.enrichment"
MEMORY_SIMILARITY_QUEUE = "memory.similarity"
GIT_HISTORY_QUEUE = "git.history.analysis"
MEMORY_UPDATE_QUEUE = "memory.update"

logger = logging.getLogger("external_worker")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# External workers can now process git diff summarization via API
async def process_git_diff_job(body):
    """Process git diff summarization using the API endpoint."""
    if "diff" not in body:
        logger.info("No 'diff' field found in job")
        return {{"status": "error", "reason": "missing_diff_field"}}
    
    concise = body.get("concise", True)
    payload = {{"diff": body["diff"], "concise": concise}}
    
    try:
        # Use the API endpoint instead of direct Ollama Functions access
        headers = {{"Authorization": f"Bearer {{MEMORY_API_TOKEN}}", "Content-Type": "application/json"}}
        response = requests.post(
            f"{{API_BASE_URL}}/summarize-git-diff", 
            json=payload, 
            headers=headers,
            timeout=180
        )
        response.raise_for_status()
        summary = response.json()
        logger.info("Git diff summary response: %s", json.dumps(summary, indent=2))
        return {{"status": "success", "summary": summary}}
    except Exception as e:
        logger.error("Error calling git diff summarization API: %s", e)
        return {{"status": "error", "reason": str(e)}}

# Available job handlers for external workers (now including git diff summarization)
JOB_HANDLERS = {{
    MEMORY_UPDATE_QUEUE: process_git_diff_job,  # Now available via API
    PROGRESS_QUEUE: process_progress_report_job,
    MEMORY_CLEANUP_QUEUE: process_memory_cleanup_job,
    MEMORY_ENRICHMENT_QUEUE: process_enrichment_job,
    MEMORY_SIMILARITY_QUEUE: process_similarity_pruning_job,
    GIT_HISTORY_QUEUE: process_git_history_analysis_job,
}}

async def main(broker: MessageBrokerBase = None):
    logger.info("=== EXTERNAL WORKER STARTING ===")
    logger.info(f"Available job handlers: {{list(JOB_HANDLERS.keys())}}")
    logger.info("✅ Git diff summarization available via API endpoint")
    logger.info(f"API Base URL: {{API_BASE_URL}}")

    if broker is None:
        logger.info("Creating new RabbitMQ client...")
        broker = RealRabbitMQClient(RABBITMQ_URL)

    logger.info(f"Broker instance type: {{type(broker).__name__}}")
    logger.info("External worker started, polling for jobs...")
    print("External worker started, polling for jobs...")

    while True:
        for queue_name, handler in JOB_HANDLERS.items():
            logger.debug(f"About to poll queue: {{queue_name}}")
            try:
                # Consume from queue
                body = await broker.consume(queue_name)
                logger.debug(f"Polled queue {{queue_name}}, got body: {{body}}")
                
                if body is None:
                    logger.debug(f"No message in queue {{queue_name}}, sleeping...")
                    await asyncio.sleep(1)
                    continue
                
                # Parse job data
                try:
                    if isinstance(body, str):
                        job_data = json.loads(body)
                    else:
                        job_data = body
                    logger.info(f"🎯 Processing job from queue {{queue_name}}: {{job_data}}")
                    print(f"=== JOB DEQUEUED FROM {{queue_name}} ===")
                    
                    # Call handler
                    logger.info(f"🚀 Calling handler for {{queue_name}}")
                    result = await handler(job_data)
                    logger.info(f"✅ Handler for {{queue_name}} completed: {{result}}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse job data from {{queue_name}}: {{e}}")
                    logger.error(f"Raw body: {{body}}")
                except Exception as e:
                    logger.error(f"❌ Handler error for {{queue_name}}: {{e}}")
                    
            except Exception as e:
                logger.error(f"❌ Error polling queue {{queue_name}}: {{e}}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return worker_main_content

def main():
    parser = argparse.ArgumentParser(description="Generate Docker Compose files for external projects")
    parser.add_argument("--project-name", required=True, help="Name of the external project")
    parser.add_argument("--output-dir", default=".", help="Output directory for generated files")
    parser.add_argument("--api-base", default="http://localhost:9103", help="API base URL for workers to connect to")
    parser.add_argument("--docker-compose", default="docker-compose.external.yml", help="Docker Compose output filename")
    parser.add_argument("--worker-dockerfile", default="worker/Dockerfile", help="Worker Dockerfile output filename")
    parser.add_argument("--worker-requirements", default="worker/requirements.txt", help="Worker requirements output filename")
    parser.add_argument("--setup-script", default="setup-workers.sh", help="Setup script output filename")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "worker"), exist_ok=True)
    
    # Generate files
    docker_compose_content = generate_docker_compose(
        args.project_name, 
        api_base=args.api_base,
        output_file=args.docker_compose
    )
    worker_dockerfile_content = generate_worker_dockerfile(args.project_name, args.worker_dockerfile)
    worker_requirements_content = generate_worker_requirements(args.worker_requirements)
    setup_script_content = generate_setup_script(
        args.project_name,
        api_base=args.api_base,
        output_file=args.setup_script
    )
    worker_main_content = generate_external_worker_main(args.project_name, args.worker_dockerfile)
    
    # Write files
    docker_compose_path = os.path.join(args.output_dir, args.docker_compose)
    with open(docker_compose_path, 'w') as f:
        f.write(docker_compose_content)
    
    worker_dockerfile_path = os.path.join(args.output_dir, args.worker_dockerfile)
    with open(worker_dockerfile_path, 'w') as f:
        f.write(worker_dockerfile_content)
    
    worker_requirements_path = os.path.join(args.output_dir, args.worker_requirements)
    with open(worker_requirements_path, 'w') as f:
        f.write(worker_requirements_content)
    
    setup_script_path = os.path.join(args.output_dir, args.setup_script)
    with open(setup_script_path, 'w') as f:
        f.write(setup_script_content)
    
    worker_main_path = os.path.join(args.output_dir, "worker/main.py")
    with open(worker_main_path, 'w') as f:
        f.write(worker_main_content)
    
    # Make setup script executable
    os.chmod(setup_script_path, 0o755)
    
    print(f"✅ Generated external project files for '{args.project_name}':")
    print(f"   📄 {docker_compose_path}")
    print(f"   📄 {worker_dockerfile_path}")
    print(f"   📄 {worker_requirements_path}")
    print(f"   📄 {setup_script_path}")
    print(f"   📄 {worker_main_path}")
    print()
    print("🚀 To set up workers:")
    print(f"   cd {args.output_dir}")
    print(f"   ./{args.setup_script}")
    print()
    print("📋 The generated files include:")
    print("   • Docker Compose with RabbitMQ and worker services")
    print("   • Worker Dockerfile for background processing")
    print("   • Requirements file for Python dependencies")
    print("   • Setup script to start everything")
    print("   • Worker main.py for external project")
    print()
    print(f"🌐 Workers will connect to AI-IDE-API at {args.api_base}")

if __name__ == "__main__":
    main() 