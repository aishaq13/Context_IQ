"""
Sample data seeding script for Context IQ.

This script populates the database with:
- Sample users
- Sample content
- Sample interactions

Run after docker-compose is up and services are healthy.
"""

import asyncio
import json
import psycopg2
import time
import os
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

# Configuration - use postgres service name when in Docker, localhost otherwise
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_URL = f"postgresql://contextiq_user:contextiq_pass@{DB_HOST}:5432/contextiq"
SAMPLE_USERS = 20
SAMPLE_CONTENT = 50
INTERACTIONS_PER_USER = 15


def create_connection():
    """Create database connection."""
    try:
        conn = psycopg2.connect(DB_URL)
        print("✓ Database connection established")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        raise


def seed_users(conn):
    """Seed sample users."""
    cursor = conn.cursor()
    
    users = [
        (f"user_{i:03d}", f"user{i}@example.com")
        for i in range(1, SAMPLE_USERS + 1)
    ]
    
    query = """
        INSERT INTO users (user_id, email, created_at, updated_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO NOTHING
    """
    
    for user_id, email in users:
        cursor.execute(query, (user_id, email))
    
    conn.commit()
    print(f"✓ Seeded {SAMPLE_USERS} users")


def seed_content(conn):
    """Seed sample content."""
    cursor = conn.cursor()
    
    categories = ["technology", "business", "entertainment", "health", "science"]
    tags_pool = {
        "technology": ["ai", "python", "machine learning", "web development"],
        "business": ["startups", "finance", "marketing", "leadership"],
        "entertainment": ["movies", "music", "gaming", "streaming"],
        "health": ["fitness", "nutrition", "mental health", "wellness"],
        "science": ["physics", "biology", "space", "research"]
    }
    
    query = """
        INSERT INTO content (content_id, title, category, description, tags, created_at)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (content_id) DO NOTHING
    """
    
    for i in range(1, SAMPLE_CONTENT + 1):
        category = categories[i % len(categories)]
        tags = json.dumps(tags_pool[category][:2])
        
        cursor.execute(query, (
            f"content_{i:04d}",
            f"Article {i}: {category.capitalize()} Deep Dive",
            category,
            f"Comprehensive guide about {category}. This article explores key concepts and best practices.",
            tags
        ))
    
    conn.commit()
    print(f"✓ Seeded {SAMPLE_CONTENT} content items")


def seed_interactions(conn):
    """Seed sample user interactions."""
    cursor = conn.cursor()
    
    interaction_types = ["view", "like", "save", "share"]
    
    query = """
        INSERT INTO interactions (user_id, content_id, interaction_type, duration_seconds, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    # Generate interactions
    for user_idx in range(1, SAMPLE_USERS + 1):
        user_id = f"user_{user_idx:03d}"
        
        # Each user has INTERACTIONS_PER_USER interactions
        for idx in range(INTERACTIONS_PER_USER):
            content_idx = (user_idx + idx) % SAMPLE_CONTENT + 1
            content_id = f"content_{content_idx:04d}"
            interaction_type = interaction_types[idx % len(interaction_types)]
            duration = 30 + (idx * 5)  # 30-95 seconds
            
            # Random timestamp in last 30 days
            days_ago = idx % 30
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute(query, (
                user_id,
                content_id,
                interaction_type,
                duration,
                timestamp
            ))
    
    conn.commit()
    interaction_count = SAMPLE_USERS * INTERACTIONS_PER_USER
    print(f"✓ Seeded {interaction_count} interactions")


def verify_data(conn):
    """Verify seeded data."""
    cursor = conn.cursor()
    
    queries = [
        ("Users", "SELECT COUNT(*) FROM users"),
        ("Content", "SELECT COUNT(*) FROM content"),
        ("Interactions", "SELECT COUNT(*) FROM interactions"),
    ]
    
    print("\n📊 Data Summary:")
    for name, query in queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"   {name}: {count}")


def main():
    """Main seeding function."""
    print("\n🌱 Context IQ - Sample Data Seeding")
    print("=" * 50)
    
    # Wait for database to be ready
    max_retries = 10
    for attempt in range(max_retries):
        try:
            conn = create_connection()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Retrying database connection ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect after {max_retries} attempts")
                raise
    
    try:
        seed_users(conn)
        seed_content(conn)
        seed_interactions(conn)
        verify_data(conn)
        
        print("\n" + "=" * 50)
        print("✓ Sample data seeding completed!")
        print("\n📝 Try this:")
        print("   1. Go to http://localhost:3000")
        print("   2. Enter a user ID: user_001, user_002, etc.")
        print("   3. Click 'Fetch Recommendations'")
        print("   4. Interact with recommendations (View, Like, Save, Share)")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
