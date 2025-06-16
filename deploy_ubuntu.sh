#!/bin/bash
# Options Trading Bot 2026 - Ubuntu Deployment Script
# Run this script on your Ubuntu server to set up the bot

set -e  # Exit on error

echo "=============================================="
echo "Options Trading Bot 2026 - Ubuntu Deployment"
echo "=============================================="

# Update system
echo "1. Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python 3.11 if not present
echo "2. Installing Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

# Install git if not present
echo "3. Installing git..."
sudo apt install -y git

# Clone repository
echo "4. Cloning repository..."
cd ~
if [ -d "options_trading_bot_2026" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd options_trading_bot_2026
    git pull
else
    git clone https://github.com/schmoll86/options_trading_bot_2026.git
    cd options_trading_bot_2026
fi

# Create virtual environment
echo "5. Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "6. Installing Python dependencies..."
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt

# Create logs directory
echo "7. Creating logs directory..."
mkdir -p logs

# Copy environment file
echo "8. Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file with your actual configuration!"
    echo "   Run: nano .env"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Install systemd service
echo "9. Installing systemd service..."
sudo cp trading-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file:      nano ~/options_trading_bot_2026/.env"
echo "2. Test the bot:        cd ~/options_trading_bot_2026 && source venv/bin/activate && python test_market_data.py"
echo "3. Start the service:   sudo systemctl start trading-bot"
echo "4. Enable auto-start:   sudo systemctl enable trading-bot"
echo "5. Check logs:          sudo journalctl -u trading-bot -f"
echo ""
echo "To switch to strict volatility version:"
echo "   cd ~/options_trading_bot_2026 && git checkout original-strict-volatility"
echo "" 