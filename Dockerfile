# Dockerfile optimizado para Railway - API Calendario Personal
FROM python:3.11-slim

ARG COMMIT_SHA
ENV COMMIT_SHA=$COMMIT_SHA

WORKDIR /app

# Install system dependencies and build tools for compiling Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port for Fly.io
EXPOSE 8003

# Run the application with Fly.io settings
CMD uvicorn app:app \
    --host 0.0.0.0 \
    --port 8003 \
    --timeout-keep-alive 90 \
    --access-log \
    --log-level info
