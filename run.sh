#!/bin/bash

# Vox Launcher Script
# This script initializes the database and starts the Vox application

echo "🎤 Starting Vox - Voice Therapy Coach"
echo "===================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 Please edit .env and add your OPENAI_API_KEY before continuing."
    echo "Press Enter to continue or Ctrl+C to exit..."
    read
fi

# Initialize database if it doesn't exist
if [ ! -f vox_data.db ]; then
    echo "📊 Initializing database..."
    python init_db.py
    echo "✅ Database initialized"
else
    echo "✅ Database already exists"
fi

echo ""
echo "🚀 Starting Vox server..."
echo "📍 Access the application at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000
