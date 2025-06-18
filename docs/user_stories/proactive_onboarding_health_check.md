# User Story: Proactive Automated Onboarding Health Check

## Motivation
As a developer, system administrator, or AI agent, I want a proactive, automated health check system that continuously monitors the AI-IDE environment and provides detailed user information, so that I can:
- Identify and resolve issues before they impact development
- Get comprehensive system status and recommendations
- Maintain optimal system health for seamless AI collaboration
- Receive actionable insights for system improvements

---

## Actors
- Developer
- System Administrator
- AI Agent
- CI/CD Pipeline
- New team member (onboarding)

---

## Preconditions
- Python 3.11+ is available
- Required dependencies are installed (requests, subprocess)
- Access to Docker and system commands
- API and services are configured

---

## Step-by-Step Actions

### 1. Run Single Health Check
```bash
# Basic health check with text output
make -f Makefile.ai ai-proactive-onboarding-health

# JSON output for automation
make -f Makefile.ai ai-proactive-onboarding-health FORMAT=json

# Verbose output with detailed logging
make -f Makefile.ai ai-proactive-onboarding-health VERBOSE=1
```

### 2. Start Continuous Monitoring
```bash
# Run continuous monitoring (default 5-minute intervals)
make -f Makefile.ai ai-proactive-onboarding-health-continuous

# Custom interval (e.g., 2 minutes)
make -f Makefile.ai ai-proactive-onboarding-health-continuous INTERVAL=120

# With verbose logging
make -f Makefile.ai ai-proactive-onboarding-health-continuous VERBOSE=1
```

### 3. Background Monitoring
```bash
# Start background monitoring (runs continuously)
make -f Makefile.ai ai-proactive-onboarding-health-bg

# Custom interval in background
make -f Makefile.ai ai-proactive-onboarding-health-bg INTERVAL=300

# View background logs
make -f Makefile.ai ai-proactive-onboarding-health-logs

# View latest health report
make -f Makefile.ai ai-proactive-onboarding-health-report

# Stop background monitoring
make -f Makefile.ai ai-proactive-onboarding-health-stop
```

### 4. Direct Script Usage
```bash
# Single check with custom format
python scripts/proactive_onboarding_health_check.py --format json

# Continuous monitoring with custom interval
python scripts/proactive_onboarding_health_check.py --continuous --interval 180

# Verbose continuous monitoring
python scripts/proactive_onboarding_health_check.py --continuous --verbose
```

---

## Health Checks Performed

### System Infrastructure
- **Environment Variables**: Validates required environment variables are set
- **Docker Services**: Checks if all required Docker containers are running
- **API Connectivity**: Tests API endpoints and service health
- **Database Health**: Verifies database connectivity and data access

### AI/LLM Services
- **Ollama Service**: Checks LLM service availability and model status
- **Memory API**: Validates memory storage and retrieval functionality
- **Rule Management**: Tests rule proposal and management endpoints

### Development Environment
- **Makefile Targets**: Ensures all required automation targets exist
- **Rules Directory**: Validates .cursor/rules structure and YAML frontmatter
- **Onboarding Documentation**: Checks documentation completeness and currency

### File System
- **Required Files**: Validates presence of critical project files
- **Configuration Files**: Checks .env and configuration completeness
- **Documentation**: Ensures onboarding guides are present and updated

---

## Expected Outcomes

### Comprehensive Reports
- **Overall System Status**: OK, WARNING, or ERROR
- **Detailed Check Results**: Individual status for each component
- **Actionable Recommendations**: Specific steps to resolve issues
- **Quick Fixes**: Common solutions for typical problems

### Continuous Monitoring Benefits
- **Proactive Issue Detection**: Identifies problems before they impact work
- **System Health Tracking**: Monitors trends and system stability
- **Automated Logging**: Maintains detailed logs for troubleshooting
- **Real-time Alerts**: Immediate notification of critical issues

### User Information Details
- **Service Status**: Which services are running and their health
- **Configuration Status**: Environment and configuration completeness
- **Performance Metrics**: Response times and service availability
- **Resource Usage**: System resource utilization and capacity

---

## Output Formats

### Text Format (Default)
```
============================================================
PROACTIVE ONBOARDING HEALTH CHECK REPORT
============================================================
Timestamp: 2024-01-15T10:30:00
Overall Status: OK
System Uptime: 0:05:30

SUMMARY:
  Total Checks: 8
  OK: 7
  Warnings: 1
  Errors: 0
  Info: 0

DETAILED RESULTS:
✅ Environment Variables
   Status: OK
   Message: All required environment variables are set
   Details: {"checked_vars": ["ENVIRONMENT", "POSTGRES_HOST", ...]}

⚠️ Ollama Service
   Status: WARNING
   Message: Ollama is running but no models are available
   Recommendations:
     • Pull a model: make -f Makefile.ai ai-ollama-pull-model
     • Check Ollama logs: make -f Makefile.ai ai-ollama-logs

GENERAL RECOMMENDATIONS:
  • Pull a model: make -f Makefile.ai ai-ollama-pull-model
  • Check Ollama logs: make -f Makefile.ai ai-ollama-logs

============================================================
```

### JSON Format
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "overall_status": "OK",
  "summary": {
    "total_checks": 8,
    "ok_count": 7,
    "warning_count": 1,
    "error_count": 0
  },
  "checks": [
    {
      "name": "Environment Variables",
      "status": "OK",
      "message": "All required environment variables are set",
      "details": {"checked_vars": ["ENVIRONMENT", "POSTGRES_HOST"]}
    }
  ],
  "recommendations": [
    "Pull a model: make -f Makefile.ai ai-ollama-pull-model"
  ],
  "quick_fixes": []
}
```

---

## Best Practices

### For Developers
- Run health checks before starting development work
- Use continuous monitoring during active development
- Check logs when experiencing issues
- Review recommendations for system improvements

### For System Administrators
- Set up background monitoring for production environments
- Configure appropriate check intervals based on system load
- Monitor logs for trends and recurring issues
- Use JSON output for integration with monitoring systems

### For AI Agents
- Run health checks before performing automated tasks
- Use JSON format for programmatic analysis
- Check system status before making changes
- Report health issues to human operators

### For CI/CD Pipelines
- Integrate health checks into deployment pipelines
- Use JSON output for automated decision making
- Fail deployments if critical health checks fail
- Generate health reports for deployment reviews

---

## Troubleshooting

### Common Issues
- **Docker not running**: Start Docker and run `make -f Makefile.ai ai-up`
- **API not accessible**: Check API logs and restart services
- **Missing environment variables**: Create or update .env file
- **Ollama service down**: Start Ollama and pull required models

### Log Analysis
```bash
# View health check logs
make -f Makefile.ai ai-proactive-onboarding-health-logs

# View background monitoring logs
tail -f proactive_health.log

# Check system logs
make -f Makefile.ai logs
```

### Recovery Actions
- **System restart**: `make -f Makefile.ai ai-down && make -f Makefile.ai ai-up`
- **Database reset**: `make -f Makefile.ai ai-db-nuke && make -f Makefile.ai ai-db-migrate`
- **Service restart**: `make -f Makefile.ai ai-api-restart-wait`
- **Ollama restart**: `make -f Makefile.ai ai-ollama-restart-docker-gateway`

---

## Integration with Existing Workflows

### Onboarding Process
- Run health check as part of new user onboarding
- Verify system readiness before starting development
- Provide health status to new team members

### Development Workflow
- Pre-commit health checks
- Continuous monitoring during development
- Health validation before deployments

### Maintenance Schedule
- Daily health check reports
- Weekly system health reviews
- Monthly health trend analysis

---

## References
- **Makefile Targets**: `ai-proactive-onboarding-health*`
- **Script**: `scripts/proactive_onboarding_health_check.py`
- **Logs**: `onboarding_health.log`, `proactive_health.log`
- **Reports**: `onboarding_health_report.json`
- **Related**: `ai-onboarding-health` (basic health check)

---

## Success Metrics
- **System Uptime**: 99%+ availability
- **Issue Detection**: 90%+ of issues detected proactively
- **Resolution Time**: 80%+ of issues resolved within recommended timeframe
- **User Satisfaction**: Reduced onboarding time and fewer system-related blockers

**This proactive health check system ensures optimal system health and provides detailed user information for seamless AI collaboration!** 