"""Kafka consumer for processing user events and training ML model."""

import json
import logging
import asyncio
from typing import List, Tuple, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import psycopg2
from app.utils.config import config
from app.models.recommender import RecommenderModel
from app.services.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumes user interaction events from Kafka.
    
    Processes events and:
    - Accumulates interaction data
    - Periodically retrains ML model
    - Scores content with LLM if available
    - Saves recommendations to database
    """
    
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.db_connection = None
        self.model = RecommenderModel()
        self.bedrock_client = BedrockClient()
        self.events_buffer = []
        self.buffer_size = 50
        self.model_update_counter = 0
    
    async def initialize(self) -> None:
        """Initialize Kafka consumer and database connection."""
        try:
            # Initialize Kafka consumer
            self.consumer = KafkaConsumer(
                config.KAFKA_TOPIC_USER_EVENTS,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='ml-consumer-group',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                session_timeout_ms=30000,
                max_poll_records=100
            )
            logger.info(f"Kafka consumer initialized for topic: {config.KAFKA_TOPIC_USER_EVENTS}")
            
            # Initialize database connection
            self.db_connection = psycopg2.connect(config.DATABASE_URL)
            logger.info("Database connection established for ML consumer")
            
            # Initialize Bedrock
            await self.bedrock_client.initialize()
        
        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            raise
    
    async def close(self) -> None:
        """Close consumer and database connections."""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")
    
    async def start_consuming(self) -> None:
        """
        Start consuming events from Kafka.
        
        Processes events in batches and periodically trains the model.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not initialized")
        
        logger.info("Starting event consumer...")
        
        try:
            for message in self.consumer:
                event = message.value
                self.events_buffer.append(event)
                
                logger.debug(f"Event received: {event['user_id']} -> {event['content_id']}")
                
                # Process batch when buffer reaches size
                if len(self.events_buffer) >= self.buffer_size:
                    await self.process_batch()
                
                # Periodic model update
                self.model_update_counter += 1
                if self.model_update_counter >= config.MODEL_UPDATE_INTERVAL:
                    await self.retrain_model()
                    self.model_update_counter = 0
        
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in consumer loop: {e}")
    
    async def process_batch(self) -> None:
        """Process accumulated events and save interactions."""
        if not self.events_buffer:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            for event in self.events_buffer:
                # Insert interaction
                insert_query = """
                    INSERT INTO interactions (user_id, content_id, interaction_type, duration_seconds, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT DO NOTHING
                """
                
                cursor.execute(
                    insert_query,
                    (
                        event['user_id'],
                        event['content_id'],
                        event['interaction_type'],
                        event.get('duration_seconds', 0)
                    )
                )
            
            self.db_connection.commit()
            logger.info(f"Processed batch of {len(self.events_buffer)} events")
            self.events_buffer.clear()
        
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error processing batch: {e}")
    
    async def retrain_model(self) -> None:
        """Retrain embeddings using recent interaction data."""
        try:
            logger.info("Starting model retraining...")
            
            # Fetch all users and content
            cursor = self.db_connection.cursor()
            
            cursor.execute("SELECT DISTINCT user_id FROM interactions")
            users = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT content_id FROM content")
            content = [row[0] for row in cursor.fetchall()]
            
            if not users or not content:
                logger.warning("Insufficient data for model training")
                return
            
            # Initialize embeddings
            self.model.initialize_embeddings(users, content)
            
            # Fetch interactions with weights
            cursor.execute("""
                SELECT user_id, content_id, COUNT(*) as interaction_count
                FROM interactions
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY user_id, content_id
            """)
            
            interactions = []
            for user_id, content_id, count in cursor.fetchall():
                # Weight based on interaction frequency
                weight = min(1.0, count / 10.0)
                user_idx = self.model.user_id_to_idx[user_id]
                content_idx = self.model.content_id_to_idx[content_id]
                interactions.append((user_idx, content_idx, weight))
            
            # Train model
            losses, final_loss = self.model.train_on_interactions(
                interactions,
                learning_rate=0.01,
                epochs=5
            )
            
            logger.info(f"Model trained. Final loss: {final_loss:.4f}")
            
            # Compute and save recommendations
            await self._compute_and_save_recommendations()
            
            # Save model
            self.model.save_embeddings("models/embeddings.npy")
        
        except Exception as e:
            logger.error(f"Error during model retraining: {e}")
    
    async def _compute_and_save_recommendations(self) -> None:
        """Compute recommendations for all users and save to database."""
        try:
            cursor = self.db_connection.cursor()
            
            # Get all users
            cursor.execute("SELECT DISTINCT user_id FROM interactions")
            users = [row[0] for row in cursor.fetchall()]
            
            # Get all content
            cursor.execute("SELECT DISTINCT content_id FROM content")
            all_content_ids = [row[0] for row in cursor.fetchall()]
            
            recommendations_to_save = []
            
            for user_id in users:
                # Get ML scores from model
                ml_scores = self.model.predict_scores(user_id, all_content_ids)
                
                # Get user profile for LLM context
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM interactions
                    WHERE user_id = %s
                """, (user_id,))
                interaction_count = cursor.fetchone()[0]
                
                user_profile = {
                    "user_id": user_id,
                    "interaction_count": interaction_count,
                    "interests": self._get_user_interests(cursor, user_id)
                }
                
                for content_id in all_content_ids:
                    ml_score = ml_scores.get(content_id, 0.5)
                    
                    # Get LLM score if available
                    llm_score = None
                    if self.bedrock_client.available and ml_score > 0.3:
                        # Only score promising candidates with LLM
                        content = self._get_content_info(cursor, content_id)
                        if content:
                            llm_score = await self.bedrock_client.score_contextual_relevance(
                                user_profile,
                                content
                            )
                    
                    # Blend scores
                    combined_score = self._blend_scores(ml_score, llm_score)
                    
                    recommendations_to_save.append({
                        "user_id": user_id,
                        "content_id": content_id,
                        "ml_score": ml_score,
                        "llm_score": llm_score,
                        "combined_score": combined_score
                    })
            
            # Batch insert recommendations
            self._save_recommendations_batch(cursor, recommendations_to_save)
            self.db_connection.commit()
            
            logger.info(f"Saved {len(recommendations_to_save)} recommendations")
        
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Error computing recommendations: {e}")
    
    @staticmethod
    def _blend_scores(ml_score: float, llm_score: Optional[float]) -> float:
        """
        Blend ML and LLM scores for final recommendation ranking.
        
        Weights: ML 60%, LLM 40%
        """
        if llm_score is None:
            return ml_score
        
        blended = (
            config.ML_SCORE_WEIGHT * ml_score +
            config.LLM_SCORE_WEIGHT * llm_score
        )
        return min(1.0, max(0.0, blended))
    
    @staticmethod
    def _get_user_interests(cursor, user_id: str) -> List[str]:
        """Get top interest categories for a user."""
        cursor.execute("""
            SELECT DISTINCT c.category
            FROM interactions i
            JOIN content c ON i.content_id = c.content_id
            WHERE i.user_id = %s
            LIMIT 10
        """, (user_id,))
        return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def _get_content_info(cursor, content_id: str) -> Optional[dict]:
        """Get content information from database."""
        cursor.execute("""
            SELECT content_id, title, category, description, tags
            FROM content
            WHERE content_id = %s
        """, (content_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                "content_id": result[0],
                "title": result[1],
                "category": result[2],
                "description": result[3],
                "tags": json.loads(result[4]) if result[4] else []
            }
        return None
    
    @staticmethod
    def _save_recommendations_batch(cursor, recommendations: List[dict]) -> None:
        """Save all recommendations in a single batch operation."""
        for rec in recommendations:
            cursor.execute("""
                INSERT INTO recommendations (user_id, content_id, ml_score, llm_score, combined_score, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, content_id) DO UPDATE
                SET ml_score = EXCLUDED.ml_score,
                    llm_score = EXCLUDED.llm_score,
                    combined_score = EXCLUDED.combined_score,
                    created_at = CURRENT_TIMESTAMP
            """, (
                rec["user_id"],
                rec["content_id"],
                rec["ml_score"],
                rec["llm_score"],
                rec["combined_score"]
            ))
