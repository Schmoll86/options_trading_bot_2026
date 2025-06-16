#!/bin/bash
# Options Trading Bot 2026 - Production Startup Script

echo "============================================================"
echo "🚀 OPTIONS TRADING BOT 2026 - PRODUCTION MODE"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ ERROR: Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

# Check if another instance is running
if pgrep -f "python main_sync_with_web.py" > /dev/null; then
    echo "❌ ERROR: Bot is already running!"
    echo "To stop it, run: pkill -f 'python main_sync_with_web.py'"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate timestamp for log file
timestamp=$(date +%Y%m%d_%H%M%S)
log_file="logs/bot_production_${timestamp}.log"

echo "📊 Configuration:"
echo "  - Analysis Interval: 60 seconds"
echo "  - Strategy Selection: Based on market conditions"
echo "    • SPY > +0.5% → Bull Strategy"
echo "    • SPY < -0.5% → Bear Strategy"
echo "    • VIX > 20 → Volatility Strategy"
echo "    • Otherwise → No trades"
echo ""
echo "📝 Log file: ${log_file}"
echo "🌐 Web Monitor: http://localhost:5001"
echo ""
echo "Starting bot..."
echo ""

# Start the bot with output to both console and log file
python main_sync_with_web.py 2>&1 | tee "${log_file}" 