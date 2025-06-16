#!/bin/bash
# Setup systemd service for Options Trading Bot 2026
# This script creates a service that runs the bot using the virtual environment

set -e

echo "Setting up Options Trading Bot as a systemd service..."

# Get the current directory (bot installation path)
BOT_DIR=$(pwd)
USER=$(whoami)

# Check if we're in the right directory
if [ ! -f "main_sync_with_web.py" ]; then
    echo "Error: Please run this script from the options_trading_bot_2026 directory"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run ubuntu_setup.sh first"
    exit 1
fi

# Create service file
SERVICE_FILE="/tmp/trading-bot.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Options Trading Bot 2026
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin:\$PATH"
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/main_sync_with_web.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot_error.log

# Resource limits
MemoryLimit=2G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd
sudo cp $SERVICE_FILE /etc/systemd/system/trading-bot.service
rm $SERVICE_FILE

# Create logs directory if it doesn't exist
mkdir -p logs

# Reload systemd
sudo systemctl daemon-reload

echo "✅ Service file created!"
echo ""
echo "Service Management Commands:"
echo "----------------------------"
echo "Start the bot:    sudo systemctl start trading-bot"
echo "Stop the bot:     sudo systemctl stop trading-bot"
echo "Restart the bot:  sudo systemctl restart trading-bot"
echo "Check status:     sudo systemctl status trading-bot"
echo "View logs:        tail -f logs/bot.log"
echo "Enable on boot:   sudo systemctl enable trading-bot"
echo ""
echo "⚠️  Before starting the service:"
echo "1. Make sure your .env file is configured"
echo "2. Test the bot manually first: source venv/bin/activate && python main_sync_with_web.py"
echo "3. Make sure IBKR Gateway/TWS is running" 