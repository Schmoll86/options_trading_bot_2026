#!/bin/bash

# Options Trading Bot 2026 - Production Runner
# This script starts the bot in production mode with proper error handling

echo "============================================================"
echo "🚀 OPTIONS TRADING BOT 2026 - PRODUCTION MODE"
echo "============================================================"
echo "Starting at $(date)"
echo "============================================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if IBKR Gateway is running
if ! nc -z localhost 4001; then
    echo "❌ IBKR Gateway not detected on port 4001"
    echo "   Please start TWS or IBKR Gateway first"
    echo "   Configure it for API connections on port 4001"
    exit 1
fi

# Check Python dependencies
echo "📦 Checking dependencies..."
python3 -c "import ib_insync, pandas, numpy, flask, scipy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

echo "✅ Dependencies verified"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the bot with production configuration
echo "🚀 Starting Options Trading Bot..."
echo "📊 Web Monitor will be available at: http://localhost:5001"
echo "📝 Logs will be written to: options_bot_2026_live.log"
echo ""
echo "Press Ctrl+C to stop the bot"
echo "============================================================"

# Run the bot
python3 main_sync_with_web.py

echo "============================================================"
echo "Bot stopped at $(date)"
echo "============================================================" 