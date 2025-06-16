# Trading Bot Quick Reference

## Current Configuration
- **Client ID**: 7 (in .env)
- **Analysis Interval**: 10 minutes (600 seconds)
- **Market Data Timeout**: 60 seconds
- **Port**: 4001

## Running the Bot

### Basic Start
```bash
python main_sync_with_web.py
```

### With Output Logging
```bash
python main_sync_with_web.py 2>&1 | tee -a trading_bot.log
```

### Background Mode
```bash
python main_sync_with_web.py 2>&1 | tee -a trading_bot.log &
```

### After Gateway Restart
```bash
python restart_and_run.py
```

## Monitoring
- **Web UI**: http://localhost:5001
- **Check Status**: `curl -s http://localhost:5001/api/status | python -m json.tool`

## Stop the Bot
```bash
pkill -f "python main_sync_with_web.py"
```

## Check Logs
```bash
# Latest activity
tail -100 options_bot_2026_live.log

# Follow live
tail -f options_bot_2026_live.log

# Errors only
grep -E "(ERROR|Exception|Traceback)" options_bot_2026_live.log
```

## Known Issues
- Market data requests timing out - may need to check Gateway subscriptions
- Bot works but gets no live data - falls back to NEUTRAL sentiment

## Environment Variables
Edit `.env` or `fixed_env.txt` then copy:
```bash
cp fixed_env.txt .env
```

## 🚀 Quick Start Commands

### Safe Production Start
```bash
# Recommended way to start the bot
python start_bot_safe.py
```

### Direct Start Options
```bash
# Production mode with web monitor
python main_sync_with_web.py

# Headless mode (no web UI)
python main_sync.py

# Monitor only mode (no trading)
python monitor_only.py

# Test connection only
python test_connection.py
```

### Web Monitor Access
```
URL: http://localhost:5001
```

## 🔧 Common Commands

### Virtual Environment
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

### Dependency Management
```bash
# Install all dependencies
pip install -r requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt

# Check installed packages
pip list
```

### Process Management
```bash
# Check if bot is running
ps aux | grep "main_sync_with_web.py"

# Kill the bot process
pkill -f "main_sync_with_web.py"

# View logs
tail -f options_bot_2026.log
```

## 📋 Configuration Checklist

### Required .env Variables
```env
# IBKR Connection
IBKR_HOST=127.0.0.1
IBKR_PORT=4001
IBKR_CLIENT_ID=1

# Risk Management
MAX_PORTFOLIO_RISK=0.02
MAX_POSITION_SIZE=0.05
DAILY_LOSS_LIMIT=0.03

# Strategy Settings
BULL_RSI_MIN=40
BULL_RSI_MAX=70
BEAR_RSI_MIN=30
BEAR_RSI_MAX=60
MIN_IV_RANK=50

# API Keys (if using external news)
NEWS_API_KEY=your_key_here
```

## 🐛 Troubleshooting Guide

### Connection Issues

#### "Cannot connect to IBKR Gateway"
1. Check Gateway is running: `telnet 127.0.0.1 4001`
2. Verify API settings in Gateway
3. Check firewall/network settings
4. Try different client ID: `IBKR_CLIENT_ID=2`

#### "This event loop is already running"
- Use `main_sync_with_web.py` instead of `main.py`
- The sync version handles event loops properly

### Trading Issues

#### "No trades being executed"
1. Check market hours (9:30 AM - 4:00 PM ET)
2. Verify account has sufficient funds
3. Check risk parameters aren't too restrictive
4. Review logs for rejected orders

#### "Risk manager blocking trades"
- Check portfolio risk: currently at X% of limit
- Verify position sizes
- Review daily loss limit

### Web Monitor Issues

#### "Cannot access web monitor"
1. Check if running: `curl http://localhost:5001`
2. Verify no other process on port 5001
3. Check firewall allows local connections

## 📊 Key Metrics to Monitor

### Portfolio Health
- **Total P&L**: Current profit/loss
- **Win Rate**: Successful trades percentage
- **Risk Exposure**: Current % of portfolio at risk
- **Daily Loss**: Today's loss vs limit

### System Health
- **Connection Status**: IBKR Gateway connection
- **Active Strategies**: Which modules are running
- **Open Positions**: Current option spreads
- **Pending Orders**: Orders awaiting fill

## 🛡️ Safety Features

### Emergency Commands

#### Stop All Trading
```python
# In Python console:
from ibkr_client_2026.client import IBKRClient2026
client = IBKRClient2026()
client.cancel_all_orders()
```

#### Close All Positions
- Use the web monitor's "EMERGENCY STOP" button
- Or run: `python close_all_positions.py`

### Risk Limits (Default)
- Max portfolio risk: 2%
- Max position size: 5%
- Daily loss limit: 3%
- Min win probability: 65%
- Min risk/reward: 1:2

## 📈 Strategy Quick Reference

### Bull Module
- **Trigger**: RSI 40-70, price > MA20 & MA50
- **Strategy**: Bull call spreads
- **Expiry**: 30-45 days
- **Exit**: 50% profit or stop loss

### Bear Module  
- **Trigger**: RSI 30-60, price < MA20 & MA50
- **Strategy**: Bear put spreads
- **Expiry**: 30-45 days
- **Exit**: 50% profit or stop loss

### Volatile Module
- **Trigger**: IV Rank > 50%
- **Strategies**: 
  - Straddle (IV > 80%)
  - Strangle (IV > 70%)
  - Iron Condor (IV > 60%)

## 📝 Log Files

### Main Logs
- `options_bot_2026.log` - All system logs
- `logs/trades_YYYY-MM-DD.log` - Daily trade logs
- `logs/errors_YYYY-MM-DD.log` - Error logs only

### Log Levels
```python
# In code or .env:
LOG_LEVEL=INFO     # Normal operation
LOG_LEVEL=DEBUG    # Detailed debugging
LOG_LEVEL=ERROR    # Errors only
```

## 🔄 Daily Maintenance

### Before Market Open
1. Check IBKR Gateway connection
2. Review overnight news
3. Verify risk parameters
4. Clear old log files

### After Market Close
1. Review daily performance
2. Check for system errors
3. Backup trade logs
4. Plan next day's parameters

## 📞 Support Resources

### Documentation
- `README.md` - Project overview
- `ARCHITECTURE.md` - System design
- `DEPENDENCIES.md` - Package requirements
- `WORKFLOW.md` - Operational flow

### Common File Locations
```
options_trading_bot_2026/
├── .env                    # Configuration
├── options_bot_2026.log    # Main log file
├── main_sync_with_web.py   # Main entry point
├── start_bot_safe.py       # Safe launcher
└── web_monitor_2026/       # Web UI files
```

### Performance Benchmarks
- Startup time: < 10 seconds
- Order execution: < 1 second
- Web UI refresh: 1 second
- Strategy evaluation: < 5 seconds

## ⚡ Quick Fixes

### Reset Everything
```bash
# Stop all processes
pkill -f "options_trading_bot"

# Clear logs
rm -f *.log logs/*.log

# Restart
python start_bot_safe.py
```

### Update Configuration
```bash
# Edit configuration
nano .env

# No restart needed for most settings
# Restart required for connection settings
```

### Debug Mode
```bash
# Set in .env:
DEBUG=True
LOG_LEVEL=DEBUG

# Or run with:
DEBUG=True python main_sync_with_web.py
``` 