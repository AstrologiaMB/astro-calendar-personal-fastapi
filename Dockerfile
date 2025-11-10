# Dockerfile optimizado para Railway - API Calendario Personal
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port (documentación, Railway ignora esto)
EXPOSE 8080

# CRITICAL: Uvicorn con configuración optimizada para Railway
CMD uvicorn app:app \
    --host 0.0.0.0 \
    --port $PORT \
    --timeout-keep-alive 90 \
    --access-log \
    --log-level info
