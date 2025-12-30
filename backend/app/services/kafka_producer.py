"""Kafka producer for publishing user events."""

import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.utils.config import config

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Handles publishing events to Kafka topics."""
    
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
    
    async def initialize(self) -> None:
        """Initialize Kafka producer with proper error handling."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                request_timeout_ms=10000
            )
            logger.info(f"Kafka producer initialized with servers: {config.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    async def close(self) -> None:
        """Close the producer gracefully."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")
    
    async def publish_user_event(
        self,
        user_id: str,
        content_id: str,
        interaction_type: str,
        duration_seconds: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish a user interaction event to Kafka.
        
        Args:
            user_id: User identifier
            content_id: Content identifier
            interaction_type: Type of interaction (view, like, share, save)
            duration_seconds: Time spent on content
            metadata: Additional context data
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.warning("Producer not initialized, skipping event publishing")
            return False
        
        event = {
            "user_id": user_id,
            "content_id": content_id,
            "interaction_type": interaction_type,
            "duration_seconds": duration_seconds,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        }
        
        try:
            future = self.producer.send(
                config.KAFKA_TOPIC_USER_EVENTS,
                value=event
            )
            
            # Wait for send to complete with timeout
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Event published to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"at offset {record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")
            return False
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Global Kafka producer instance
kafka_producer = KafkaProducerService()
