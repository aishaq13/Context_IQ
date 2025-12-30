# Context IQ - Deployment Guide

This guide covers deploying Context IQ to different environments.

## Table of Contents

1. [Local Development (Docker Compose)](#local-development-docker-compose)
2. [Docker Hub Registry](#docker-hub-registry)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [AWS ECS](#aws-ecs)
5. [Production Considerations](#production-considerations)

---

## Local Development (Docker Compose)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM available
- ~5GB disk space

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd context-iq

# Run startup script
./start.sh  # Linux/Mac
# or
start.bat   # Windows

# Services will start and be healthy in ~60 seconds
```

### Manual Setup

```bash
# Create environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Seed sample data
docker-compose exec backend python seed_data.py

# Verify services
docker-compose ps
docker-compose logs -f backend
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs

### Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## Docker Hub Registry

### Build and Push Images

```bash
# Login to Docker Hub
docker login

# Build backend image
docker build -t your-username/contextiq-backend:latest backend/
docker push your-username/contextiq-backend:latest

# Build ML image
docker build -t your-username/contextiq-ml:latest -f ml/Dockerfile .
docker push your-username/contextiq-ml:latest

# Build frontend image
docker build -t your-username/contextiq-frontend:latest frontend/
docker push your-username/contextiq-frontend:latest

# Tag with version
docker tag your-username/contextiq-backend:latest your-username/contextiq-backend:v1.0.0
docker push your-username/contextiq-backend:v1.0.0
```

### Use from Registry

Update `docker-compose.yml`:

```yaml
backend:
  image: your-username/contextiq-backend:latest
ml-consumer:
  image: your-username/contextiq-ml:latest
frontend:
  image: your-username/contextiq-frontend:latest
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- `kubectl` configured
- 4+ CPU cores, 8GB+ RAM

### Namespace Setup

```bash
# Create namespace
kubectl create namespace contextiq

# Create secrets
kubectl create secret generic contextiq-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/contextiq \
  --from-literal=aws-access-key-id=your-key \
  --from-literal=aws-secret-access-key=your-secret \
  -n contextiq

# Verify
kubectl get secrets -n contextiq
```

### Deploy Services

```bash
# Create ConfigMaps for configuration
kubectl create configmap contextiq-config \
  --from-literal=embedding-dim=128 \
  --from-literal=cache-ttl=300 \
  -n contextiq

# Deploy backend
kubectl apply -f infra/k8s/backend-deployment.yaml -n contextiq

# Deploy Kafka
kubectl apply -f infra/k8s/kafka.yaml -n contextiq

# Verify deployments
kubectl get pods -n contextiq
kubectl get svc -n contextiq
```

### Check Deployment Status

```bash
# Watch pods starting
kubectl get pods -n contextiq -w

# View logs
kubectl logs -n contextiq deployment/contextiq-backend
kubectl logs -n contextiq pod/kafka-0

# Port forward for local testing
kubectl port-forward -n contextiq svc/backend 8000:8000
kubectl port-forward -n contextiq svc/frontend 3000:3000
```

### Update Deployment

```bash
# Update image
kubectl set image deployment/contextiq-backend \
  backend=your-username/contextiq-backend:v1.1.0 \
  -n contextiq

# Rollback if needed
kubectl rollout history deployment/contextiq-backend -n contextiq
kubectl rollout undo deployment/contextiq-backend -n contextiq
```

### Cleanup

```bash
# Delete deployment
kubectl delete namespace contextiq

# Or individual resources
kubectl delete -f infra/k8s/ -n contextiq
```

---

## AWS ECS

### Prerequisites

- AWS account with ECS permissions
- ECR repositories created
- RDS PostgreSQL instance
- ElastiCache Redis
- MSK Kafka cluster

### Create Task Definitions

```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json \
  --region us-east-1
```

Example `ecs-task-definition.json`:

```json
{
  "family": "contextiq-backend",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/contextiq-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@postgres.c1234.us-east-1.rds.amazonaws.com:5432/contextiq"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://contextiq.12345.ng.0001.use1.cache.amazonaws.com:6379"
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
}
```

### Create ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster contextiq-cluster \
  --service-name contextiq-backend \
  --task-definition contextiq-backend:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000
```

### Update Service

```bash
# Update task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Update service with new task definition
aws ecs update-service \
  --cluster contextiq-cluster \
  --service contextiq-backend \
  --task-definition contextiq-backend:2 \
  --force-new-deployment
```

---

## Production Considerations

### Security

- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Set up WAF (Web Application Firewall)
- [ ] Use IAM roles instead of hardcoded credentials
- [ ] Enable encryption at rest (RDS, ElastiCache)
- [ ] Implement rate limiting on API endpoints
- [ ] Use API Gateway for authentication/authorization
- [ ] Rotate credentials regularly
- [ ] Set up VPC with private subnets for databases

### High Availability

- [ ] Run 3+ replicas of backend service
- [ ] Use load balancer (ALB, ELB, or ingress)
- [ ] Configure auto-scaling based on CPU/memory
- [ ] Set up read replicas for PostgreSQL
- [ ] Use Redis cluster mode for high availability
- [ ] Configure Kafka with 3 brokers minimum
- [ ] Set up database backups (daily minimum)

### Monitoring & Logging

- [ ] Set up Prometheus for metrics
- [ ] Configure Grafana dashboards
- [ ] Enable CloudWatch/DataDog logs
- [ ] Set up alerts for critical metrics
- [ ] Track: latency, error rate, cache hit rate
- [ ] Monitor database connections and slow queries
- [ ] Set up log aggregation (ELK, Splunk, DataDog)

### Performance Optimization

- [ ] Enable Gzip compression
- [ ] Configure CDN for static assets
- [ ] Implement request batching for Bedrock calls
- [ ] Use database connection pooling
- [ ] Index frequently queried columns
- [ ] Cache Bedrock responses
- [ ] Use async workers for heavy computations

### Cost Optimization

- [ ] Use auto-scaling to match demand
- [ ] Use spot instances where appropriate
- [ ] Schedule non-critical batch jobs during off-peak
- [ ] Clean up old data regularly
- [ ] Monitor and optimize RDS instance type
- [ ] Review and consolidate redundant services

### Compliance

- [ ] Implement GDPR data retention policies
- [ ] Audit user data access
- [ ] Implement user deletion workflows
- [ ] Encrypt sensitive data (PII)
- [ ] Maintain audit logs
- [ ] Regular security assessments

---

## Environment Variables for Production

```env
# Database (managed RDS)
DATABASE_URL=postgresql://prod_user:secure_pass@contextiq-prod.c1234.us-east-1.rds.amazonaws.com:5432/contextiq

# Redis (managed ElastiCache)
REDIS_URL=redis://contextiq-prod.12345.ng.0001.use1.cache.amazonaws.com:6379

# Kafka (managed MSK)
KAFKA_BOOTSTRAP_SERVERS=b-1.contextiq-prod.1a2b3c.kafka.us-east-1.amazonaws.com:9092,b-2.contextiq-prod.1a2b3c.kafka.us-east-1.amazonaws.com:9092,b-3.contextiq-prod.1a2b3c.kafka.us-east-1.amazonaws.com:9092

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=${SECRETS_MANAGER_KEY}
AWS_SECRET_ACCESS_KEY=${SECRETS_MANAGER_SECRET}

# Application
DEBUG=false
CACHE_TTL=600
EMBEDDING_DIM=256
MODEL_UPDATE_INTERVAL=7200
```

---

## CI/CD Pipeline Example (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker images
        run: |
          docker build -t your-repo/contextiq-backend:${{ github.sha }} backend/
          docker push your-repo/contextiq-backend:${{ github.sha }}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/contextiq-backend \
            backend=your-repo/contextiq-backend:${{ github.sha }} \
            -n contextiq
          kubectl rollout status deployment/contextiq-backend -n contextiq
```

---

## Disaster Recovery

### Backup Strategy

```bash
# PostgreSQL backup
pg_dump -h localhost -U contextiq_user -d contextiq > backup.sql

# Restore
psql -h localhost -U contextiq_user -d contextiq < backup.sql

# Automated backups with RDS (AWS)
aws rds create-db-snapshot \
  --db-instance-identifier contextiq-prod \
  --db-snapshot-identifier contextiq-backup-$(date +%Y%m%d)
```

### Recovery Procedures

1. **Database Recovery:** Restore from most recent backup
2. **Cache Recovery:** Regenerate from source of truth (database)
3. **Service Recovery:** Redeploy containers, health checks will verify
4. **Data Recovery:** Use point-in-time restore for RDS

---

## Monitoring Dashboard

Set up Grafana with these key metrics:

- **API Latency:** p50, p95, p99 response times
- **Error Rate:** 4xx and 5xx errors per minute
- **Throughput:** Requests per second
- **Database:** Connection pool utilization, slow queries
- **Cache:** Hit rate, eviction rate
- **Kafka:** Consumer lag, message throughput
- **ML Model:** Training loss, inference latency
- **System:** CPU, memory, disk usage

---

## Rollback Procedure

```bash
# Kubernetes rollback
kubectl rollout undo deployment/contextiq-backend -n contextiq
kubectl rollout status deployment/contextiq-backend -n contextiq

# ECS rollback
aws ecs update-service \
  --cluster contextiq-cluster \
  --service contextiq-backend \
  --task-definition contextiq-backend:prev-version \
  --force-new-deployment
```

---

## Support & Troubleshooting

For deployment issues:

1. Check service logs: `kubectl logs -f <pod>`
2. Verify connectivity between services
3. Check environment variables are set correctly
4. Ensure all required AWS resources exist
5. Review CloudWatch/DataDog for errors

---

**Last Updated:** January 2024
