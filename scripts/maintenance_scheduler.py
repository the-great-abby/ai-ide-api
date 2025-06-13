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

async def publish_task(task, args=None, broker: MessageBrokerBase = None):
    if broker is None:
        broker = RealRabbitMQClient(f"amqp://user:password@{RABBITMQ_HOST}:5672/")
    body = {"task": task, "args": args or {}}
    await broker.publish(QUEUE_NAME, body)
    logger.info(f"[PUBLISHED] task={task} args={args}")

scheduler = AsyncIOScheduler()

scheduler.add_job(lambda: asyncio.create_task(publish_task("memory_cleanup", {"dry_run": True})), 'cron', day_of_week='sun', hour=2)
scheduler.add_job(lambda: asyncio.create_task(publish_task("memory_refinement", {"dry_run": True})), 'cron', day_of_week='sun', hour=3)
scheduler.add_job(lambda: asyncio.create_task(publish_task("stale_rule_detector", {"dry_run": True})), 'cron', day_of_week='mon', hour=2)
scheduler.add_job(lambda: asyncio.create_task(publish_task("user_story_completeness_check", {"dry_run": True})), 'cron', hour=4)  # daily
scheduler.add_job(lambda: asyncio.create_task(publish_task("onboarding_path_optimization", {"dry_run": True})), 'cron', day_of_week='mon', hour=5)

if __name__ == "__main__":
    logger.info("Starting maintenance scheduler...")
    try:
        asyncio.run(scheduler.start())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.") 