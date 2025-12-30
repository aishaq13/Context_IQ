"""ML training and evaluation module."""

import logging
import asyncio
import numpy as np
from typing import List, Tuple, Dict
from app.models.recommender import RecommenderModel
from app.utils.config import config

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self):
        self.model = RecommenderModel()
        self.training_history = []
    
    def evaluate_model(
        self,
        test_interactions: List[Tuple[int, int, float]],
        k: int = 10
    ) -> Dict[str, float]:
        """
        Evaluate model on test set.
        
        Computes:
        - RMSE: Root mean squared error on predicted ratings
        - Accuracy: Percentage of correct predictions within tolerance
        
        Args:
            test_interactions: Test set of (user_idx, content_idx, weight)
            k: Context length for evaluation
        
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model.user_embeddings is None:
            logger.warning("Model not trained yet")
            return {}
        
        predictions = []
        actuals = []
        
        for user_idx, content_idx, actual_weight in test_interactions:
            user_vec = self.model.user_embeddings[user_idx]
            content_vec = self.model.content_embeddings[content_idx]
            
            # Predict score
            similarity = torch.nn.functional.cosine_similarity(
                user_vec.unsqueeze(0),
                content_vec.unsqueeze(0)
            ).item()
            predicted = (similarity + 1) / 2
            
            predictions.append(predicted)
            actuals.append(actual_weight)
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Compute metrics
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        mae = np.mean(np.abs(predictions - actuals))
        accuracy = np.mean(np.abs(predictions - actuals) < 0.2)  # Within 0.2
        
        metrics = {
            "rmse": float(rmse),
            "mae": float(mae),
            "accuracy": float(accuracy),
            "test_samples": len(test_interactions)
        }
        
        logger.info(f"Evaluation metrics: {metrics}")
        return metrics
    
    @staticmethod
    def compute_relevance_accuracy(
        predicted_scores: Dict[str, float],
        ground_truth_relevant: set,
        top_k: int = 10
    ) -> float:
        """
        Compute accuracy of recommendation ranking.
        
        Measures what percentage of top-k recommendations are actually relevant.
        Target: 75% (meaning 7.5 out of 10 top recommendations are correct)
        
        Args:
            predicted_scores: Dict mapping content_id to score
            ground_truth_relevant: Set of content_ids user is known to like
            top_k: Number of top recommendations to evaluate
        
        Returns:
            Accuracy score between 0 and 1
        """
        # Get top-k by score
        top_k_items = sorted(
            predicted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        top_k_ids = {item[0] for item in top_k_items}
        
        # Compute hit rate
        hits = len(top_k_ids & ground_truth_relevant)
        accuracy = hits / top_k if top_k > 0 else 0
        
        logger.info(f"Relevance accuracy: {accuracy:.2%} ({hits}/{top_k})")
        return accuracy


class EmbeddingGenerator:
    """Generates and manages embeddings for users and content."""
    
    @staticmethod
    def generate_from_interactions(
        interactions: List[Tuple[str, str, float]],
        embedding_dim: int = config.EMBEDDING_DIM
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        Generate embeddings from interaction data using simple averaging.
        
        Args:
            interactions: List of (user_id, content_id, weight)
            embedding_dim: Dimension of output embeddings
        
        Returns:
            Tuple of (user_embeddings_dict, content_embeddings_dict)
        """
        user_vecs = {}
        content_vecs = {}
        
        # Initialize random embeddings
        for user_id, _, _ in interactions:
            if user_id not in user_vecs:
                user_vecs[user_id] = np.random.randn(embedding_dim) * 0.01
        
        for _, content_id, _ in interactions:
            if content_id not in content_vecs:
                content_vecs[content_id] = np.random.randn(embedding_dim) * 0.01
        
        return user_vecs, content_vecs


import torch


class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self):
        self.model = RecommenderModel()
        self.training_history = []
    
    def evaluate_model(
        self,
        test_interactions: List[Tuple[int, int, float]],
        k: int = 10
    ) -> Dict[str, float]:
        """
        Evaluate model on test set.
        
        Computes:
        - RMSE: Root mean squared error on predicted ratings
        - Accuracy: Percentage of correct predictions within tolerance
        
        Args:
            test_interactions: Test set of (user_idx, content_idx, weight)
            k: Context length for evaluation
        
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model.user_embeddings is None:
            logger.warning("Model not trained yet")
            return {}
        
        predictions = []
        actuals = []
        
        for user_idx, content_idx, actual_weight in test_interactions:
            user_vec = self.model.user_embeddings[user_idx]
            content_vec = self.model.content_embeddings[content_idx]
            
            # Predict score
            similarity = torch.nn.functional.cosine_similarity(
                user_vec.unsqueeze(0),
                content_vec.unsqueeze(0)
            ).item()
            predicted = (similarity + 1) / 2
            
            predictions.append(predicted)
            actuals.append(actual_weight)
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Compute metrics
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        mae = np.mean(np.abs(predictions - actuals))
        accuracy = np.mean(np.abs(predictions - actuals) < 0.2)  # Within 0.2
        
        metrics = {
            "rmse": float(rmse),
            "mae": float(mae),
            "accuracy": float(accuracy),
            "test_samples": len(test_interactions)
        }
        
        logger.info(f"Evaluation metrics: {metrics}")
        return metrics
    
    @staticmethod
    def compute_relevance_accuracy(
        predicted_scores: Dict[str, float],
        ground_truth_relevant: set,
        top_k: int = 10
    ) -> float:
        """
        Compute accuracy of recommendation ranking.
        
        Measures what percentage of top-k recommendations are actually relevant.
        Target: 75% (meaning 7.5 out of 10 top recommendations are correct)
        
        Args:
            predicted_scores: Dict mapping content_id to score
            ground_truth_relevant: Set of content_ids user is known to like
            top_k: Number of top recommendations to evaluate
        
        Returns:
            Accuracy score between 0 and 1
        """
        # Get top-k by score
        top_k_items = sorted(
            predicted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        top_k_ids = {item[0] for item in top_k_items}
        
        # Compute hit rate
        hits = len(top_k_ids & ground_truth_relevant)
        accuracy = hits / top_k if top_k > 0 else 0
        
        logger.info(f"Relevance accuracy: {accuracy:.2%} ({hits}/{top_k})")
        return accuracy
