#!/bin/bash

# Personal Astrology Calendar FastAPI Microservice Startup Script

echo "Starting Personal Astrology Calendar FastAPI Microservice..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the FastAPI server
echo "Starting FastAPI server on port 8004..."
python app.py
