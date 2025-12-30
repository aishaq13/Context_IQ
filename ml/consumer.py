"""ML entry point for Kafka consumer."""

import asyncio
import logging
import sys
import os

# /app already has the app/ directory and modules at the root, so no path adjustment needed

from app.consumers.kafka_consumer import EventConsumer
from app.utils.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for ML consumer service."""
    consumer = EventConsumer()
    
    try:
        await consumer.initialize()
        await consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await consumer.close()


if __name__ == "__main__":
    asyncio.run(main())
