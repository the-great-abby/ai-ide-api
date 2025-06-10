#!/usr/bin/env python3
"""
Maintenance Scheduler
Publishes maintenance/refinement tasks to RabbitMQ at scheduled intervals.
"""
import logging
import json
import pika
from apscheduler.schedulers.blocking import BlockingScheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maintenance_scheduler")

RABBITMQ_HOST = "rabbitmq"  # Adjust if needed
QUEUE_NAME = "maintenance"

# Helper to publish a task message
def publish_task(task, args=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    body = json.dumps({"task": task, "args": args or {}})
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=body)
    logger.info(f"[PUBLISHED] task={task} args={args}")
    connection.close()

# Scheduler setup
scheduler = BlockingScheduler()

# Schedule jobs (adjust times as needed)
scheduler.add_job(lambda: publish_task("memory_cleanup", {"dry_run": True}), 'cron', day_of_week='sun', hour=2)
scheduler.add_job(lambda: publish_task("memory_refinement", {"dry_run": True}), 'cron', day_of_week='sun', hour=3)
scheduler.add_job(lambda: publish_task("stale_rule_detector", {"dry_run": True}), 'cron', day_of_week='mon', hour=2)
scheduler.add_job(lambda: publish_task("user_story_completeness_check", {"dry_run": True}), 'cron', hour=4)  # daily
scheduler.add_job(lambda: publish_task("onboarding_path_optimization", {"dry_run": True}), 'cron', day_of_week='mon', hour=5)

if __name__ == "__main__":
    logger.info("Starting maintenance scheduler...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.") 