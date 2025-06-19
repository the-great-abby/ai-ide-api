# User Story: Start All Development Services (up-full)

## Motivation
When switching computers or starting fresh development work, developers need a simple way to bring up all the necessary services including the core API, database, and RabbitMQ, as well as the LLM services (ollama-functions), background workers, and misc-scripts for development utilities.

## Actors
- Developers switching to a new computer
- Developers starting fresh development work
- Developers who need all services running for comprehensive testing

## Preconditions
- Project is cloned and in the correct directory
- Docker and Docker Compose are installed and running
- Environment files are properly configured

## Step-by-Step Actions

### 1. Quick Setup (Recommended for new computers)
```bash
# Run the full dev-quickstart process
make -f Makefile.ai dev-quickstart
```

### 2. Start All Services
```bash
# Bring up all services including LLM, worker, and misc-scripts
make -f Makefile.ai up-full
```

### 3. Verify Services Are Running
```bash
# Check status of all services
make -f Makefile.ai status
```

## Expected Outcomes

### Services Started
- **API**: FastAPI server running on port 9103
- **Database**: PostgreSQL with pgvector extensions on port 5432
- **RabbitMQ**: Message broker with management UI on port 15672
- **Ollama Functions**: LLM service for AI-powered features
- **Worker**: Background job processor
- **Misc Scripts**: Development utilities and tools

### Service URLs
- API: http://localhost:9103
- API Documentation: http://localhost:9103/docs
- Admin Frontend: http://localhost:3000 (if started)
- RabbitMQ Management: http://localhost:15672
- Ollama Functions: http://localhost:8000 (internal)

### Health Checks
- Database shows as "healthy" in status
- All containers are in "Up" state
- Services are ready to accept requests

## Best Practices

### When to Use
- **up-full**: When you need all services for comprehensive development
- **up**: When you only need core services (API, DB, RabbitMQ)
- **dev-quickstart**: When setting up on a new computer

### Troubleshooting
- If services fail to start, check Docker logs: `docker-compose logs <service-name>`
- Ensure Docker has enough resources allocated
- Verify environment variables are properly set
- Check that required ports are not already in use

### Service Management
- **Stop all services**: `make -f Makefile.ai down`
- **Restart specific service**: `docker-compose restart <service-name>`
- **View logs**: `make -f Makefile.ai logs` or `docker-compose logs <service-name>`

## Related Commands
- `make -f Makefile.ai help` - View all available commands
- `make -f Makefile.ai health` - Run health checks
- `make -f Makefile.ai test` - Run test suite

## References
- [Docker Compose Configuration](../docker-compose.yml)
- [Makefile.ai](../Makefile.ai)
- [Development Environment Setup](../onboarding/FRESH_MACHINE_SETUP.md) 