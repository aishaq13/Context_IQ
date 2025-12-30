"""API Endpoints Documentation

## Authentication
Currently not implemented. Future versions will support JWT tokens.

## Base URL
- Local: `http://localhost:8000/api/v1`
- Production: `https://api.contextiq.example.com/api/v1`

## Endpoints

### Health Check
```
GET /health
```
Returns system status for all services.

**Response:** 200 OK
```json
{
  "status": "healthy",
  "timestamp": "2025-12-29T10:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "kafka": "connected",
    "ml_model": "loaded"
  }
}
```

### Get Recommendations
```
GET /recommendations?user_id=user_001&limit=10
```
Retrieve personalized content recommendations for a user.

**Query Parameters:**
- `user_id` (string, required): User identifier
- `limit` (integer, optional): Number of recommendations (default: 10)

**Response:** 200 OK
```json
{
  "user_id": "user_001",
  "recommendations": [
    {
      "content_id": "content_0001",
      "title": "The Art of Machine Learning",
      "category": "Technology",
      "ml_score": 0.95,
      "combined_score": 0.92
    }
  ]
}
```

### Log Interaction
```
POST /interact
```
Record a user interaction (view, like, save, share).

**Request Body:**
```json
{
  "user_id": "user_001",
  "content_id": "content_0001",
  "interaction_type": "like"
}
```

**Response:** 201 Created
```json
{
  "status": "success",
  "interaction_id": "uuid"
}
```

### Get User Profile
```
GET /user/{user_id}
```
Retrieve user profile and interaction statistics.

**Response:** 200 OK
```json
{
  "user_id": "user_001",
  "total_interactions": 42,
  "interaction_types": {
    "view": 25,
    "like": 12,
    "save": 3,
    "share": 2
  }
}
```

### List Content
```
GET /content?category=Technology&limit=20
```
List all available content items.

**Query Parameters:**
- `category` (string, optional): Filter by category
- `limit` (integer, optional): Number of items (default: 50)

**Response:** 200 OK
```json
{
  "total": 50,
  "items": [
    {
      "content_id": "content_0001",
      "title": "The Art of Machine Learning",
      "category": "Technology",
      "created_at": "2025-12-29T10:00:00Z"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid user_id format"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database connection failed"
}
```
"""
