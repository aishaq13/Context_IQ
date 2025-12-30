"""FastAPI main application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.config import config
from app.db.database import db_manager
from app.services.kafka_producer import kafka_producer
from app.services.redis_cache import redis_cache
from app.services.bedrock_client import bedrock_client
from app.api import routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    
    # STARTUP
    logger.info("Starting Context IQ API...")
    
    try:
        # Initialize database
        await db_manager.initialize()
        logger.info("✓ Database initialized")
        
        # Initialize Kafka producer
        await kafka_producer.initialize()
        logger.info("✓ Kafka producer initialized")
        
        # Initialize Redis cache
        await redis_cache.initialize()
        logger.info("✓ Redis cache initialized")
        
        # Initialize Bedrock client (optional)
        await bedrock_client.initialize()
        if bedrock_client.available:
            logger.info("✓ AWS Bedrock client initialized")
        else:
            logger.info("⚠ AWS Bedrock not available (optional)")
        
        logger.info("All services initialized successfully!")
    
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("Shutting down Context IQ API...")
    
    try:
        await kafka_producer.close()
        logger.info("✓ Kafka producer closed")
        
        await redis_cache.close()
        logger.info("✓ Redis cache closed")
        
        await db_manager.close()
        logger.info("✓ Database closed")
    
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=config.APP_NAME,
    description="Personalized content recommendation system with ML and LLM integration",
    version=config.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
