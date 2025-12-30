"""AWS Bedrock client for LLM-based contextual reasoning."""

import json
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.utils.config import config

logger = logging.getLogger(__name__)


class BedrockClient:
    """Handles interactions with AWS Bedrock for contextual recommendation scoring."""
    
    def __init__(self):
        self.client = None
        self.available = False
    
    async def initialize(self) -> None:
        """Initialize Bedrock client if credentials are available."""
        if not config.is_bedrock_available():
            logger.warning(
                "AWS Bedrock credentials not configured. "
                "LLM-based scoring will be disabled. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to enable."
            )
            self.available = False
            return
        
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=config.AWS_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
            self.available = True
            logger.info(f"Bedrock client initialized for region {config.AWS_REGION}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.available = False
    
    async def score_contextual_relevance(
        self,
        user_profile: Dict[str, Any],
        content: Dict[str, Any],
        interaction_history: Optional[list] = None
    ) -> Optional[float]:
        """
        Score the contextual relevance of content for a user using Claude.
        
        Args:
            user_profile: User's profile and preferences
            content: Content item to score
            interaction_history: Recent user interactions for context
        
        Returns:
            Relevance score between 0 and 1, or None if Bedrock is unavailable
        """
        if not self.available or not self.client:
            logger.debug("Bedrock not available, skipping LLM scoring")
            return None
        
        try:
            prompt = self._build_scoring_prompt(
                user_profile,
                content,
                interaction_history
            )
            
            response = self.client.invoke_model(
                modelId=config.BEDROCK_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": 100,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            score = self._extract_score(response_body)
            
            if score is not None:
                logger.debug(f"LLM relevance score: {score}")
                return score
            
            return None
        
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"Bedrock connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during LLM scoring: {e}")
            return None
    
    def _build_scoring_prompt(
        self,
        user_profile: Dict[str, Any],
        content: Dict[str, Any],
        interaction_history: Optional[list]
    ) -> str:
        """
        Build a prompt for Claude to score content relevance.
        
        Args:
            user_profile: User preferences and interests
            content: Content to evaluate
            interaction_history: Recent user interactions
        
        Returns:
            Formatted prompt string
        """
        interests = ", ".join(user_profile.get("interests", []))
        content_tags = ", ".join(content.get("tags", []))
        
        recent_interactions = ""
        if interaction_history:
            recent_interactions = f"\nRecent interactions: {len(interaction_history)} items viewed in this category"
        
        prompt = f"""You are a content recommendation system. Score how relevant this content is to the user.

USER PROFILE:
- Interests: {interests}
- Interaction count: {user_profile.get('interaction_count', 0)}

CONTENT:
- Title: {content.get('title', 'N/A')}
- Category: {content.get('category', 'N/A')}
- Tags: {content_tags}
- Description: {content.get('description', 'N/A')[:200]}

{recent_interactions}

Provide a relevance score as a single number between 0 and 1 (e.g., 0.75).
Only respond with the numeric score, nothing else."""
        
        return prompt
    
    @staticmethod
    def _extract_score(response_body: Dict[str, Any]) -> Optional[float]:
        """
        Extract numeric score from Bedrock response.
        
        Args:
            response_body: Response from Bedrock API
        
        Returns:
            Float score between 0 and 1, or None if extraction fails
        """
        try:
            # Claude responses are in content array
            if "content" in response_body:
                content = response_body["content"]
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get("text", "").strip()
                    score = float(text)
                    # Clamp to [0, 1]
                    return max(0.0, min(1.0, score))
            
            return None
        except (ValueError, KeyError, IndexError, TypeError) as e:
            logger.warning(f"Failed to extract score from response: {e}")
            return None


# Global Bedrock client instance
bedrock_client = BedrockClient()
