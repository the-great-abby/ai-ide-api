# Maintenance Automation Guide

## Startup & Shutdown

- Start: `make ai-maintenance-up`
- Stop: `make ai-maintenance-down`
- Status: `make ai-maintenance-status`
- Live logs: `make ai-maintenance-logs`

## Manual Task Trigger

```
python scripts/trigger_maintenance_task.py memory_cleanup dry_run=False
```

## Log Review

- Live logs: `make ai-maintenance-logs`
- Log files: (if mounted) `logs/maintenance-worker/worker.log`, `logs/maintenance-scheduler/scheduler.log`

## Adding a New Job

1. Add a function to the appropriate script.
2. Register it in `worker/maintenance_worker.py`'s `TASK_MAP`.
3. Add a schedule in `scripts/maintenance_scheduler.py` if needed.

## Troubleshooting

- Check logs for errors.
- Ensure RabbitMQ is running (`docker compose ps`).
- Use `docker compose restart <service>` to restart a stuck container. 