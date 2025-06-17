# 🚀 Options Trading Bot 2026 - Production Setup

## ✅ What's Fixed
- ✅ **ThreadSafeIBKRWrapper interface errors** - All methods properly implemented
- ✅ **Position sizing calculations** - Portfolio provider integration working
- ✅ **Strategy execution** - Bull, Bear, and Volatile strategies all functional
- ✅ **Risk management** - Portfolio monitoring and position sizing working
- ✅ **Web monitoring** - Dashboard available at http://localhost:5001
- ✅ **IBKR connectivity** - Market data and order placement working

## 🛠️ Step-by-Step Production Setup

### 1. **Prerequisites**
```bash
# Ensure you have Python 3.8+
python3 --version

# Install system dependencies
sudo apt update
sudo apt install python3-venv python3-pip netcat-openbsd
```

### 2. **IBKR Gateway Setup**
1. **Download & Install** IBKR Gateway or TWS
2. **Configure API Settings:**
   - Enable API connections
   - Set port to **4001** 
   - Allow localhost connections
   - Set Master API client ID (optional)
3. **Start Gateway** and login with your credentials

### 3. **Bot Installation**
```bash
# Navigate to bot directory
cd ~/options_trading_bot_2026-1

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. **Configuration** (Optional)
- Bot uses automatic configuration
- No `.env` file required - it works with defaults
- Portfolio value is automatically detected from IBKR account

### 5. **Start the Bot**
```bash
# Option 1: Use the production script (RECOMMENDED)
./run_production_bot.sh

# Option 2: Manual start
source .venv/bin/activate
python3 main_sync_with_web.py
```

### 6. **Monitor the Bot**
- **Web Dashboard:** http://localhost:5001
- **Log File:** `options_bot_2026_live.log`
- **Terminal Output:** Real-time status updates

## 📊 What the Bot Does

### **Market Analysis**
- Analyzes SPY for market sentiment (Bullish/Bearish/Volatile)
- Monitors VIX for volatility conditions
- Screens stocks for trading opportunities

### **Strategy Execution**
- **Bull Strategy:** Bull call spreads when market is bullish
- **Bear Strategy:** Bear put spreads when market is bearish  
- **Volatile Strategy:** Straddles/strangles when volatility is high

### **Risk Management**
- Automatic position sizing based on account value
- Kelly Criterion optimization
- Stop losses and profit targets
- Portfolio monitoring

## 🎯 Trading Hours
- **Active:** Monday-Friday 9:30 AM - 4:00 PM ET
- **Inactive:** Outside market hours (analysis only)

## 🛑 Stopping the Bot
```bash
# In terminal: Press Ctrl+C
# Or kill the process
pkill -f "python3 main_sync_with_web.py"
```

## 📝 Important Notes

### **Paper Trading**
- Start with IBKR paper trading account
- Test thoroughly before live trading
- Monitor for several days to verify functionality

### **Live Trading**
- Only use with funded IBKR account
- Start with small position sizes
- Monitor closely during first weeks
- Keep sufficient cash for margin requirements

### **Troubleshooting**
```bash
# Check IBKR connection
nc -z localhost 4001

# View recent logs
tail -f options_bot_2026_live.log

# Restart if issues
pkill -f python3
./run_production_bot.sh
```

## 🚨 Risk Warning
**This bot trades real money. Options trading involves significant risk of loss. Only trade with money you can afford to lose. Monitor the bot closely and understand its strategies before using with live funds.** 