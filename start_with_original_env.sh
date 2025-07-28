#!/bin/bash

# Personal Astrology Calendar FastAPI Microservice
# Startup Script using Original Environment
# 
# This script uses the working environment from the original project
# to avoid dependency conflicts with newer versions of Immanuel.
#
# Based on the successful strategy used in astro_interpretador_rag_fastapi

echo "🚀 Starting Personal Astrology Calendar FastAPI Microservice..."
echo "📁 Using original environment from astro_calendar_personal_v3"

# Check if original project exists
if [ ! -d "/Users/apple/astro_calendar_personal_v3" ]; then
    echo "❌ Error: Original project not found at /Users/apple/astro_calendar_personal_v3"
    exit 1
fi

# Check if original venv exists
if [ ! -d "/Users/apple/astro_calendar_personal_v3/venv" ]; then
    echo "❌ Error: Original virtual environment not found"
    exit 1
fi

echo "✅ Original project found"
echo "🔧 Activating original environment..."

# Navigate to original project and activate its environment
cd /Users/apple/astro_calendar_personal_v3
source venv/bin/activate

# Verify Immanuel version
echo "📦 Checking Immanuel version..."
python -c "import immanuel; print(f'Immanuel version: {immanuel.__version__}')" 2>/dev/null || echo "⚠️  Immanuel version check failed"

# Navigate to microservice directory
echo "📂 Switching to microservice directory..."
cd /Users/apple/astro-calendar-personal-fastapi

# Check if FastAPI is installed
python -c "import fastapi" 2>/dev/null || {
    echo "📦 Installing FastAPI dependencies..."
    pip install fastapi uvicorn python-multipart
}

echo "🌟 Starting FastAPI server on port 8004..."
echo "📊 API Documentation: http://localhost:8004/docs"
echo "🔍 Health Check: http://localhost:8004/health"
echo "ℹ️  Service Info: http://localhost:8004/info"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the FastAPI server
python app.py
