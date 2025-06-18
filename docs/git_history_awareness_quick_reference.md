# Git History Awareness Quick Reference

## 🚀 Quick Start Commands

### Basic Monitoring
```bash
# Check overall awareness status
make -f Makefile.ai memory-git-history-awareness-status

# View analysis timeline
make -f Makefile.ai memory-git-history-awareness-timeline

# Analyze development patterns
make -f Makefile.ai memory-git-history-awareness-patterns
```

### Anomaly Detection
```bash
# Check for recent anomalies
make -f Makefile.ai memory-git-history-awareness-anomalies

# Analyze development trends
make -f Makefile.ai memory-git-history-awareness-trends
```

### Report Generation
```bash
# Generate comprehensive report
make -f Makefile.ai memory-git-history-awareness-report

# Export data for external analysis
make -f Makefile.ai memory-git-history-awareness-export
```

### Memory Management
```bash
# Clean up old analysis nodes (6+ months)
make -f Makefile.ai memory-git-history-awareness-cleanup
```

### Custom Analysis
```bash
# Trigger comprehensive analysis
make -f Makefile.ai memory-git-history-awareness-trigger-full

# Custom analysis with parameters
make -f Makefile.ai memory-git-history-awareness-trigger-custom SINCE='1 week ago' NAMESPACE=custom_analysis MEMORY_TAGS='sprint1 retrospective'
```

## 📊 Scheduled Execution

| **Frequency** | **Time** | **Command** | **Purpose** |
|---------------|----------|-------------|-------------|
| **Daily** | 6 AM | Automatic | Daily development tracking |
| **Weekly** | Monday 7 AM | Automatic | Weekly patterns |
| **Sprint** | Monday 8 AM | Automatic | Sprint analysis |
| **Monthly** | 1st of month 9 AM | Automatic | Long-term trends |

## 🔍 Monitoring Workflows

### Daily Check
```bash
# Quick status check
make -f Makefile.ai memory-git-history-awareness-status

# Check for anomalies
make -f Makefile.ai memory-git-history-awareness-anomalies
```

### Weekly Review
```bash
# Generate weekly report
make -f Makefile.ai memory-git-history-awareness-report

# Analyze patterns
make -f Makefile.ai memory-git-history-awareness-patterns
```

### Monthly Cleanup
```bash
# Export before cleanup
make -f Makefile.ai memory-git-history-awareness-export

# Clean up old nodes
make -f Makefile.ai memory-git-history-awareness-cleanup
```

### Sprint Retrospective
```bash
# Generate sprint analysis
make -f Makefile.ai memory-git-history-awareness-trigger-custom SINCE='2 weeks ago' NAMESPACE=sprint_retro MEMORY_TAGS='sprint retrospective'

# Analyze sprint patterns
make -f Makefile.ai memory-git-history-awareness-patterns
```

## 🎯 Use Case Examples

### Team Lead Daily Check
```bash
# Morning status check
make -f Makefile.ai memory-git-history-awareness-status

# Check yesterday's activity
make -f Makefile.ai memory-git-history-awareness-anomalies
```

### Project Manager Weekly Report
```bash
# Generate weekly report
make -f Makefile.ai memory-git-history-awareness-report

# Export for stakeholder presentation
make -f Makefile.ai memory-git-history-awareness-export
```

### DevOps Monthly Maintenance
```bash
# Check system health
make -f Makefile.ai memory-git-history-awareness-status

# Clean up old data
make -f Makefile.ai memory-git-history-awareness-cleanup
```

### Developer Sprint Review
```bash
# Generate sprint analysis
make -f Makefile.ai memory-git-history-awareness-trigger-custom SINCE='2 weeks ago' NAMESPACE=sprint5 MEMORY_TAGS='sprint5 retrospective'

# View sprint patterns
make -f Makefile.ai memory-git-history-awareness-patterns
```

## 🔧 Troubleshooting

### No Analysis Nodes Found
```bash
# Check worker status
make -f Makefile.ai misc-git-history-worker-logs

# Trigger manual analysis
make -f Makefile.ai memory-git-history-awareness-trigger-full
```

### API Connection Issues
```bash
# Check API health
curl -s http://localhost:9103/health

# Verify authentication
cat /code/.apitoken
```

### Memory Storage Issues
```bash
# Check memory usage
make -f Makefile.ai memory-git-history-awareness-status

# Clean up old nodes
make -f Makefile.ai memory-git-history-awareness-cleanup
```

## 📈 Expected Output Examples

### Status Check Output
```
=== Analysis Node Counts ===
  daily_analysis: 30 analyses
  weekly_analysis: 12 analyses
  sprint_analysis: 6 analyses
  monthly_analysis: 3 analyses

=== Recent Analysis Timeline ===
2024-01-15T06:00:00Z - daily_analysis (1 day ago, 5 commits)
2024-01-15T07:00:00Z - weekly_analysis (1 week ago, 25 commits)
2024-01-15T08:00:00Z - sprint_analysis (2 weeks ago, 45 commits)
```

### Pattern Analysis Output
```
=== Daily Patterns ===
{"avg": 5.2, "min": 1, "max": 12, "count": 30}

=== Weekly Patterns ===
{"avg": 24.5, "min": 15, "max": 35, "count": 12}
```

### Anomaly Detection Output
```
=== Recent Activity Analysis ===
2024-01-15T06:00:00Z - daily_analysis: 5 commits
2024-01-14T06:00:00Z - daily_analysis: 12 commits (SPIKE)
2024-01-13T06:00:00Z - daily_analysis: 3 commits
```

## 🚀 Advanced Usage

### Custom Analysis Pipeline
```bash
# Export data for custom processing
make -f Makefile.ai memory-git-history-awareness-export

# Process with custom scripts
python3 scripts/custom_analysis.py exports/git_history_awareness_*.json
```

### Automated Monitoring
```bash
# Add to crontab
0 9 * * 1 make -f Makefile.ai memory-git-history-awareness-status
0 10 * * 1 make -f Makefile.ai memory-git-history-awareness-report
```

### CI/CD Integration
```bash
# Add to CI pipeline
make -f Makefile.ai memory-git-history-awareness-trigger-custom SINCE='${{ github.event.before }}' NAMESPACE=ci_analysis MEMORY_TAGS='ci automated'
```

## 📚 Related Documentation

- [Git History Analysis Workflow](user_stories/git_history_analysis.md)
- [Git History RabbitMQ Integration](user_stories/git_history_rabbitmq_integration.md)
- [Git History Awareness Growth](git_history_awareness_growth.md)
- [Git History Awareness Management](user_stories/git_history_awareness_management.md) 