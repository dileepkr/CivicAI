#!/bin/bash

# CivicAI Policy Debate System - Fixed Startup Script
# This script starts the system with proper Weave configuration to avoid circular reference errors

echo "🚀 Starting CivicAI Policy Debate System with Weave fixes..."

# Set environment variables to prevent Weave issues
export WEAVE_DISABLE_TRACING="1"
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "requirements.txt" ]; then
    echo "⚠️  requirements.txt not found. Please ensure dependencies are installed."
else
    echo "📦 Checking dependencies..."
    pip install -r requirements.txt --quiet
fi

# Check for required environment variables
if [ -z "$WNB_API_KEY" ]; then
    echo "⚠️  WNB_API_KEY not set. Some features may not work."
    echo "   Set it with: export WNB_API_KEY='your_api_key'"
fi

if [ -z "$WANDB_PROJECT" ]; then
    export WANDB_PROJECT="civicai-policy-debate"
    echo "📊 Using default WANDB_PROJECT: $WANDB_PROJECT"
fi

# Run the test script to verify fixes
echo "🧪 Running system tests..."
python test_weave_fix.py

if [ $? -eq 0 ]; then
    echo "✅ System tests passed. Starting API server..."
    
    # Start the API server
    echo "🌐 Starting FastAPI server on http://0.0.0.0:8000"
    echo "📊 API documentation available at http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the API with proper configuration
    python api/main.py
else
    echo "❌ System tests failed. Please check the configuration."
    exit 1
fi 