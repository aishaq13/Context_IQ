"""Environment variables configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # Database
    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "contextiq_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "contextiq_pass")
    DB_NAME = os.getenv("DB_NAME", "contextiq")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_TTL_RECOMMENDATIONS = int(os.getenv("REDIS_TTL_RECOMMENDATIONS", "300"))
    REDIS_TTL_PROFILES = int(os.getenv("REDIS_TTL_PROFILES", "600"))
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_USER_EVENTS_TOPIC = os.getenv("KAFKA_USER_EVENTS_TOPIC", "user_events")
    
    # ML Model
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "32"))
    ML_LEARNING_RATE = float(os.getenv("ML_LEARNING_RATE", "0.01"))
    ML_EPOCHS = int(os.getenv("ML_EPOCHS", "5"))
    
    # AWS Bedrock
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    
    # API
    API_V1_PREFIX = "/api/v1"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
