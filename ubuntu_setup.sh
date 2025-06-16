#!/bin/bash
# Options Trading Bot 2026 - Ubuntu Setup Script
# This script sets up the bot with Python 3.11 in a virtual environment

set -e  # Exit on error

echo "=========================================="
echo "Options Trading Bot 2026 - Ubuntu Setup"
echo "=========================================="

# Check if we're in the bot directory
if [ ! -f "main_sync_with_web.py" ]; then
    echo "Error: Please run this script from the options_trading_bot_2026 directory"
    exit 1
fi

# Install Python 3.11 if needed
echo "1. Checking Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
else
    echo "Python 3.11 is already installed"
fi

# Create virtual environment
echo "2. Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3.11 -m venv venv
    echo "Virtual environment created"
fi

# Activate venv and install dependencies
echo "3. Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example if it doesn't exist
echo "4. Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
    echo "⚠️  Please edit .env with your actual values:"
    echo "   nano .env"
else
    echo ".env file already exists"
fi

# Create logs directory
echo "5. Creating logs directory..."
mkdir -p logs

# Test the setup
echo "6. Testing Python environment..."
python --version

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit your .env file: nano .env"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Test the bot: python test_market_data.py"
echo "4. Run the bot: python main_sync_with_web.py"
echo ""
echo "To run as a service, see: setup_service.sh"
