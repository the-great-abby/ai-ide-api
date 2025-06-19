#!/usr/bin/env python3
"""
Maintenance Scheduler
Publishes maintenance/refinement tasks to RabbitMQ at scheduled intervals.
"""
import logging
import json
import asyncio
from utils.message_broker import RealRabbitMQClient, MessageBrokerBase
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maintenance_scheduler")

RABBITMQ_HOST = "rabbitmq"  # Adjust if needed
QUEUE_NAME = "maintenance"
GIT_HISTORY_QUEUE = "git.history.analysis"


async def publish_task(task, args=None, broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(f"amqp://user:password@{RABBITMQ_HOST}:5672/")
    body = {"task": task, "args": args or {}}
    await broker.publish(QUEUE_NAME, body)
    logger.info(f"[PUBLISHED] task={task} args={args}")


async def publish_git_history_job(job_config, broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(f"amqp://user:password@{RABBITMQ_HOST}:5672/")
    await broker.publish(GIT_HISTORY_QUEUE, job_config)
    logger.info(f"[PUBLISHED] git_history_job={job_config}")


scheduler = AsyncIOScheduler()

scheduler.add_job(
    lambda: asyncio.create_task(publish_task("memory_cleanup", {"dry_run": True})),
    "cron",
    day_of_week="sun",
    hour=2,
)
scheduler.add_job(
    lambda: asyncio.create_task(publish_task("memory_refinement", {"dry_run": True})),
    "cron",
    day_of_week="sun",
    hour=3,
)
scheduler.add_job(
    lambda: asyncio.create_task(publish_task("stale_rule_detector", {"dry_run": True})),
    "cron",
    day_of_week="mon",
    hour=2,
)
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_task("user_story_completeness_check", {"dry_run": True})
    ),
    "cron",
    hour=4,
)  # daily
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_task("onboarding_path_optimization", {"dry_run": True})
    ),
    "cron",
    day_of_week="mon",
    hour=5,
)

# Git History Analysis tasks
# Daily analysis at 6 AM
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_git_history_job(
            {
                "since": "1 day ago",
                "max_commits": 50,
                "output_format": "summary",
                "create_memory_node": True,
                "memory_namespace": "daily_analysis",
                "memory_tags": ["daily", "automated"],
                "summarize": True,
                "include_diff": False,
            }
        )
    ),
    "cron",
    hour=6,
)

# Weekly analysis on Monday at 7 AM
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_git_history_job(
            {
                "since": "1 week ago",
                "max_commits": 100,
                "output_format": "summary",
                "create_memory_node": True,
                "memory_namespace": "weekly_analysis",
                "memory_tags": ["weekly", "retrospective"],
                "summarize": True,
                "include_diff": False,
            }
        )
    ),
    "cron",
    day_of_week="mon",
    hour=7,
)

# Sprint analysis every 2 weeks on Monday at 8 AM
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_git_history_job(
            {
                "since": "2 weeks ago",
                "max_commits": 200,
                "output_format": "summary",
                "create_memory_node": True,
                "memory_namespace": "sprint_analysis",
                "memory_tags": ["sprint", "retrospective"],
                "summarize": True,
                "include_diff": False,
            }
        )
    ),
    "cron",
    day_of_week="mon",
    hour=8,
)

# Monthly detailed analysis on the 1st of each month at 9 AM
scheduler.add_job(
    lambda: asyncio.create_task(
        publish_git_history_job(
            {
                "since": "1 month ago",
                "max_commits": 500,
                "output_format": "json",
                "create_memory_node": True,
                "memory_namespace": "monthly_analysis",
                "memory_tags": ["monthly", "detailed"],
                "summarize": True,
                "include_diff": True,
            }
        )
    ),
    "cron",
    day=1,
    hour=9,
)

if __name__ == "__main__":
    logger.info("Starting maintenance scheduler...")
    try:
        asyncio.run(scheduler.start())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
