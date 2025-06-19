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
        
        # Define supported queues and their handlers
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
        
        # Your enrichment logic here
        pass

    async def process_memory_similarity(self, body: Dict[str, Any]):
        """Process memory similarity pruning jobs."""
        logger.info(f"Processing memory similarity: {body}")
        
        # Your similarity analysis logic here
        pass

    async def process_git_history_analysis(self, body: Dict[str, Any]):
        """Process git history analysis jobs."""
        logger.info(f"Processing git history analysis: {body}")
        
        since = body.get("since", "1 week ago")
        max_commits = body.get("max_commits", 20)
        create_memory = body.get("create_memory_node", False)
        
        # Your git analysis logic here
        logger.info(f"Git analysis: since={since}, max_commits={max_commits}")

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
# RabbitMQ Configuration
RABBITMQ_USER=user
RABBITMQ_PASS=password

# AI IDE API Configuration
AI_IDE_API_URL=http://localhost:9103
MEMORY_API_URL=http://localhost:9103/memory
MEMORY_API_TOKEN=your-project-admin-token-here

# Worker Configuration
WORKER_LOG_LEVEL=INFO
WORKER_MAX_RETRIES=3
```

### 7. Create Job Publisher Scripts 📤

Create `scripts/publish_job.py`:

```python
#!/usr/bin/env python3
"""
Job Publisher for AI IDE RabbitMQ Integration
Publishes jobs to various queues with standardized message formats.
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
    parser = argparse.ArgumentParser(description="Publish jobs to AI IDE RabbitMQ queues")
    parser.add_argument("--queue", required=True, help="Queue name to publish to")
    parser.add_argument("--message", required=True, help="JSON message to publish")
    parser.add_argument("--file", help="File containing JSON message")
    
    args = parser.parse_args()
    
    # Parse message
    if args.file:
        with open(args.file, 'r') as f:
            message = json.load(f)
    else:
        message = json.loads(args.message)
    
    # Publish job
    publisher = JobPublisher()
    try:
        publisher.connect()
        publisher.publish_job(args.queue, message)
    finally:
        publisher.close()

if __name__ == "__main__":
    main()
```

### 8. Create Example Jobs 📋

Create `examples/memory_update_example.py`:

```python
#!/usr/bin/env python3
"""
Example: Publishing a memory update job
"""

import json
from scripts.publish_job import JobPublisher

# Example memory update job
memory_update_job = {
    "content": "User completed onboarding step 3: Database setup",
    "meta": {
        "type": "onboarding_progress",
        "user_id": "user123",
        "step": "database_setup",
        "status": "completed",
        "tags": ["onboarding", "progress"],
        "categories": ["user_activity"]
    }
}

# Publish the job
publisher = JobPublisher()
try:
    publisher.connect()
    publisher.publish_job("memory.update", memory_update_job)
finally:
    publisher.close()
```

Create `examples/git_history_example.py`:

```python
#!/usr/bin/env python3
"""
Example: Publishing a git history analysis job
"""

import json
from scripts.publish_job import JobPublisher

# Example git history analysis job
git_history_job = {
    "since": "1 week ago",
    "max_commits": 50,
    "include_diff": True,
    "summarize": True,
    "output_format": "summary",
    "create_memory_node": True,
    "memory_namespace": "weekly_analysis",
    "memory_tags": ["weekly", "automated", "git-history"],
    "batch_size": 5
}

# Publish the job
publisher = JobPublisher()
try:
    publisher.connect()
    publisher.publish_job("git.history.analysis", git_history_job)
finally:
    publisher.close()
```

### 9. Start the System 🚀

```bash
# Start the services
docker compose up -d

# Check logs
docker compose logs -f worker

# Test with example jobs
python examples/memory_update_example.py
python examples/git_history_example.py
```

## Understanding the System 🧠

### Queue Types and Message Schemas

#### 1. Memory Update Queue (`memory.update`)
**Purpose**: Update the AI IDE's memory system with new information.

**Message Schema**:
```json
{
  "content": "Human-readable content to store",
  "meta": {
    "type": "string",
    "tags": ["array", "of", "tags"],
    "categories": ["array", "of", "categories"],
    "user_id": "optional_user_id",
    "source": "optional_source",
    "priority": "optional_priority"
  }
}
```

#### 2. Memory Cleanup Queue (`memory.cleanup`)
**Purpose**: Clean up old or stale memory entries.

**Message Schema**:
```json
{
  "dry_run": true,
  "age_days": 180,
  "tags": ["optional", "tags", "to", "target"],
  "categories": ["optional", "categories", "to", "target"]
}
```

#### 3. Memory Enrichment Queue (`memory.enrichment`)
**Purpose**: Enhance existing memory entries with additional context.

**Message Schema**:
```json
{
  "memory_ids": ["array", "of", "memory", "ids"],
  "enrichment_type": "context|similarity|classification",
  "parameters": {
    "additional": "parameters"
  }
}
```

#### 4. Memory Similarity Queue (`memory.similarity`)
**Purpose**: Analyze and prune similar memory entries.

**Message Schema**:
```json
{
  "similarity_threshold": 0.8,
  "batch_size": 100,
  "dry_run": true
}
```

#### 5. Git History Analysis Queue (`git.history.analysis`)
**Purpose**: Analyze git repository history for insights.

**Message Schema**:
```json
{
  "since": "1 week ago",
  "until": "optional_end_date",
  "max_commits": 50,
  "author": "optional_author_filter",
  "include_diff": true,
  "summarize": true,
  "output_format": "json|text|summary",
  "create_memory_node": true,
  "memory_namespace": "git_analysis",
  "memory_tags": ["git", "analysis"],
  "batch_size": 5
}
```

#### 6. Progress Report Queue (`progress.report`)
**Purpose**: Generate progress reports and analytics.

**Message Schema**:
```json
{
  "report_type": "daily|weekly|monthly",
  "include_metrics": true,
  "target_audience": "team|management|stakeholders"
}
```

#### 7. Maintenance Queue (`maintenance`)
**Purpose**: Run system maintenance tasks.

**Message Schema**:
```json
{
  "task": "task_name",
  "args": {
    "additional": "arguments"
  },
  "dry_run": true
}
```

#### 8. Background Jobs Queue (`background.jobs`)
**Purpose**: General purpose background processing.

**Message Schema**:
```json
{
  "job_type": "custom_job_type",
  "data": {
    "job": "specific_data"
  },
  "priority": "high|normal|low",
  "retry_count": 0
}
```

### Best Practices 💡

#### 1. Queue Management
- **Use descriptive queue names** that clearly indicate purpose
- **Make queues durable** for persistence across restarts
- **Implement proper error handling** with dead letter queues
- **Monitor queue lengths** to prevent bottlenecks

#### 2. Message Design
- **Keep messages small** and focused on single responsibilities
- **Use consistent schema** across similar message types
- **Include metadata** for tracking and debugging
- **Version your schemas** for backward compatibility

#### 3. Worker Design
- **Keep workers focused** on specific queue types
- **Implement proper logging** for debugging and monitoring
- **Handle reconnection gracefully** for network issues
- **Use appropriate acknowledgment patterns**

#### 4. Security
- **Change default credentials** in production
- **Use SSL/TLS** for encrypted communication
- **Implement proper access control** with user permissions
- **Secure sensitive environment variables**

#### 5. Monitoring
- **Use RabbitMQ Management UI** (http://localhost:15672)
- **Monitor queue lengths** and processing rates
- **Track failed jobs** and error rates
- **Set up alerts** for critical issues

## Troubleshooting Guide 🔍

### Common Issues and Solutions

#### 1. Connection Errors
```bash
# Check if RabbitMQ is running
docker compose ps

# Check RabbitMQ logs
docker compose logs rabbitmq

# Verify network connectivity
docker compose exec worker ping rabbitmq
```

#### 2. Worker Not Processing
```bash
# Check worker logs
docker compose logs worker

# Restart worker
docker compose restart worker

# Check queue status
docker compose exec rabbitmq rabbitmqctl list_queues
```

#### 3. Message Publishing Issues
```bash
# Test connection
python -c "
import pika
conn = pika.BlockingConnection(pika.URLParameters('amqp://user:password@localhost:5672/'))
print('Connection successful')
conn.close()
"

# Check queue declarations
docker compose exec rabbitmq rabbitmqctl list_queues
```

#### 4. Memory API Integration Issues
```bash
# Test API connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:9103/health

# Check token validity
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:9103/memory/nodes
```

### Performance Optimization

#### 1. Queue Performance
- **Use appropriate prefetch counts** for workers
- **Implement batch processing** for high-volume queues
- **Monitor memory usage** and adjust accordingly
- **Use separate queues** for different priority levels

#### 2. Worker Performance
- **Scale workers horizontally** for high throughput
- **Implement connection pooling** for external APIs
- **Use async processing** for I/O operations
- **Monitor resource usage** and optimize accordingly

## Expected Outcomes

After setting up the portable RabbitMQ system, you should have:

### ✅ Working Infrastructure
- **Running RabbitMQ server** with management UI
- **Functional worker** processing multiple queue types
- **Job publishing scripts** for easy integration
- **Example implementations** for common use cases

### ✅ Integration Capabilities
- **Memory system integration** for storing and retrieving information
- **Git history analysis** for codebase insights
- **Background job processing** for async tasks
- **Maintenance automation** for system health

### ✅ Development Workflow
- **Easy job publishing** through standardized scripts
- **Comprehensive logging** for debugging and monitoring
- **Scalable architecture** for growing needs
- **Security best practices** for production deployment

### ✅ Monitoring and Management
- **Queue monitoring** through RabbitMQ Management UI
- **Worker health checks** and automatic restarts
- **Error tracking** and alerting capabilities
- **Performance metrics** for optimization

## Next Steps

### 1. Customize for Your Needs
- **Add custom queue handlers** for your specific requirements
- **Implement your business logic** in worker methods
- **Create custom message schemas** for your use cases
- **Add authentication** for your external services

### 2. Production Deployment
- **Set up SSL/TLS** for secure communication
- **Configure monitoring** and alerting
- **Implement backup strategies** for data persistence
- **Set up CI/CD** for automated deployment

### 3. Integration with AI IDE
- **Obtain project admin tokens** for API access
- **Configure memory system integration** for knowledge sharing
- **Set up automated workflows** for continuous learning
- **Monitor integration health** and performance

### 4. Advanced Features
- **Implement dead letter queues** for failed message handling
- **Add message routing** based on content or priority
- **Set up message persistence** for critical workflows
- **Implement retry mechanisms** for transient failures

---

## Mermaid Diagram: System Architecture

```mermaid
graph TB
    subgraph "External Project"
        A[Your Application] --> B[Job Publisher]
        B --> C[RabbitMQ]
        C --> D[Worker]
        D --> E[Custom Logic]
        E --> F[AI IDE API]
    end
    
    subgraph "AI IDE System"
        F --> G[Memory System]
        F --> H[Git Analysis]
        F --> I[Progress Reports]
        F --> J[Maintenance Tasks]
    end
    
    subgraph "Monitoring"
        K[RabbitMQ Management UI]
        L[Worker Logs]
        M[API Health Checks]
    end
    
    C --> K
    D --> L
    F --> M
    
    style A fill:#e1f5fe
    style C fill:#f3e5f5
    style F fill:#e8f5e8
    style K fill:#fff3e0
```

This setup provides a robust foundation for building external bots and helpers that can integrate seamlessly with the AI IDE system while maintaining separation and security. 