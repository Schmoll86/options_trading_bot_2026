#!/bin/bash

# Options Trading Bot 2026 - Stop Script

PIDFILE="/tmp/options_trading_bot_2026.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 Stopping Options Trading Bot (PID: $PID)..."
        kill "$PID"
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Bot stopped successfully"
                rm -f "$PIDFILE"
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        echo "⚠️  Process didn't stop gracefully, forcing..."
        kill -9 "$PID" 2>/dev/null
        rm -f "$PIDFILE"
        echo "✅ Bot stopped (forced)"
    else
        echo "❌ Bot is not running (stale PID file)"
        rm -f "$PIDFILE"
    fi
else
    echo "❌ Bot is not running (no PID file found)"
fi 