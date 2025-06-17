#!/bin/bash

# Options Trading Bot 2026 - Production Startup
# This script ensures a clean production environment

echo "============================================================"
echo "🚀 OPTIONS TRADING BOT 2026 - PRODUCTION STARTUP"
echo "============================================================"
echo "Starting at $(date)"
echo "============================================================"

# Function to check requirements
check_requirements() {
    echo "🔍 Checking requirements..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1)
    echo "✓ Python: $python_version"
    
    # Check virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo "❌ Virtual environment not activated"
        echo "Please run: source .venv/bin/activate"
        exit 1
    fi
    echo "✓ Virtual environment: $VIRTUAL_ENV"
    
    # Check IBKR Gateway
    if ! nc -z localhost 4001; then
        echo "❌ IBKR Gateway not accessible on port 4001"
        echo "Please ensure IBKR Gateway is running with API enabled"
        exit 1
    fi
    echo "✓ IBKR Gateway accessible on port 4001"
}

# Function to clean cache
clean_cache() {
    echo "🧹 Cleaning cache files..."
    
    # Remove Python cache
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clear any existing bot processes
    pkill -f "python.*main_sync" 2>/dev/null || true
    
    echo "✓ Cache cleaned"
}

# Function to test IBKR connection
test_connection() {
    echo "🔗 Testing IBKR connection..."
    
    timeout 30 python3 test_ibkr_connection.py
    if [ $? -eq 0 ]; then
        echo "✓ IBKR connection test passed"
    else
        echo "❌ IBKR connection test failed"
        echo "Please check your IBKR Gateway settings:"
        echo "  1. Enable API in Gateway: Configure → Settings → API → Settings"
        echo "  2. Check 'Enable ActiveX and Socket Clients'"
        echo "  3. Set Socket port to 4001"
        echo "  4. Allow connections from localhost"
        echo "  5. Restart Gateway after changes"
        exit 1
    fi
}

# Main execution
main() {
    check_requirements
    clean_cache
    test_connection
    
    echo "============================================================"
    echo "🎯 STARTING PRODUCTION BOT"
    echo "============================================================"
    
    # Start the bot
    python3 main_sync_with_web.py
}

# Run the script
main "$@" 