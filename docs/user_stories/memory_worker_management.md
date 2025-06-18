---
title: Memory Worker Management Workflow
description: Guide for managing and triggering memory system background workers
category: Memory System
tags: [memory, workers, automation, maintenance, rabbitmq]
---

# Memory Worker Management Workflow

## Overview
The memory system uses several background workers to maintain data quality, detect similarities, and enrich content. This workflow explains how to manage these workers and trigger their jobs.

## Motivation
- Maintain clean and organized memory nodes
- Detect and handle similar or duplicate content
- Enrich nodes with tags and categories
- Track development progress
- Ensure system health

## Actors
- **Developer/Admin**: Triggers jobs and monitors worker status
- **Memory Workers**:
  - Progress Report Worker: Tracks and summarizes development progress
  - Cleanup Worker: Removes stale or irrelevant nodes
  - Enrichment Worker: Adds tags and categories to nodes
  - Similarity Worker: Detects and handles similar content

## Preconditions
- Docker environment is running
- RabbitMQ service is available
- Worker containers are deployed
- Required Python scripts are installed

## Step-by-Step Actions

### 1. Worker Status Management
```bash
# Restart all memory workers
make -f Makefile.ai memory-restart-workers

# View recent worker logs
make -f Makefile.ai memory-worker-logs
```

### 2. Progress Report Worker
Track development progress and create memory nodes for changes:
```bash
# Trigger progress report
make -f Makefile.ai memory-trigger-progress
```

### 3. Memory Cleanup Worker
Clean up stale or irrelevant nodes:
```bash
# Normal cleanup
make -f Makefile.ai memory-trigger-cleanup

# Preview changes without applying
make -f Makefile.ai memory-trigger-cleanup DRY_RUN=true
```

### 4. Memory Enrichment Worker
Add tags and categories to nodes:
```bash
# Process all nodes
make -f Makefile.ai memory-trigger-enrichment SCOPE=all

# Process only new nodes
make -f Makefile.ai memory-trigger-enrichment SCOPE=new

# Process specific namespace
make -f Makefile.ai memory-trigger-enrichment SCOPE=namespace:docs

# Preview changes
make -f Makefile.ai memory-trigger-enrichment SCOPE=all DRY_RUN=true
```

### 5. Memory Similarity Worker
Detect and handle similar content:
```bash
# Basic similarity check
make -f Makefile.ai memory-trigger-similarity SCOPE=all

# Fine-tuned similarity detection
make -f Makefile.ai memory-trigger-similarity SCOPE=new \
  VECTOR_THRESHOLD=0.95 \
  CONTENT_THRESHOLD=0.90 \
  TAG_THRESHOLD=0.80

# Preview similarity matches
make -f Makefile.ai memory-trigger-similarity SCOPE=all DRY_RUN=true
```

## Expected Outcomes

### Progress Report Worker
- New memory nodes created for recent changes
- Git diffs summarized and stored
- Development progress tracked

### Cleanup Worker
- Stale nodes identified and removed
- System resources optimized
- Memory graph stays relevant

### Enrichment Worker
- Nodes tagged with relevant categories
- Content automatically classified
- Improved searchability

### Similarity Worker
- Similar content detected
- Duplicate nodes merged
- Related nodes connected
- Knowledge graph better organized

## Best Practices

1. **Regular Maintenance**
   - Run cleanup weekly
   - Process new nodes daily
   - Check similarities after bulk imports

2. **Safe Operations**
   - Always use `DRY_RUN=true` first
   - Review logs before/after jobs
   - Back up before major operations

3. **Performance**
   - Process in batches using SCOPE
   - Run intensive jobs during off-hours
   - Monitor resource usage

4. **Monitoring**
   - Check worker logs regularly
   - Verify job completion
   - Track error patterns

## Troubleshooting

### Common Issues

1. **Worker Not Responding**
   ```bash
   # Restart the worker
   make -f Makefile.ai memory-restart-workers
   
   # Check logs
   make -f Makefile.ai memory-worker-logs
   ```

2. **Job Stuck in Queue**
   - Verify RabbitMQ is running
   - Check worker container status
   - Review error logs

3. **Failed Jobs**
   - Check worker logs for errors
   - Verify input parameters
   - Ensure dependencies are available

## References
- [Memory System Architecture](../onboarding/MEMORY_SYSTEM.md)
- [Memory Hygiene Best Practices](../onboarding/MEMORY_HYGIENE_AND_CONFIDENCE.md)
- [Testing Workflow](../onboarding/TESTING_WORKFLOW.md)
- [Maintenance Automation](../../MAINTENANCE_AUTOMATION.md)

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Worker Health**
   - Worker process status (up/down)
   - Memory usage and trends
   - CPU utilization
   - Error rates and types
   - Job processing latency

2. **Queue Metrics**
   - Queue lengths
   - Message age in queue
   - Processing time per job type
   - Failed/retry job counts
   - Dead letter queue size

3. **Operation Success Rates**
   - Node creation/update success
   - Edge creation success
   - Similarity detection accuracy
   - Enrichment completion rates
   - Cleanup operation success

4. **System Impact**
   - Database connection pool usage
   - Network I/O rates
   - Disk usage (for logs/temp files)
   - API endpoint latency
   - Overall system load

### Alerting Thresholds

1. **Critical Alerts** (Immediate Action Required)
   ```yaml
   worker_down:
     condition: process_status == 'down'
     duration: '5m'
     action: notify_oncall

   queue_stuck:
     condition: queue_age > 30m
     count: 10
     action: notify_oncall

   error_spike:
     condition: error_rate > 20%
     window: '5m'
     action: notify_oncall
   ```

2. **Warning Alerts** (Investigation Needed)
   ```yaml
   high_latency:
     condition: processing_time > 2m
     count: 5
     action: notify_team

   memory_growth:
     condition: memory_usage > 85%
     duration: '15m'
     action: notify_team

   failed_jobs:
     condition: failed_count > 10
     window: '1h'
     action: notify_team
   ```

3. **Info Alerts** (For Awareness)
   ```yaml
   large_batch:
     condition: batch_size > 1000
     action: log_event

   long_running_job:
     condition: job_duration > 10m
     action: log_event
   ```

### Monitoring Setup

1. **Worker Container Monitoring**
   ```bash
   # Check worker status
   make -f Makefile.ai memory-worker-logs | grep "ERROR\|WARN"
   
   # Monitor resource usage
   docker stats worker
   
   # Check queue status
   docker exec rabbitmq rabbitmqctl list_queues
   ```

2. **Log Aggregation**
   - Configure log forwarding to central system
   - Set up log parsing rules
   - Create dashboards for key metrics
   - Enable log-based alerts

3. **Health Check Endpoints**
   ```bash
   # Worker health
   curl http://localhost:9103/health/worker
   
   # Queue health
   curl http://localhost:9103/health/queue
   
   # Job status
   curl http://localhost:9103/health/jobs
   ```

### Automated Health Checks

1. **Periodic Checks**
   ```bash
   # Add to crontab
   */5 * * * * make -f Makefile.ai memory-healthcheck
   
   # Daily status report
   0 0 * * * make -f Makefile.ai memory-status-report
   ```

2. **Proactive Monitoring**
   ```bash
   # Monitor job completion times
   make -f Makefile.ai memory-monitor-jobs
   
   # Check for stuck jobs
   make -f Makefile.ai memory-check-stuck-jobs
   ```

### Recovery Procedures

1. **Worker Recovery**
   ```bash
   # Restart single worker
   make -f Makefile.ai memory-restart-workers
   
   # Full system recovery
   make -f Makefile.ai memory-system-recover
   ```

2. **Queue Recovery**
   ```bash
   # Clear stuck jobs
   make -f Makefile.ai memory-clear-stuck-jobs
   
   # Requeue failed jobs
   make -f Makefile.ai memory-requeue-failed
   ```

### Best Practices for Monitoring

1. **Proactive Monitoring**
   - Set up trending analysis
   - Monitor for pattern changes
   - Track seasonal variations
   - Establish baseline metrics

2. **Alert Management**
   - Define clear escalation paths
   - Set appropriate thresholds
   - Avoid alert fatigue
   - Document response procedures

3. **Maintenance Windows**
   - Schedule regular maintenance
   - Plan for peak/off-peak times
   - Coordinate with team schedules
   - Document maintenance procedures

4. **Capacity Planning**
   - Track resource utilization
   - Project growth trends
   - Plan for scale events
   - Monitor bottlenecks 