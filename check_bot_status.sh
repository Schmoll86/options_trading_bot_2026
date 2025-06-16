#!/bin/bash

echo "============================================"
echo "Options Trading Bot 2026 - Status Check"
echo "============================================"
echo ""

# Check if bot is running
BOT_PID=$(ps aux | grep "python main_sync_with_web.py" | grep -v grep | tail -1 | awk '{print $2}')

if [ -n "$BOT_PID" ]; then
    echo "✅ Bot is RUNNING (PID: $BOT_PID)"
    echo ""
    
    # Show process details
    echo "Process details:"
    ps aux | grep "python main_sync_with_web.py" | grep -v grep | tail -1
    echo ""
    
    # Show latest log entries
    echo "Latest activity:"
    tail -10 bot_production_continuous.log | grep -E "Trading cycle|Market sentiment|Portfolio value|ERROR|WARNING" | tail -5
    echo ""
    
    # Show market data
    echo "Recent market data:"
    tail -50 bot_production_continuous.log | grep "Got market data" | tail -5
    echo ""
    
    # Check web monitor
    if curl -s http://localhost:5001 > /dev/null; then
        echo "✅ Web monitor is accessible at http://localhost:5001"
    else
        echo "⚠️ Web monitor is not responding"
    fi
else
    echo "❌ Bot is NOT running"
    echo ""
    echo "To start the bot, run:"
    echo "nohup python main_sync_with_web.py > bot_production_continuous.log 2>&1 &"
fi

echo ""
echo "============================================" 