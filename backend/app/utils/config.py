"""Configuration management for Context IQ backend."""

import os
from typing import Optional

class Config:
    """Application configuration from environment variables."""
    
    # API Configuration
    APP_NAME = "Context IQ"
    APP_VERSION = "1.0.0"
    API_V1_STR = "/api/v1"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://contextiq_user:contextiq_pass@postgres:5432/contextiq"
    )
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "kafka:9092"
    ).split(",")
    KAFKA_TOPIC_USER_EVENTS = "user_events"
    
    # AWS Bedrock Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "claude-3-sonnet-20240229")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # ML Configuration
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "128"))
    MODEL_UPDATE_INTERVAL = int(os.getenv("MODEL_UPDATE_INTERVAL", "3600"))  # 1 hour
    MIN_INTERACTION_COUNT = int(os.getenv("MIN_INTERACTION_COUNT", "5"))
    
    # Relevance Scoring
    ML_SCORE_WEIGHT = float(os.getenv("ML_SCORE_WEIGHT", "0.6"))
    LLM_SCORE_WEIGHT = float(os.getenv("LLM_SCORE_WEIGHT", "0.4"))
    
    @classmethod
    def is_bedrock_available(cls) -> bool:
        """Check if AWS Bedrock credentials are available."""
        return bool(cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY)

config = Config()
