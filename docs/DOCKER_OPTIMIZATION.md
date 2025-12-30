"""Docker optimization layer

This Dockerfile uses multi-stage builds to minimize image size.
"""

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH
COPY app/ ./app/
COPY seed_data.py ./
COPY compute_recommendations.py ./

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
