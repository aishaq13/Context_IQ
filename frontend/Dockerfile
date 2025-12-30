# Frontend Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY frontend/public/ ./public/
COPY frontend/src/ ./src/

# Build React app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the app
RUN npm install -g serve

# Copy built app from builder
COPY --from=builder /app/build ./build

# Expose frontend port
EXPOSE 3000

# Run the app
CMD ["serve", "-s", "build", "-l", "3000"]
