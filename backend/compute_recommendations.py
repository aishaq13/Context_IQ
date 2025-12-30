"""
Compute initial recommendations for all seeded users.
Run this after seeding data to populate the recommendations table.
"""

import os
import sys
import json
from app.db.database import db_manager
from app.models.recommender import RecommenderModel
from app.utils.config import config

# Initialize database
os.environ.setdefault("DB_HOST", "postgres")

def get_all_interactions():
    """Fetch all interactions from database."""
    query = """
        SELECT user_id, content_id, interaction_type
        FROM interactions
        ORDER BY user_id, created_at
    """
    return db_manager.execute_query(query)

def get_all_users():
    """Get list of all users."""
    query = "SELECT user_id FROM users ORDER BY user_id"
    results = db_manager.execute_query(query)
    return [row[0] for row in results]

def get_all_content():
    """Get list of all content."""
    query = "SELECT content_id FROM content ORDER BY content_id"
    results = db_manager.execute_query(query)
    return [row[0] for row in results]

def compute_and_save_recommendations():
    """Train model and compute recommendations for all users."""
    print("📊 Computing recommendations...")
    
    # Initialize database manager pool
    import psycopg2.pool
    if not db_manager.pool:
        db_url = f"postgresql://contextiq_user:contextiq_pass@{os.environ.get('DB_HOST', 'postgres')}:5432/contextiq"
        db_manager.pool = psycopg2.pool.SimpleConnectionPool(
            2, 20, 
            db_url,
            connect_timeout=10
        )
    
    # Fetch data
    interactions = get_all_interactions()
    users = get_all_users()
    content = get_all_content()
    
    print(f"  Users: {len(users)}")
    print(f"  Content: {len(content)}")
    print(f"  Interactions: {len(interactions)}")
    
    if not interactions:
        print("  ❌ No interactions to train on!")
        return
    
    # Initialize model
    model = RecommenderModel(embedding_dim=config.EMBEDDING_DIM)
    
    # Initialize embeddings with user and content dimensions
    model.initialize_embeddings(users, content)
    
    # Train model on interactions
    print("\n  Training model...")
    
    # Convert interactions to format: (user_idx, content_idx, weight)
    interaction_weights = {
        "view": 0.5,
        "like": 1.0,
        "save": 0.8,
        "share": 1.0
    }
    
    weighted_interactions = []
    for user_id, content_id, interaction_type in interactions:
        user_idx = model.user_id_to_idx.get(user_id)
        content_idx = model.content_id_to_idx.get(content_id)
        weight = interaction_weights.get(interaction_type, 0.5)
        
        if user_idx is not None and content_idx is not None:
            weighted_interactions.append((user_idx, content_idx, weight))
    
    model.train_on_interactions(weighted_interactions)
    print("  ✓ Model trained")
    
    # Compute and save recommendations
    print("\n  Computing recommendations for all users...")
    
    # Clear existing recommendations
    delete_query = "DELETE FROM recommendations"
    db_manager.execute_update(delete_query)
    
    insert_query = """
        INSERT INTO recommendations (user_id, content_id, ml_score, combined_score, created_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    """
    
    total_recs = 0
    for user_id in users:
        # Get top 10 recommendations for this user
        user_idx = model.user_id_to_idx.get(user_id)
        
        if user_idx is None:
            continue
        
        # Score all content for this user
        scores = []
        for content_id in content:
            content_idx = model.content_id_to_idx.get(content_id)
            
            if content_idx is None:
                continue
            
            try:
                score = model.predict_score(user_idx, content_idx)
                scores.append((content_id, score))
            except:
                scores.append((content_id, 0.0))
        
        # Sort by score descending and take top 10
        scores.sort(key=lambda x: x[1], reverse=True)
        top_scores = scores[:10]
        
        # Save to database
        for content_id, ml_score in top_scores:
            db_manager.execute_insert(
                insert_query,
                (user_id, content_id, float(ml_score), float(ml_score))
            )
            total_recs += 1
    
    print(f"  ✓ Computed {total_recs} recommendations")
    
    # Verify
    verify_query = "SELECT COUNT(*) FROM recommendations"
    result = db_manager.execute_query(verify_query)
    count = result[0][0] if result else 0
    print(f"\n✓ Recommendations in database: {count}")

if __name__ == "__main__":
    try:
        compute_and_save_recommendations()
        print("\n✅ Recommendations computation complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
