# Git History Analysis Quick Reference

## 📅 Scheduled Execution

| **Frequency** | **Time** | **Scope** | **Max Commits** | **Output** | **Namespace** |
|---------------|----------|-----------|-----------------|------------|---------------|
| **Daily** | 6 AM | Last 24 hours | 50 | Summary | `daily_analysis` |
| **Weekly** | Monday 7 AM | Last week | 100 | Summary | `weekly_analysis` |
| **Sprint** | Monday 8 AM | Last 2 weeks | 200 | Summary | `sprint_analysis` |
| **Monthly** | 1st of month 9 AM | Last month | 500 | JSON + diffs | `monthly_analysis` |

## 🚀 Quick Start Commands

### Check Status
```bash
# Check overall status
make -f Makefile.ai ai-git-history-status

# View worker logs
make -f Makefile.ai ai-git-history-logs

# Check scheduler logs
make -f Makefile.ai ai-git-history-scheduler-logs
```

### Manual Triggers
```bash
# Trigger daily analysis
make -f Makefile.ai ai-git-history-trigger-daily

# Trigger weekly analysis
make -f Makefile.ai ai-git-history-trigger-weekly

# Trigger sprint analysis
make -f Makefile.ai ai-git-history-trigger-sprint

# Trigger monthly analysis
make -f Makefile.ai ai-git-history-trigger-monthly
```

### View Results
```bash
# List recent results
make -f Makefile.ai ai-git-history-list-results

# View specific result
make -f Makefile.ai ai-git-history-view-result ID=<memory_node_id>
```

## 🔧 Troubleshooting

### Check System Health
```bash
# Comprehensive health check
make -f Makefile.ai ai-git-history-check-health

# Restart services if needed
make -f Makefile.ai ai-git-history-restart
```

### Common Issues

1. **Analysis Not Running**
   ```bash
   # Check if services are running
   docker compose ps worker maintenance-scheduler
   
   # Check scheduler logs
   make -f Makefile.ai ai-git-history-scheduler-logs
   
   # Restart services
   make -f Makefile.ai ai-git-history-restart
   ```

2. **No Results Found**
   ```bash
   # Check if analysis has run
   make -f Makefile.ai ai-git-history-list-results
   
   # Trigger manual analysis
   make -f Makefile.ai ai-git-history-trigger-daily
   ```

3. **Memory Nodes Not Created**
   ```bash
   # Check API token
   cat /code/.apitoken
   
   # Check API health
   curl -s http://localhost:9103/health
   
   # Check worker logs
   make -f Makefile.ai ai-git-history-logs
   ```

## 📊 Expected Output

### Status Check
```
=== Scheduled Jobs ===
Daily: 6 AM - Last 24 hours (50 commits max)
Weekly: Monday 7 AM - Last week (100 commits max)
Sprint: Monday 8 AM - Last 2 weeks (200 commits max)
Monthly: 1st of month 9 AM - Last month (500 commits max)

=== Worker Status ===
worker    Up 2 hours

=== Recent Analysis Results ===
2024-01-15T06:00:00Z - daily_analysis: 5 commits
2024-01-15T07:00:00Z - weekly_analysis: 25 commits
2024-01-15T08:00:00Z - sprint_analysis: 45 commits
```

### Results List
```
2024-01-15T06:00:00Z - daily_analysis (1 day ago, 5 commits)
2024-01-15T07:00:00Z - weekly_analysis (1 week ago, 25 commits)
2024-01-15T08:00:00Z - sprint_analysis (2 weeks ago, 45 commits)
```

## 🎯 Use Cases

### Daily Check
```bash
# Morning status check
make -f Makefile.ai ai-git-history-status

# Check yesterday's activity
make -f Makefile.ai ai-git-history-list-results
```

### Sprint Retrospective
```bash
# Generate sprint analysis
make -f Makefile.ai ai-git-history-trigger-sprint

# View sprint results
make -f Makefile.ai ai-git-history-list-results
```

### Monthly Review
```bash
# Generate monthly analysis
make -f Makefile.ai ai-git-history-trigger-monthly

# View detailed monthly results
make -f Makefile.ai ai-git-history-list-results
```

### Troubleshooting Session
```bash
# Check system health
make -f Makefile.ai ai-git-history-check-health

# View recent logs
make -f Makefile.ai ai-git-history-logs

# Restart if needed
make -f Makefile.ai ai-git-history-restart
```

## 📚 Related Documentation

- [Git History Analysis Process](git_history_analysis_process.md)
- [Git History Analysis Workflow](user_stories/git_history_analysis.md)
- [Git History RabbitMQ Integration](user_stories/git_history_rabbitmq_integration.md)
- [Git History Awareness Growth](git_history_awareness_growth.md) 