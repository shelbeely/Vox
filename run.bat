@echo off
REM Vox Launcher Script for Windows
REM This script initializes the database and starts the Vox application

echo.
echo 🎤 Starting Vox - Voice Therapy Coach
echo ====================================
echo.

REM Check if .env file exists
if not exist .env (
    echo ⚠️  Warning: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo ✅ Created .env file
    echo.
    echo 📝 Please edit .env and add your OPENAI_API_KEY before continuing.
    echo Press Enter to continue or Ctrl+C to exit...
    pause > nul
)

REM Initialize database if it doesn't exist
if not exist vox_data.db (
    echo 📊 Initializing database...
    python init_db.py
    echo ✅ Database initialized
) else (
    echo ✅ Database already exists
)

echo.
echo 🚀 Starting Vox server...
echo 📍 Access the application at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000
