# Context IQ - Quick Reference

## 🚀 Start Here

```bash
# 1. Navigate to project
cd context-iq

# 2. Start all services (30 seconds)
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
```

---

## 📌 Key Directories

```
backend/        → FastAPI REST API + ML consumer
frontend/       → React UI
ml/             → PyTorch model training
infra/          → Docker Compose & Kubernetes
```

---

## 🔌 API Quick Reference

### Health Check
```bash
GET http://localhost:8000/api/v1/health
```

### Log Interaction
```bash
curl -X POST http://localhost:8000/api/v1/interact \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "content_id": "content_0001",
    "interaction_type": "view",
    "duration_seconds": 120,
    "metadata": {}
  }'
```

**Interaction Types:** `view`, `like`, `save`, `share`

### Get Recommendations
```bash
GET http://localhost:8000/api/v1/recommendations?user_id=user_001&limit=10
```

### User Profile
```bash
GET http://localhost:8000/api/v1/user-profile/user_001
```

### List Content
```bash
GET http://localhost:8000/api/v1/content?category=technology&limit=50
```

---

## 🐳 Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f                    # All services
docker-compose logs -f backend            # Specific service
docker-compose logs -f ml-consumer

# Check status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec postgres psql -U contextiq_user -d contextiq

# Stop services
docker-compose down

# Reset data
docker-compose down -v

# Rebuild images
docker-compose build
```

---

## 🔧 Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **frontend** | 3000 | React UI |
| **backend** | 8000 | FastAPI REST API |
| **postgres** | 5432 | Database |
| **redis** | 6379 | Cache |
| **kafka** | 9092 | Event streaming |
| **zookeeper** | 2181 | Kafka coordination |
| **ml-consumer** | - | ML model training |

---

## 📊 Data Seeding

```bash
# Seed sample data (creates 20 users, 50 content items, 300 interactions)
docker-compose exec backend python seed_data.py

# Connect to database
docker-compose exec postgres psql -U contextiq_user -d contextiq

# View tables
\dt                          # List tables
SELECT COUNT(*) FROM users;  # Count users
SELECT COUNT(*) FROM content; # Count content
SELECT COUNT(*) FROM interactions; # Count interactions
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# API health
curl http://localhost:8000/api/v1/health

# Database connection
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('dbname=contextiq user=contextiq_user password=contextiq_pass host=postgres')
print('Database connected!')
conn.close()
"
```

---

## 🐛 Troubleshooting

### Services not starting
```bash
docker-compose logs -f backend
docker-compose ps  # Check health status
```

### Database errors
```bash
# Recreate database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec postgres psql -U contextiq_user -d contextiq < backend/app/db/schema.sql
```

### Kafka not processing events
```bash
# Check Kafka is running
docker-compose exec kafka kafka-topics --list --bootstrap-server kafka:9092

# Create topic if missing
docker-compose exec kafka kafka-topics --create \
  --topic user_events \
  --bootstrap-server kafka:9092 \
  --partitions 3 \
  --replication-factor 1
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python seed_data.py
```

---

## 📁 Configuration

### Environment Variables (.env)
```env
DATABASE_URL=postgresql://contextiq_user:contextiq_pass@postgres:5432/contextiq
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
EMBEDDING_DIM=128
CACHE_TTL=300
ML_SCORE_WEIGHT=0.6
LLM_SCORE_WEIGHT=0.4
```

### For AWS Bedrock (optional)
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
BEDROCK_MODEL_ID=claude-3-sonnet-20240229
```

---

## 📖 Documentation

- **README.md** - Main documentation (architecture, API, setup)
- **DEPLOYMENT.md** - Production deployment guide
- **PROJECT_SUMMARY.md** - What was built and why
- **QUICK_REFERENCE.md** - This file

---

## 🎯 Workflow

### 1. User Logs In
```bash
POST /api/v1/interact
```
→ Interaction stored in PostgreSQL
→ Event published to Kafka
→ User cache invalidated in Redis

### 2. ML Training
```
Kafka Consumer reads events
→ Accumulates 50 events
→ Trains PyTorch model (5 epochs)
→ Computes recommendations
→ Stores in database
```

### 3. Get Recommendations
```bash
GET /api/v1/recommendations?user_id=X
```
→ Check Redis cache (5 min TTL)
→ If miss: Query database, enrich, cache
→ Return recommendations with scores

---

## 🚀 Deployment

### Local (Docker Compose)
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f infra/k8s/backend-deployment.yaml
kubectl apply -f infra/k8s/kafka.yaml
```

### AWS ECS
See DEPLOYMENT.md for detailed instructions

---

## 📊 Key Metrics

| Metric | Target | How to Measure |
|--------|--------|---|
| Recommendation Accuracy | 75% | Hit rate (relevant / top-k) |
| API Latency | <500ms | curl timing |
| Cache Hit Rate | >80% | Redis stats |
| Model Training | <10s | Check logs |
| Interaction Logging | <100ms | API response time |

---

## 🎓 Tech Stack Summary

```
Frontend:  React.js + CSS3
Backend:   FastAPI (Python)
ML:        PyTorch (embeddings)
Database:  PostgreSQL (persistence)
Cache:     Redis (recommendations)
Streaming: Kafka (events)
LLM:       AWS Bedrock (Claude)
Infra:     Docker, Kubernetes
```

---

## 💡 Common Tasks

### Add a new API endpoint
1. Edit `backend/app/api/routes.py`
2. Add FastAPI route
3. Restart: `docker-compose restart backend`

### Change ML model parameters
1. Edit `backend/app/utils/config.py`
2. Update environment variables in `docker-compose.yml`
3. Restart ML consumer: `docker-compose restart ml-consumer`

### Update database schema
1. Edit `backend/app/db/schema.sql`
2. Apply: `docker-compose exec postgres psql -U contextiq_user -d contextiq < schema.sql`

### Deploy to production
1. See DEPLOYMENT.md
2. Build images: `docker build -t myrepo/contextiq-backend:v1 backend/`
3. Push to registry
4. Deploy with K8s or ECS

---

## ✨ Project Highlights

✅ **Production-Ready** - Error handling, logging, health checks
✅ **Scalable** - Async processing, event streaming, caching
✅ **Well-Documented** - Comprehensive guides and inline comments
✅ **Modern Stack** - FastAPI, PyTorch, React, Kubernetes
✅ **Easy to Extend** - Modular architecture, clean code
✅ **Interview Ready** - Best practices, attention to detail

---

## 🔗 URLs When Running

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc UI |
| http://localhost:5432 | PostgreSQL |
| http://localhost:6379 | Redis |
| http://localhost:9092 | Kafka |

---

## 📞 Quick Help

**Check if services are healthy**
```bash
docker-compose ps
curl http://localhost:8000/api/v1/health
```

**View all logs**
```bash
docker-compose logs -f
```

**Enter database**
```bash
docker-compose exec postgres psql -U contextiq_user -d contextiq
```

**Rebuild everything**
```bash
docker-compose down -v
docker-compose build
docker-compose up -d
```

---

**Quick Reference Complete** 📋

For detailed information, see README.md, DEPLOYMENT.md, or PROJECT_SUMMARY.md
