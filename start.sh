#!/bin/bash

# Context IQ Quick Start Script
# This script initializes the project with sample data

set -e

echo "🚀 Context IQ - Quick Start"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created"
fi

echo ""
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
echo "   This may take 30-60 seconds..."

# Wait for backend health check
max_retries=60
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    
    retry_count=$((retry_count + 1))
    if [ $((retry_count % 10)) -eq 0 ]; then
        echo "   Still waiting... ($retry_count/$max_retries)"
    fi
    sleep 1
done

if [ $retry_count -eq $max_retries ]; then
    echo "⚠️ Backend took too long to start. Check logs with:"
    echo "   docker-compose logs -f backend"
fi

echo ""
echo "✓ All services are running!"
echo ""
echo "======================================"
echo "📚 Context IQ is ready!"
echo "======================================"
echo ""
echo "🌐 Access the application:"
echo "   • Frontend:    http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo ""
echo "🛠️  Useful commands:"
echo "   • View logs:   docker-compose logs -f <service>"
echo "   • Services:    docker-compose ps"
echo "   • Stop:        docker-compose down"
echo "   • Reset data:  docker-compose down -v && docker-compose up -d"
echo ""
echo "📖 Documentation: Read README.md for detailed setup and usage"
echo ""
