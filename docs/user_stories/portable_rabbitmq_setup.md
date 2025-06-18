# User Story: Portable RabbitMQ Setup for External Projects

## Motivation
As a developer working on external projects, I want to set up a portable RabbitMQ system that can handle background jobs and automated tasks, enabling efficient asynchronous processing and integration with the AI IDE's memory system.

## Actors
- Junior Developers
- External Project Teams
- DevOps Engineers
- CI/CD Systems

## Preconditions
- Docker and Docker Compose installed
- Python 3.8+ installed
- Basic understanding of message queues
- Access to the AI IDE API (optional, for memory integration)

## Step-by-Step Guide

### 1. Project Structure Setup 🏗️

First, create the necessary directory structure:

```bash
mkdir -p my-project/{workers,scripts,docker}
cd my-project

# Create initial files
touch docker-compose.yml
touch workers/requirements.txt
touch workers/main.py
touch .env
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

  worker:
    build:
      context: ./workers
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-user}:${RABBITMQ_PASS:-password}@rabbitmq:5672/
      - MEMORY_API_URL=${MEMORY_API_URL:-http://localhost:9103/memory}
      - MEMORY_API_TOKEN=${MEMORY_API_TOKEN}
    volumes:
      - ./workers:/app
    depends_on:
      - rabbitmq

volumes:
  rabbitmq_data:
```

### 3. Create Worker Dockerfile 📄

Create `workers/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 4. Set Up Worker Dependencies 📦

Add to `workers/requirements.txt`:

```
pika==1.3.1
requests==2.31.0
python-dotenv==1.0.0
```

### 5. Create Basic Worker 🔧

Create `workers/main.py`:

```python
import os
import json
import asyncio
import pika
from dotenv import load_dotenv

load_dotenv()

class RabbitMQWorker:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        self.queues = {
            "background.jobs": self.process_background_job,
            "memory.update": self.process_memory_update
        }

    def connect(self):
        parameters = pika.URLParameters(self.rabbitmq_url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queues
        for queue in self.queues.keys():
            self.channel.queue_declare(queue=queue, durable=True)

    async def process_background_job(self, body):
        print(f"Processing background job: {body}")
        # Add your job processing logic here

    async def process_memory_update(self, body):
        print(f"Processing memory update: {body}")
        # Add memory system integration here

    def start(self):
        try:
            self.connect()
            print("Worker started, waiting for messages...")
            
            for queue, callback in self.queues.items():
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=lambda ch, method, props, body: asyncio.run(
                        callback(json.loads(body))
                    ),
                    auto_ack=True
                )
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            print("Shutting down worker...")
            if self.connection:
                self.connection.close()
        except Exception as e:
            print(f"Error: {e}")
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    worker = RabbitMQWorker()
    worker.start()
```

### 6. Environment Setup 🔐

Create `.env` file:

```bash
RABBITMQ_USER=user
RABBITMQ_PASS=password
MEMORY_API_URL=http://localhost:9103/memory
MEMORY_API_TOKEN=your-token-here
```

### 7. Create Job Publisher Script 📤

Create `scripts/publish_job.py`:

```python
import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

def publish_job(queue_name, message):
    # Connect to RabbitMQ
    url = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
    parameters = pika.URLParameters(url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    # Declare queue
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Publish message
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    
    print(f" [x] Sent {message} to {queue_name}")
    connection.close()

if __name__ == "__main__":
    # Example usage
    job = {
        "task": "example_task",
        "data": {"key": "value"}
    }
    publish_job("background.jobs", job)
```

### 8. Start the System 🚀

```bash
# Start the services
docker compose up -d

# Check logs
docker compose logs -f worker

# Publish a test job
python scripts/publish_job.py
```

## Understanding the System 🧠

### Queue Types and Usage

1. **Background Jobs Queue** (`background.jobs`)
   - General purpose background tasks
   - Long-running operations
   - Data processing jobs

2. **Memory Update Queue** (`memory.update`)
   - Integration with AI IDE memory system
   - Code change logging
   - Knowledge base updates

### Best Practices 💡

1. **Queue Management**
   - Use descriptive queue names
   - Make queues durable for persistence
   - Implement proper error handling
   - Add dead letter queues for failed jobs

2. **Worker Design**
   - Keep workers focused and simple
   - Implement proper logging
   - Handle reconnection gracefully
   - Use appropriate acknowledgment patterns

3. **Monitoring**
   - Use RabbitMQ Management UI (http://localhost:15672)
   - Monitor queue lengths
   - Track failed jobs
   - Set up alerts for issues

4. **Security**
   - Change default credentials
   - Use SSL in production
   - Implement proper access control
   - Secure sensitive environment variables

## Troubleshooting Guide 🔍

### Common Issues and Solutions

1. **Connection Errors**
   ```bash
   # Check if RabbitMQ is running
   docker compose ps
   
   # Check RabbitMQ logs
   docker compose logs rabbitmq
   ```

2. **Worker Not Processing**
   ```bash
   # Check worker logs
   docker compose logs worker
   
   # Restart worker
   docker compose restart worker
   ```

3. **Queue Issues**
   - Check Management UI
   - Verify queue declarations
   - Check for queue bindings

## Expected Outcomes

After setting up the portable RabbitMQ system, you should have:
- A running RabbitMQ server
- Working background job processing
- Optional memory system integration
- Ability to monitor and manage queues

## Workflow Diagram

```mermaid
flowchart TD
    A["Setup Project Structure"] --> B["Configure Docker"]
    B --> C["Start RabbitMQ"]
    C --> D["Deploy Workers"]
    
    subgraph "Job Processing"
    E["Publish Job"] --> F["Queue"]
    F --> G["Worker Processes"]
    G --> H["Complete Task"]
    end
```

## Quick Reference

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Publish test job
python scripts/publish_job.py

# Access RabbitMQ UI
open http://localhost:15672
```

## Next Steps
1. Add more specialized workers
2. Implement job retry logic
3. Add monitoring and alerting
4. Set up dead letter queues
5. Integrate with CI/CD pipeline

---

**Remember:** Start with simple jobs and gradually add complexity as needed. Monitor your queues and worker performance regularly.

Need help? Check the [RabbitMQ documentation](https://www.rabbitmq.com/documentation.html) or contact your system administrator. 