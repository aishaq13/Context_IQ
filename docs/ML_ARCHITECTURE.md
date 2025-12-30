"""ML Model Training and Inference Documentation

## Overview

The Context IQ ML system uses a PyTorch-based collaborative filtering model to generate personalized content recommendations.

## Model Architecture

### EmbeddingModel (Neural Network)
- Single embedding layer for users/content
- Dimension: Configurable (default 32)
- Initialization: Normal distribution (std=0.01)

### RecommenderModel
- **User Embeddings:** Learned vectors capturing user preferences
- **Content Embeddings:** Learned vectors capturing content characteristics
- **Scoring:** Dot-product similarity between user and content embeddings

## Training Pipeline

### Data Flow
1. Fetch interactions from database (user_id, content_id, interaction_type)
2. Convert to weighted format (view=0.5, like=1.0, save=0.8, share=1.0)
3. Initialize embeddings with all users and content
4. Train with gradient descent (Adam optimizer, MSE loss)

### Training Configuration
- Learning rate: 0.01
- Epochs: 5
- Batch: All interactions at once

## Inference

### Prediction Score Calculation
```python
score = dot_product(user_embedding, content_embedding)
```

### Top-K Recommendations
- For each user, score all content items
- Sort by score descending
- Return top 10 as recommendations

## Performance Notes

- Training time: ~5-10 seconds on 300 interactions
- Inference time: <1ms per user-content pair
- Memory: ~2-5MB for embeddings (20 users × 50 content × 32 dims)
- Model accuracy improves with more interaction data

## Future Improvements

- Add regularization to prevent overfitting
- Implement mini-batch training for large datasets
- Add user/content features beyond embeddings
- Support cold-start problem with content-based features
- Implement online learning for new interactions
"""
