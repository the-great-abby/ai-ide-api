# Git History Analysis Process Documentation

## Overview
The git history analyzer runs on a scheduled basis to build awareness of codebase evolution over time. This document explains the process, scheduling, and how to manage it.

## Scheduled Execution

The git history analyzer runs automatically on the following schedule:

### Daily Analysis (6 AM every day)
- **Time**: 6:00 AM daily
- **Scope**: Last 24 hours
- **Max Commits**: 50
- **Output**: Summary format
- **Memory Namespace**: `daily_analysis`
- **Tags**: `daily`, `automated`

### Weekly Analysis (Monday 7 AM)
- **Time**: 7:00 AM every Monday
- **Scope**: Last week
- **Max Commits**: 100
- **Output**: Summary format
- **Memory Namespace**: `weekly_analysis`
- **Tags**: `weekly`, `retrospective`

### Sprint Analysis (Monday 8 AM)
- **Time**: 8:00 AM every Monday
- **Scope**: Last 2 weeks
- **Max Commits**: 200
- **Output**: Summary format
- **Memory Namespace**: `sprint_analysis`
- **Tags**: `sprint`, `retrospective`

### Monthly Analysis (1st of month 9 AM)
- **Time**: 9:00 AM on the 1st of each month
- **Scope**: Last month
- **Max Commits**: 500
- **Output**: JSON format with diffs
- **Memory Namespace**: `monthly_analysis`
- **Tags**: `monthly`, `detailed`

## How It Works

### 1. Job Scheduling
The `maintenance_scheduler.py` script runs the scheduled jobs using APScheduler:

```python
# Daily analysis at 6 AM
scheduler.add_job(
    lambda: asyncio.create_task(publish_git_history_job({
        "since": "1 day ago",
        "max_commits": 50,
        "output_format": "summary",
        "create_memory_node": True,
        "memory_namespace": "daily_analysis",
        "memory_tags": ["daily", "automated"],
        "summarize": True,
        "include_diff": False
    })),
    'cron', hour=6
)
```

### 2. Job Processing
Jobs are published to the `git.history.analysis` RabbitMQ queue and processed by the `git_history_worker.py`:

```python
async def process_git_history_analysis_job(job_config: Dict[str, Any]):
    # Extract parameters
    since = job_config.get("since")
    max_commits = job_config.get("max_commits", 20)
    create_memory = job_config.get("create_memory_node", False)
    memory_namespace = job_config.get("memory_namespace", "git_history_analysis")
    
    # Get commits and analyze
    commits = get_commit_list(since=since, max_commits=max_commits)
    analyzed_commits = analyze_commit_range(commits)
    report = generate_report(analyzed_commits, output_format)
    
    # Create memory node if requested
    if create_memory:
        await create_memory_node(report, memory_namespace, memory_tags)
```

### 3. Memory Integration
Analysis results are stored as memory nodes with metadata:

```json
{
  "content": "Git history analysis summary...",
  "meta": {
    "type": "git_history_analysis",
    "namespace": "daily_analysis",
    "since": "1 day ago",
    "commits_analyzed": 15,
    "tags": ["daily", "automated"],
    "categories": ["development", "code-analysis"]
  }
}
```

## Awareness Growth Over Time

The system builds awareness through:

1. **Layered Analysis**: Daily, weekly, sprint, and monthly views
2. **Overlapping Windows**: Each analysis covers overlapping time periods
3. **Memory Accumulation**: Results stored as searchable memory nodes
4. **Pattern Recognition**: LLM summaries identify trends and patterns

## Makefile Targets for Management

### Check Analysis Status
```bash
# Check if analysis is running
make -f Makefile.ai misc-git-history-worker-logs

# Check queue status
make -f Makefile.ai misc-git-history-queue-status

# View recent analysis results
make -f Makefile.ai misc-list-memory-nodes | grep git_history_analysis
```

### Trigger Manual Analysis
```bash
# Trigger daily analysis
make -f Makefile.ai misc-git-history-trigger-daily

# Trigger weekly analysis
make -f Makefile.ai misc-git-history-trigger-weekly

# Trigger sprint analysis
make -f Makefile.ai misc-git-history-trigger-sprint

# Custom analysis
make -f Makefile.ai misc-git-history-trigger SINCE='1 week ago' CREATE_MEMORY=true
```

### Monitor Scheduled Jobs
```bash
# Check maintenance scheduler logs
docker compose logs maintenance-scheduler

# Check worker status
docker compose ps worker

# Restart workers if needed
make -f Makefile.ai restart-workers
```

## Troubleshooting

### Analysis Not Running
1. Check if maintenance scheduler is running:
   ```bash
   docker compose ps maintenance-scheduler
   ```

2. Check scheduler logs:
   ```bash
   docker compose logs maintenance-scheduler
   ```

3. Verify worker is processing jobs:
   ```bash
   make -f Makefile.ai misc-git-history-worker-logs
   ```

### Memory Nodes Not Created
1. Check API token:
   ```bash
   cat /code/.apitoken
   ```

2. Verify memory API is accessible:
   ```bash
   curl -s http://localhost:9103/health
   ```

3. Check worker logs for errors:
   ```bash
   make -f Makefile.ai misc-git-history-worker-logs
   ```

### Performance Issues
1. Reduce commit limits for large repositories
2. Use summary format instead of full JSON
3. Exclude diffs for large time periods
4. Monitor system resources during analysis

## Integration with Development Workflow

### Sprint Retrospectives
```bash
# Generate sprint analysis for retrospective
make -f Makefile.ai misc-git-history-trigger SINCE='2 weeks ago' CREATE_MEMORY=true MEMORY_NAMESPACE=sprint_retro MEMORY_TAGS='sprint retrospective'
```

### Release Planning
```bash
# Analyze since last release
make -f Makefile.ai misc-git-history-trigger SINCE='v1.0.0' CREATE_MEMORY=true MEMORY_NAMESPACE=release_analysis
```

### Team Performance Tracking
```bash
# Analyze team member contributions
make -f Makefile.ai misc-git-history-trigger SINCE='1 month ago' AUTHOR='Team Member' CREATE_MEMORY=true
```

## Best Practices

1. **Regular Monitoring**: Check worker logs weekly
2. **Memory Management**: Archive old analysis nodes periodically
3. **Performance Tuning**: Adjust commit limits based on repository size
4. **Integration**: Use analysis results in sprint retrospectives and planning

## References
- [Git History Analysis Workflow](user_stories/git_history_analysis.md)
- [Git History RabbitMQ Integration](user_stories/git_history_rabbitmq_integration.md)
- [Maintenance Scheduler](../../scripts/maintenance_scheduler.py)
- [Git History Worker](../../scripts/git_history_worker.py) 