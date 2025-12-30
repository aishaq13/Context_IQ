"""Redis caching service for recommendations."""

import json
import logging
from typing import Optional, List, Dict, Any
import redis
from redis.asyncio import Redis
from app.utils.config import config

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Manages caching of recommendations and user data in Redis."""
    
    def __init__(self):
        self.client: Optional[Redis] = None
        self.ttl = config.CACHE_TTL
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.client = await Redis.from_url(
                config.REDIS_URL,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=10
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Redis connection established: {config.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    def _get_recommendation_key(self, user_id: str) -> str:
        """Generate cache key for user recommendations."""
        return f"recommendations:{user_id}"
    
    def _get_user_profile_key(self, user_id: str) -> str:
        """Generate cache key for user profile."""
        return f"user_profile:{user_id}"
    
    def _get_embedding_key(self, entity_id: str, entity_type: str) -> str:
        """Generate cache key for embeddings."""
        return f"embedding:{entity_type}:{entity_id}"
    
    async def cache_recommendations(
        self,
        user_id: str,
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache personalized recommendations for a user.
        
        Args:
            user_id: User identifier
            recommendations: List of recommendation dictionaries
        
        Returns:
            True if caching succeeded
        """
        if not self.client:
            logger.warning("Redis client not initialized")
            return False
        
        try:
            key = self._get_recommendation_key(user_id)
            value = json.dumps(recommendations)
            await self.client.setex(key, self.ttl, value)
            logger.debug(f"Cached recommendations for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache recommendations: {e}")
            return False
    
    async def get_cached_recommendations(
        self,
        user_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached recommendations for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of recommendations or None if not cached
        """
        if not self.client:
            return None
        
        try:
            key = self._get_recommendation_key(user_id)
            value = await self.client.get(key)
            if value:
                logger.debug(f"Retrieved cached recommendations for user {user_id}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve cached recommendations: {e}")
            return None
    
    async def invalidate_recommendations(self, user_id: str) -> bool:
        """
        Invalidate cached recommendations for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if invalidation succeeded
        """
        if not self.client:
            return False
        
        try:
            key = self._get_recommendation_key(user_id)
            await self.client.delete(key)
            logger.debug(f"Invalidated cache for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    async def cache_user_profile(
        self,
        user_id: str,
        profile: Dict[str, Any]
    ) -> bool:
        """Cache user profile data."""
        if not self.client:
            return False
        
        try:
            key = self._get_user_profile_key(user_id)
            value = json.dumps(profile)
            await self.client.setex(key, self.ttl * 2, value)  # Longer TTL for profiles
            return True
        except Exception as e:
            logger.error(f"Failed to cache user profile: {e}")
            return False
    
    async def get_cached_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached user profile."""
        if not self.client:
            return None
        
        try:
            key = self._get_user_profile_key(user_id)
            value = await self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Failed to retrieve user profile: {e}")
            return None


# Global Redis cache instance
redis_cache = RedisCacheService()
