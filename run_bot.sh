#!/bin/bash

# Options Trading Bot 2026 - Single Instance Runner
# This script ensures only one instance of the bot runs at a time

PIDFILE="/tmp/options_trading_bot_2026.pid"
LOGFILE="bot_production_$(date +%Y%m%d_%H%M%S).log"

# Function to check if process is running
is_running() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is not running
            rm -f "$PIDFILE"
            return 1
        fi
    fi
    return 1
}

# Check if already running
if is_running; then
    echo "❌ Bot is already running with PID $(cat $PIDFILE)"
    echo "To stop it, run: kill $(cat $PIDFILE)"
    exit 1
fi

echo "============================================================"
echo "🚀 Starting Options Trading Bot 2026"
echo "============================================================"
echo "Log file: $LOGFILE"
echo "PID file: $PIDFILE"
echo ""

# Start the bot in background
nohup python main_sync_with_web.py > "$LOGFILE" 2>&1 &
BOT_PID=$!

# Save PID
echo $BOT_PID > "$PIDFILE"

# Wait a moment to check if it started successfully
sleep 3

if is_running; then
    echo "✅ Bot started successfully with PID $BOT_PID"
    echo ""
    echo "📊 Web Monitor: http://localhost:5001"
    echo "📄 View logs: tail -f $LOGFILE"
    echo "🛑 Stop bot: kill $BOT_PID"
    echo ""
    echo "============================================================"
else
    echo "❌ Bot failed to start. Check the log file: $LOGFILE"
    exit 1
fi 