#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}🚀 RELATRIX - Starting Local Environment${NC}"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Please run first-time setup:${NC}"
    echo "cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found. Please run first-time setup:${NC}"
    echo "cd frontend && npm install"
    exit 1
fi

# Function to kill processes on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping RELATRIX...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Start Backend
echo -e "${GREEN}📦 Starting Backend on http://localhost:8001${NC}"
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start Frontend
echo -e "${GREEN}🎨 Starting Frontend on http://localhost:3001${NC}"
cd frontend
npm run dev -- --port 3001 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

# Open browser
echo -e "${GREEN}🌐 Opening browser...${NC}"
open http://localhost:3001 2>/dev/null || xdg-open http://localhost:3001 2>/dev/null || echo "Please open http://localhost:3001 in your browser"

echo "========================================"
echo -e "${GREEN}✅ RELATRIX is running!${NC}"
echo -e "${BLUE}📍 Frontend:${NC} http://localhost:3001"
echo -e "${BLUE}📍 Backend:${NC} http://localhost:8001"
echo -e "${BLUE}📍 API Docs:${NC} http://localhost:8001/docs"
echo "========================================"
echo -e "${YELLOW}🛑 Press Ctrl+C to stop${NC}"
echo ""

# Keep script running
wait