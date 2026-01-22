# FinanceAI Dockerfile
# Multi-stage build for optimized production image

# ===================
# Stage 1: Frontend Builder
# ===================
FROM node:22-slim AS frontend-builder

WORKDIR /app/web

# Copy frontend files
COPY web/package*.json ./
RUN npm ci

COPY web/ ./
RUN npm run build

# ===================
# Stage 2: Python Base
# ===================
FROM python:3.11-slim AS python-base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===================
# Stage 3: Production
# ===================
FROM python-base AS production

WORKDIR /app

# Copy backend code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy built frontend
COPY --from=frontend-builder /app/web/.next/standalone ./web/
COPY --from=frontend-builder /app/web/.next/static ./web/.next/static
COPY --from=frontend-builder /app/web/public ./web/public

# Create data directories
RUN mkdir -p data/user data/cache

# Environment variables
ENV PYTHONPATH=/app
ENV BACKEND_PORT=8001
ENV FRONTEND_PORT=3000

# Expose ports
EXPOSE 8001 3000

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
