"""API routes for Context IQ."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from app.db.database import db_manager
from app.services.kafka_producer import kafka_producer
from app.services.redis_cache import redis_cache
from app.services.bedrock_client import bedrock_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


# Pydantic models for request/response validation
class InteractionRequest(BaseModel):
    """Request model for user interaction."""
    user_id: str = Field(..., description="User identifier")
    content_id: str = Field(..., description="Content identifier")
    interaction_type: str = Field(..., description="Type: view, like, share, save")
    duration_seconds: int = Field(0, description="Time spent on content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RecommendationResponse(BaseModel):
    """Response model for a single recommendation."""
    content_id: str
    title: str
    category: str
    ml_score: float
    llm_score: Optional[float]
    combined_score: float


class RecommendationsListResponse(BaseModel):
    """Response model for recommendations list."""
    user_id: str
    recommendations: List[RecommendationResponse]
    cached: bool
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    services: Dict[str, bool]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """
    Check service health and dependencies.
    
    Returns status of API and connected services (database, Redis, Kafka).
    """
    services_status = {
        "database": False,
        "redis": False,
        "kafka": False,
        "bedrock": bedrock_client.available
    }
    
    # Check database
    try:
        results = db_manager.execute_query("SELECT 1")
        services_status["database"] = len(results) > 0
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
    
    # Check Redis
    if redis_cache.client:
        try:
            await redis_cache.client.ping()
            services_status["redis"] = True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
    
    # Check Kafka
    if kafka_producer.producer:
        services_status["kafka"] = True
    
    overall_status = "healthy" if all(services_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        services=services_status
    )


@router.post("/interact", summary="Log user interaction")
async def log_interaction(request: InteractionRequest):
    """
    Log a user interaction with content.
    
    - Records interaction in PostgreSQL
    - Publishes event to Kafka for ML processing
    - Invalidates cached recommendations
    
    **Request body:**
    - `user_id`: Unique user identifier
    - `content_id`: Unique content identifier
    - `interaction_type`: One of [view, like, share, save]
    - `duration_seconds`: Time spent (optional, for views)
    - `metadata`: Additional context (optional)
    """
    try:
        # Ensure user exists
        user_query = "SELECT id FROM users WHERE user_id = %s"
        user_result = db_manager.execute_query(user_query, (request.user_id,))
        
        if not user_result:
            # Create user
            insert_user_query = """
                INSERT INTO users (user_id, created_at, updated_at)
                VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """
            db_manager.execute_insert(
                insert_user_query,
                (request.user_id,)
            )
        
        # Ensure content exists (assume it's already in the system)
        content_query = "SELECT id FROM content WHERE content_id = %s"
        content_result = db_manager.execute_query(
            content_query,
            (request.content_id,)
        )
        
        if not content_result:
            logger.warning(f"Content {request.content_id} not found in database")
        
        # Insert interaction
        interaction_query = """
            INSERT INTO interactions (user_id, content_id, interaction_type, duration_seconds, created_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        db_manager.execute_insert(
            interaction_query,
            (
                request.user_id,
                request.content_id,
                request.interaction_type,
                request.duration_seconds
            )
        )
        
        # Publish to Kafka for ML processing
        await kafka_producer.publish_user_event(
            user_id=request.user_id,
            content_id=request.content_id,
            interaction_type=request.interaction_type,
            duration_seconds=request.duration_seconds,
            metadata=request.metadata
        )
        
        # Invalidate cached recommendations
        await redis_cache.invalidate_recommendations(request.user_id)
        
        logger.info(
            f"Interaction logged: {request.user_id} -> {request.content_id} "
            f"({request.interaction_type})"
        )
        
        return {
            "status": "success",
            "message": "Interaction recorded and queued for processing"
        }
    
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to log interaction")


@router.get(
    "/recommendations",
    response_model=RecommendationsListResponse,
    summary="Get personalized recommendations"
)
async def get_recommendations(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(10, ge=1, le=100, description="Number of recommendations")
):
    """
    Get personalized content recommendations for a user.
    
    - Returns cached recommendations if available (TTL: 5 minutes)
    - Otherwise computes recommendations from embeddings and LLM scores
    - Blends ML score (60%) and LLM score (40%) for final ranking
    
    **Query parameters:**
    - `user_id`: User to get recommendations for
    - `limit`: Maximum number of recommendations (default: 10)
    """
    try:
        # Check cache first
        cached = await redis_cache.get_cached_recommendations(user_id)
        if cached:
            return RecommendationsListResponse(
                user_id=user_id,
                recommendations=cached[:limit],
                cached=True,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Fetch user interaction history
        history_query = """
            SELECT content_id, interaction_type, created_at
            FROM interactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """
        interaction_history = db_manager.execute_query(
            history_query,
            (user_id,)
        )
        
        if not interaction_history:
            # No interaction history, return empty or popular content
            logger.info(f"No interaction history for user {user_id}")
            recommendations = []
        else:
            # Query recommendations from database (pre-computed by ML consumer)
            recs_query = """
                SELECT content_id, ml_score, llm_score, combined_score
                FROM recommendations
                WHERE user_id = %s
                ORDER BY combined_score DESC
                LIMIT %s
            """
            rec_results = db_manager.execute_query(
                recs_query,
                (user_id, limit)
            )
            
            # Enrich with content details
            recommendations = []
            for content_id, ml_score, llm_score, combined_score in rec_results:
                content_query = """
                    SELECT title, category
                    FROM content
                    WHERE content_id = %s
                """
                content_results = db_manager.execute_query(
                    content_query,
                    (content_id,)
                )
                
                if content_results:
                    title, category = content_results[0]
                    recommendations.append(
                        RecommendationResponse(
                            content_id=content_id,
                            title=title,
                            category=category,
                            ml_score=ml_score or 0.0,
                            llm_score=llm_score,
                            combined_score=combined_score or 0.0
                        )
                    )
        
        # Cache the recommendations
        if recommendations:
            rec_dicts = [r.dict() for r in recommendations]
            await redis_cache.cache_recommendations(user_id, rec_dicts)
        
        return RecommendationsListResponse(
            user_id=user_id,
            recommendations=recommendations,
            cached=False,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.get("/user-profile/{user_id}", summary="Get user profile")
async def get_user_profile(user_id: str):
    """
    Get user profile with interaction statistics.
    
    Returns:
    - Total interactions count
    - Interaction breakdown by type
    - Most viewed categories
    """
    try:
        # Check cache
        cached_profile = await redis_cache.get_cached_user_profile(user_id)
        if cached_profile:
            return {**cached_profile, "cached": True}
        
        # Get interaction counts by type
        count_query = """
            SELECT interaction_type, COUNT(*) as count
            FROM interactions
            WHERE user_id = %s
            GROUP BY interaction_type
        """
        type_counts = db_manager.execute_query(
            count_query,
            (user_id,)
        )
        
        # Get top categories
        categories_query = """
            SELECT c.category, COUNT(*) as count
            FROM interactions i
            JOIN content c ON i.content_id = c.content_id
            WHERE i.user_id = %s
            GROUP BY c.category
            ORDER BY count DESC
            LIMIT 5
        """
        top_categories = db_manager.execute_query(
            categories_query,
            (user_id,)
        )
        
        profile = {
            "user_id": user_id,
            "total_interactions": sum(count[1] for count in type_counts),
            "interaction_breakdown": {
                count[0]: count[1] for count in type_counts
            },
            "top_categories": [
                {"category": cat[0], "count": cat[1]} for cat in top_categories
            ],
            "cached": False
        }
        
        # Cache profile
        await redis_cache.cache_user_profile(user_id, profile)
        
        return profile
    
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")


@router.get("/content", summary="List all content")
async def list_content(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=500)
):
    """List available content with optional filtering."""
    try:
        if category:
            query = """
                SELECT content_id, title, category, description
                FROM content
                WHERE category = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            results = db_manager.execute_query(query, (category, limit))
        else:
            query = """
                SELECT content_id, title, category, description
                FROM content
                ORDER BY created_at DESC
                LIMIT %s
            """
            results = db_manager.execute_query(query, (limit,))
        
        content_list = [
            {
                "content_id": row[0],
                "title": row[1],
                "category": row[2],
                "description": row[3]
            }
            for row in results
        ]
        
        return {"content": content_list, "count": len(content_list)}
    
    except Exception as e:
        logger.error(f"Error listing content: {e}")
        raise HTTPException(status_code=500, detail="Failed to list content")
