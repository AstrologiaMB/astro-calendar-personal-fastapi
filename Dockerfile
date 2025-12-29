# Dockerfile optimizado para Railway - API Calendario Personal
FROM python:3.11-slim

WORKDIR /app

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
