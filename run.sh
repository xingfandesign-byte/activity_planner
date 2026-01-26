#!/bin/bash

# Weekend Planner Startup Script

echo "🎉 Starting Weekend Planner..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Start backend
echo "📦 Starting backend server..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Start backend in background
python app.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   API available at http://localhost:5001"

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🌐 Starting frontend server..."
cd ../frontend

# Start simple HTTP server
python3 -m http.server 8000 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   App available at http://localhost:8000"
echo ""
echo "✨ Weekend Planner is running!"
echo "   Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
