# User Story: RabbitMQ Pull-Based Memory Processing for KEDA/Kubernetes (Docker-first)

## Motivation
To enable scalable, event-driven memory processing for AI agents, we want to use RabbitMQ in pull mode. This will allow us to easily migrate to KEDA-based autoscaling in Kubernetes in the future, while supporting local and CI development using Docker Compose. The system should allow new worker containers to pull jobs as they start, without requiring a working Kubernetes cluster during development.

## Actors
- **User**: Triggers memory processing events (e.g., uploads, requests enrichment)
- **API Service**: Publishes memory processing jobs to RabbitMQ
- **Memory Worker**: Pulls jobs from RabbitMQ and processes them
- **(Future) KEDA Scaler**: Monitors queue length and scales worker pods in Kubernetes

## Preconditions
- RabbitMQ is running (locally via Docker Compose or in the future via Kubernetes)
- API service and worker containers are networked with RabbitMQ
- Memory processing jobs are published as messages to a queue (e.g., `memory.update`)

## Step-by-Step Actions
1. **User triggers a memory update** (e.g., uploads a file or sends a message).
2. **API service** publishes a job to the RabbitMQ queue (`memory.update`).
3. **Worker container** (Docker) starts and connects to RabbitMQ.
4. **Worker uses pull mode** (`basic.get` or equivalent) to poll for jobs from the queue.
5. **Worker processes the job** (e.g., vectorizes, enriches, stores memory).
6. **Worker acknowledges the message** after successful processing.
7. **(Optional)** Worker publishes a completion event to a pub/sub system (e.g., Valkey/Redis) for real-time UI updates.
8. **(Future)** In Kubernetes, KEDA will monitor the queue and scale worker pods up/down based on job backlog.

## Expected Outcomes
- Users receive fast API responses (job is queued, not processed synchronously)
- Memory jobs are reliably processed by available workers
- New worker containers can be started/stopped at any time and will pick up jobs as needed
- The system is ready for seamless migration to KEDA/Kubernetes autoscaling

## Best Practices
- Use stateless, idempotent workers (safe to process the same job more than once)
- Use environment variables for RabbitMQ connection info (works in Docker and Kubernetes)
- Use a single, well-defined queue for memory jobs (e.g., `memory.update`)
- Monitor queue length and worker health (for future KEDA integration)
- Use `basic.get` (pull) or short-lived `basic.consume` with prefetch=1 for predictable scaling
- Log job processing and errors for observability

## Managing Job Pulls in Docker (Without Kubernetes)
- Use Docker Compose to run RabbitMQ, API, and one or more worker containers
- To scale up workers, run additional worker containers (e.g., `docker-compose up --scale worker=3`)
- Each new worker will connect to RabbitMQ and begin polling for jobs
- No special orchestration is needed—workers can be started/stopped manually or via Compose
- For local development, this simulates how KEDA will scale pods in Kubernetes

## Migration to KEDA/Kubernetes
- When ready, deploy RabbitMQ and workers as Kubernetes resources
- Use KEDA's RabbitMQ scaler to monitor queue length and autoscale worker pods
- No code changes needed if workers use pull-based job fetching and stateless design

## References
- [KEDA RabbitMQ Scaler Docs](https://keda.sh/docs/2.12/scalers/rabbitmq-queue/)
- [RabbitMQ basic.get vs basic.consume](https://www.rabbitmq.com/consumers.html)
- [Docker Compose scaling](https://docs.docker.com/compose/compose-file/compose-file-v3/#scale) 