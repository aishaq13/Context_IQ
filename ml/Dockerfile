# ML Consumer Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and ML code
COPY backend/app/ ./app/
COPY ml/consumer.py ./consumer.py
COPY ml/train.py ./train.py

# Create models directory
RUN mkdir -p models

# Set Python path to include /app for imports
ENV PYTHONPATH=/app:$PYTHONPATH

# Run ML consumer
CMD ["python", "consumer.py"]
