import argparse
import os
import asyncio
from utils.message_broker import RealRabbitMQClient

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
QUEUE_NAME = "memory.cleanup"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Publish a memory cleanup job to RabbitMQ"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without deleting"
    )
    parser.add_argument(
        "--age-days", type=int, default=180, help="Age threshold for staleness"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    job_data = {"dry_run": args.dry_run, "age_days": args.age_days}
    broker = RealRabbitMQClient(RABBITMQ_URL)
    await broker.publish(QUEUE_NAME, job_data)
    print(f"Published memory cleanup job: {job_data}")


if __name__ == "__main__":
    asyncio.run(main())
