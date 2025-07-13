#!/bin/bash

# CivicAI Policy Debate System - Startup Script
# This script starts both the backend API and frontend UI

echo "🚀 Starting CivicAI Policy Debate System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📦 uv not found. Installing uv...${NC}"
    # Install uv if not available
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check again after installation
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ Failed to install uv. Please install manually: https://github.com/astral-sh/uv${NC}"
        exit 1
    fi
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is required but not installed${NC}"
    exit 1
fi

# Create virtual environment with uv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment with uv...${NC}"
    uv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install Python dependencies with uv from pyproject.toml
echo -e "${BLUE}📦 Installing Python dependencies with uv...${NC}"
uv pip install -e .

# Install Node.js dependencies
echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
cd policy-pulse-debate
npm install
cd ..

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the backend API
echo -e "${GREEN}🔧 Starting FastAPI backend...${NC}"
cd api
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to start
sleep 3

# Start the frontend
echo -e "${GREEN}🎨 Starting React frontend...${NC}"
cd policy-pulse-debate
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for services to start
sleep 5

echo -e "${GREEN}✅ System is running!${NC}"
echo -e "${BLUE}📊 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}🎨 Frontend UI: http://localhost:5173${NC}"
echo -e "${BLUE}📖 API Docs: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop all services${NC}"

# Wait for user to stop
wait 