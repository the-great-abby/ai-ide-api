#!/usr/bin/env python3
"""
Publish Sales Update Job

Script to publish sales presentation update jobs to the RabbitMQ queue
for processing by the sales presentation updater worker.
"""

import os
import json
import argparse
import logging
import pika
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def publish_sales_update_job(job_config: Dict[str, Any]) -> bool:
    """Publish a sales presentation update job to RabbitMQ"""
    try:
        # RabbitMQ connection
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://user:password@rabbitmq:5672/")
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()
        
        # Ensure queue exists
        queue_name = "sales.presentation.update"
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Prepare job message
        job_message = {
            "type": "sales_presentation_update",
            "timestamp": datetime.now().isoformat(),
            "config": job_config
        }
        
        # Publish job
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(job_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        logger.info(f"Sales presentation update job published to queue: {queue_name}")
        logger.info(f"Job config: {job_config}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"Error publishing sales update job: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Publish sales presentation update job")
    parser.add_argument("--since", default="1 week ago", help="Time period to analyze (e.g., '1 week ago')")
    parser.add_argument("--dry-run", default="false", help="Run in dry-run mode (true/false)")
    parser.add_argument("--review", default="false", help="Enable human review (true/false)")
    parser.add_argument("--analysis-focus", nargs="+", 
                       default=["new_features", "capability_improvements", "performance_enhancements", "user_experience_updates"],
                       help="Focus areas for analysis")
    parser.add_argument("--presentation-sections", nargs="+",
                       default=["system_architecture", "memory_system", "ai_augmented_code_review", 
                               "frictionless_onboarding", "seamless_test_environment", "error_handling_debugging", "demo_examples"],
                       help="Presentation sections to update")
    
    args = parser.parse_args()
    
    # Prepare job configuration
    job_config = {
        "since": args.since,
        "dry_run": args.dry_run.lower() == "true",
        "review": args.review.lower() == "true",
        "analysis_focus": args.analysis_focus,
        "presentation_sections": args.presentation_sections
    }
    
    # Publish job
    success = publish_sales_update_job(job_config)
    
    if success:
        print("✅ Sales presentation update job published successfully")
        print(f"📋 Job details:")
        print(f"   - Time period: {args.since}")
        print(f"   - Dry run: {args.dry_run}")
        print(f"   - Review enabled: {args.review}")
        print(f"   - Analysis focus: {', '.join(args.analysis_focus)}")
        print(f"   - Sections: {', '.join(args.presentation_sections)}")
    else:
        print("❌ Failed to publish sales presentation update job")
        exit(1)

if __name__ == "__main__":
    main() 