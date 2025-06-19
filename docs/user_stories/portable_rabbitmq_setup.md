# User Story: Portable RabbitMQ Setup for External Projects

## Motivation
As a developer working on external projects, I want to set up a portable RabbitMQ system that can handle background jobs and automated tasks, enabling efficient asynchronous processing and integration with the AI IDE's memory system. This setup allows external teams to build their own bots and helpers that can communicate with our AI IDE API using standardized message formats.

## Actors
- Junior Developers
- External Project Teams
- DevOps Engineers
- CI/CD Systems
- Project Administrators

## Preconditions
- Docker and Docker Compose installed
- Python 3.8+ installed
- Basic understanding of message queues
- Access to the AI IDE API (project admin level tokens)
- Git repository for version control

## Complete Onboarding Workflow 🚀

Before setting up your RabbitMQ workers, you need to initialize your project with the AI IDE API. Here's the complete workflow:

### Step 1: Initialize Your Project

**Option A: Use the External Onboarding Script (Recommended)**
```bash
# Download and run the onboarding script
curl -s http://localhost:9103/scripts/onboard_external.py > onboard_external.py
python onboard_external.py
```

**Option B: Manual Onboarding Initialization**
```bash
# Initialize your project
curl -X POST http://localhost:9103/onboarding/init \
  -H 'Content-Type: application/json' \
  -d '{"project_name": "my-external-project", "journey": "external_project"}'
```

### Step 2: Get Your API Token

After initialization, you'll need an API token for authenticated operations:

```bash
# Generate a token (requires admin access)
curl -X POST http://localhost:9103/admin/generate-token \
  -H 'Content-Type: application/json' \
  -d '{"description": "External project token", "role": "user"}'
```

### Step 3: Test Your Setup

```bash
# Test API connectivity
curl -X GET http://localhost:9103/memory/nodes \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Test onboarding path
curl -X GET http://localhost:9103/onboarding/path/external_project
```

### Step 4: Set Up Your Environment

Create a `.env` file with your configuration:
```bash
# AI IDE API Configuration
AI_IDE_API_URL=http://localhost:9103
MEMORY_API_URL=http://localhost:9103/memory
MEMORY_API_TOKEN=your_token_here

# Project Configuration
PROJECT_NAME=my-external-project

# RabbitMQ Configuration
RABBITMQ_URL=amqp://user:password@localhost:5672/

# Worker Configuration
WORKER_LOG_LEVEL=INFO
WORKER_MAX_RETRIES=3
```

**Now you're ready to set up RabbitMQ! Continue with the steps below.**

## Recent System Updates (June 2025)
- Enhanced memory system with categories and tags
- New git history analysis capabilities
- Improved maintenance scheduling
- Updated API token management
- New queue types for specialized processing

## Step-by-Step Guide

### 1. Project Structure Setup 🏗️

First, create the necessary directory structure:

```bash
mkdir -p my-ai-bots/{workers,scripts,docker,examples}
cd my-ai-bots

# Create initial files
touch docker-compose.yml
touch workers/requirements.txt
touch workers/main.py
touch .env
touch README.md
```

### 2. Set Up Docker Compose 🐳

Create a minimal `docker-compose.yml`:

```yaml
version: "3.8"
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"      # AMQP protocol
      - "15672:15672"    # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-user}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-password}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: ./workers
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-user}:${RABBITMQ_PASS:-password}@rabbitmq:5672/
      - MEMORY_API_URL=${MEMORY_API_URL:-http://localhost:9103/memory}
      - MEMORY_API_TOKEN=${MEMORY_API_TOKEN}
      - AI_IDE_API_URL=${AI_IDE_API_URL:-http://localhost:9103}
    volumes:
      - ./workers:/app
      - ./examples:/app/examples
    depends_on:
      rabbitmq:
        condition: service_healthy
    restart: unless-stopped

volumes:
  rabbitmq_data:
```

### 3. Create Worker Dockerfile 📄

Create `workers/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

CMD ["python", "main.py"]
```

### 4. Set Up Worker Dependencies 📦

Add to `workers/requirements.txt`:

```
pika==1.3.1
requests==2.31.0
python-dotenv==1.0.0
aiohttp==3.8.5
asyncio-mqtt==0.11.1
```

### 5. Create Enhanced Worker 🔧

Create `workers/main.py`:

```python
#!/usr/bin/env python3
"""
Enhanced RabbitMQ Worker for AI IDE Integration
Handles multiple queue types with standardized message formats.
Updated June 2025 with new queue types and enhanced features.
"""

import os
import json
import asyncio
import logging
import pika
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIIDEWorker:
    """
    Worker that processes jobs from AI IDE RabbitMQ queues.
    Supports multiple queue types with standardized message formats.
    """
    
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
        self.memory_api_url = os.getenv("MEMORY_API_URL", "http://localhost:9103/memory")
        self.memory_api_token = os.getenv("MEMORY_API_TOKEN", "")
        self.ai_ide_api_url = os.getenv("AI_IDE_API_URL", "http://localhost:9103")
        
        self.connection = None
        self.channel = None
        
        # Define supported queues and their handlers (Updated June 2025)
        self.queues = {
            "memory.update": self.process_memory_update,
            "memory.cleanup": self.process_memory_cleanup,
            "memory.enrichment": self.process_memory_enrichment,
            "memory.similarity": self.process_memory_similarity,
            "git.history.analysis": self.process_git_history_analysis,
            "progress.report": self.process_progress_report,
            "maintenance": self.process_maintenance_task,
            "background.jobs": self.process_background_job,
        }

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare all queues as durable
            for queue in self.queues.keys():
                self.channel.queue_declare(queue=queue, durable=True)
                logger.info(f"Declared queue: {queue}")
                
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def process_memory_update(self, body: Dict[str, Any]):
        """Process memory update jobs."""
        logger.info(f"Processing memory update: {body}")
        
        # Example: Update memory with new information
        try:
            # Your custom logic here
            content = body.get("content", "")
            meta = body.get("meta", {})
            
            # Example: Send to AI IDE memory API
            if self.memory_api_token:
                await self.send_to_memory_api(content, meta)
                
            logger.info("Memory update processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing memory update: {e}")

    async def process_memory_cleanup(self, body: Dict[str, Any]):
        """Process memory cleanup jobs."""
        logger.info(f"Processing memory cleanup: {body}")
        
        dry_run = body.get("dry_run", True)
        age_days = body.get("age_days", 180)
        
        # Your cleanup logic here
        logger.info(f"Memory cleanup: dry_run={dry_run}, age_days={age_days}")

    async def process_memory_enrichment(self, body: Dict[str, Any]):
        """Process memory enrichment jobs."""
        logger.info(f"Processing memory enrichment: {body}")
        
        scope = body.get("scope", "all")
        dry_run = body.get("dry_run", True)
        
        # Your enrichment logic here
        logger.info(f"Memory enrichment: scope={scope}, dry_run={dry_run}")

    async def process_memory_similarity(self, body: Dict[str, Any]):
        """Process memory similarity pruning jobs."""
        logger.info(f"Processing memory similarity: {body}")
        
        scope = body.get("scope", "all")
        vector_threshold = body.get("vector_similarity_threshold", 0.92)
        content_threshold = body.get("content_similarity_threshold", 0.85)
        
        # Your similarity analysis logic here
        logger.info(f"Memory similarity: scope={scope}, vector_threshold={vector_threshold}")

    async def process_git_history_analysis(self, body: Dict[str, Any]):
        """Process git history analysis jobs."""
        logger.info(f"Processing git history analysis: {body}")
        
        since = body.get("since", "1 week ago")
        max_commits = body.get("max_commits", 20)
        create_memory = body.get("create_memory_node", False)
        memory_namespace = body.get("memory_namespace", "git_history")
        memory_tags = body.get("memory_tags", [])
        
        # Your git analysis logic here
        logger.info(f"Git analysis: since={since}, max_commits={max_commits}, create_memory={create_memory}")

    async def process_progress_report(self, body: Dict[str, Any]):
        """Process progress report jobs."""
        logger.info(f"Processing progress report: {body}")
        
        # Your progress reporting logic here
        pass

    async def process_maintenance_task(self, body: Dict[str, Any]):
        """Process maintenance tasks."""
        logger.info(f"Processing maintenance task: {body}")
        
        task = body.get("task", "")
        args = body.get("args", {})
        
        # Your maintenance logic here
        logger.info(f"Maintenance: task={task}, args={args}")

    async def process_background_job(self, body: Dict[str, Any]):
        """Process general background jobs."""
        logger.info(f"Processing background job: {body}")
        
        # Your custom background job logic here
        pass

    async def send_to_memory_api(self, content: str, meta: Dict[str, Any]):
        """Send data to AI IDE memory API."""
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.memory_api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": content,
                "meta": meta
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.memory_api_url}/nodes",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Memory node created: {result.get('id')}")
                    else:
                        logger.error(f"Failed to create memory node: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending to memory API: {e}")

    def start(self):
        """Start the worker and begin processing messages."""
        try:
            self.connect()
            logger.info("Worker started, waiting for messages...")
            
            # Set up consumers for all queues
            for queue, callback in self.queues.items():
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=lambda ch, method, props, body: asyncio.run(
                        self._handle_message(callback, body)
                    ),
                    auto_ack=True
                )
                logger.info(f"Listening on queue: {queue}")
            
            # Start consuming messages
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Shutting down worker...")
            self._cleanup()
        except Exception as e:
            logger.error(f"Worker error: {e}")
            self._cleanup()

    async def _handle_message(self, callback, body):
        """Handle incoming messages with error handling."""
        try:
            message = json.loads(body)
            await callback(message)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _cleanup(self):
        """Clean up resources."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

if __name__ == "__main__":
    worker = AIIDEWorker()
    worker.start()
```

### 6. Environment Setup 🔐

Create `.env` file:

```bash
# AI IDE API Configuration (from onboarding process)
AI_IDE_API_URL=http://localhost:9103
MEMORY_API_URL=http://localhost:9103/memory
MEMORY_API_TOKEN=your_token_from_onboarding_process

# Project Configuration
PROJECT_NAME=my-external-project

# RabbitMQ Configuration
RABBITMQ_USER=user
RABBITMQ_PASS=password

# Worker Configuration
WORKER_LOG_LEVEL=INFO
WORKER_MAX_RETRIES=3
```

**Note:** The `MEMORY_API_TOKEN` should be obtained from the onboarding process (see "Complete Onboarding Workflow" section above).

### 7. Create Job Publisher Scripts 📤

Create `scripts/publish_job.py`:

```python
#!/usr/bin/env python3
"""
Job Publisher for AI IDE RabbitMQ Integration
Publishes jobs to various queues with standardized message formats.
Updated June 2025 with new queue types and enhanced features.
"""

import pika
import json
import os
import argparse
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class JobPublisher:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
        self.connection = None
        self.channel = None

    def connect(self):
        """Connect to RabbitMQ."""
        parameters = pika.URLParameters(self.rabbitmq_url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def publish_job(self, queue_name: str, message: Dict[str, Any]):
        """Publish a job to the specified queue."""
        try:
            # Declare queue as durable
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Publish message with persistence
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            print(f"✅ Published job to {queue_name}: {json.dumps(message, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error publishing job: {e}")

    def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def main():
    """Example usage of the job publisher."""
    parser = argparse.ArgumentParser(description="Publish jobs to AI IDE RabbitMQ queues")
    parser.add_argument("--queue", required=True, help="Queue name to publish to")
    parser.add_argument("--message", required=True, help="JSON message to publish")
    
    args = parser.parse_args()
    
    try:
        message = json.loads(args.message)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON message: {e}")
        return
    
    publisher = JobPublisher()
    publisher.connect()
    publisher.publish_job(args.queue, message)
    publisher.close()

if __name__ == "__main__":
    main()
```

### 8. Example Job Publishing 📋

Here are examples of how to publish jobs to different queues:

#### Memory Cleanup Job
```bash
python scripts/publish_job.py \
  --queue memory.cleanup \
  --message '{"dry_run": true, "age_days": 180}'
```

#### Git History Analysis Job
```bash
python scripts/publish_job.py \
  --queue git.history.analysis \
  --message '{"since": "1 week ago", "max_commits": 50, "create_memory_node": true, "memory_namespace": "weekly_analysis", "memory_tags": ["weekly", "automated"]}'
```

#### Memory Enrichment Job
```bash
python scripts/publish_job.py \
  --queue memory.enrichment \
  --message '{"scope": "new", "dry_run": false}'
```

#### Memory Similarity Pruning Job
```bash
python scripts/publish_job.py \
  --queue memory.similarity \
  --message '{"scope": "all", "vector_similarity_threshold": 0.95, "content_similarity_threshold": 0.90, "dry_run": true}'
```

#### Progress Report Job
```bash
python scripts/publish_job.py \
  --queue progress.report \
  --message '{"source": "external_worker", "timestamp": "2025-06-01T12:00:00Z"}'
```

### 9. Testing Your Setup 🧪

Create a test script `scripts/test_setup.py`:

```python
#!/usr/bin/env python3
"""
Test script to verify your RabbitMQ setup is working correctly.
"""

import os
import json
import time
from dotenv import load_dotenv
from publish_job import JobPublisher

load_dotenv()

def test_queue_publishing():
    """Test publishing to all queues."""
    publisher = JobPublisher()
    publisher.connect()
    
    test_jobs = {
        "memory.update": {
            "content": "Test memory update from external worker",
            "meta": {"tags": ["test", "external"], "source": "test_script"}
        },
        "memory.cleanup": {
            "dry_run": True,
            "age_days": 30
        },
        "git.history.analysis": {
            "since": "1 day ago",
            "max_commits": 5,
            "create_memory_node": False
        },
        "progress.report": {
            "source": "test_script",
            "timestamp": time.time()
        }
    }
    
    for queue, message in test_jobs.items():
        print(f"Testing queue: {queue}")
        publisher.publish_job(queue, message)
        time.sleep(1)  # Small delay between publishes
    
    publisher.close()
    print("✅ All test jobs published successfully!")

if __name__ == "__main__":
    test_queue_publishing()
```

### 10. Monitoring and Debugging 🔍

#### Check Queue Status
```bash
# Access RabbitMQ Management UI
open http://localhost:15672
# Username: user, Password: password

# Or use command line
docker exec -it your-rabbitmq-container rabbitmqctl list_queues
```

#### View Worker Logs
```bash
docker compose logs -f worker
```

#### Test API Connectivity
```bash
curl -X GET http://localhost:9103/memory/nodes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting 🛠️

### Common Issues

1. **Connection Refused**
   - Check if RabbitMQ container is running
   - Verify port mappings in docker-compose.yml
   - Check firewall settings

2. **Authentication Errors**
   - Verify RABBITMQ_USER and RABBITMQ_PASS in .env
   - Check API token validity
   - Ensure proper Authorization headers

3. **Queue Not Found**
   - Verify queue names match exactly
   - Check if queues are declared as durable
   - Restart worker container

4. **Memory API Errors**
   - Verify MEMORY_API_TOKEN is valid
   - Check API endpoint URL
   - Ensure proper JSON formatting in meta field

### Onboarding-Specific Issues

5. **Onboarding Initialization Fails**
   - Ensure API is running and accessible
   - Check that project_name and journey are non-empty strings
   - Verify the journey name exists in onboarding_paths.json
   - Try manual initialization with curl to see detailed error messages

6. **Token Generation Fails**
   - First token generation doesn't require authentication
   - Subsequent tokens require an admin token in Authorization header
   - Check token description and role are valid
   - Verify API endpoint is correct

7. **Script Download Fails**
   - Check API is running on correct port
   - Verify the script endpoint is accessible
   - Try manual onboarding initialization instead

### Getting Help

- Check the [AI IDE API Documentation](http://localhost:9103/docs)
- Review worker logs for detailed error messages
- Use the troubleshooting section in onboarding docs
- Contact your project administrator for API access issues

## Best Practices 📚

1. **Error Handling**: Always implement proper error handling in your workers
2. **Logging**: Use structured logging for better debugging
3. **Retry Logic**: Implement retry mechanisms for failed jobs
4. **Monitoring**: Set up monitoring for queue depths and worker health
5. **Security**: Keep API tokens secure and rotate them regularly
6. **Testing**: Test your workers thoroughly before deploying to production

## Next Steps 🚀

1. **Customize Workers**: Adapt the worker code to your specific needs
2. **Add New Queues**: Extend the system with custom queue types
3. **Scale Up**: Add multiple worker instances for high throughput
4. **Integrate**: Connect with your existing CI/CD pipelines
5. **Monitor**: Set up comprehensive monitoring and alerting

## Onboarding Initialization

To initialize onboarding for your project, POST to `/onboarding/init`:

- **Endpoint:** `POST /onboarding/init`
- **Payload:**
  - `project_name` (string, required)
  - `journey` (string, required; use onboarding path name)
  - `path` (string, optional, for backward compatibility)
- **Authentication:** Not required for onboarding initialization

### Example (curl):
```bash
curl -X POST http://localhost:9103/onboarding/init \
  -H 'Content-Type: application/json' \
  -d '{"project_name": "my-external-project", "journey": "external_project"}'
```

### Example (Python):
```python
import requests
payload = {"project_name": "my-external-project", "journey": "external_project"}
resp = requests.post("http://localhost:9103/onboarding/init", json=payload)
print(resp.json())
```

---

**Happy coding! 🏴‍☠️**

For more information, see:
- [AI IDE API Documentation](http://localhost:9103/docs)
- [Memory System Guide](../onboarding/MEMORY_SYSTEM.md)
- [External Onboarding Guide](../onboarding/ONBOARDING_EXTERNAL.md) 