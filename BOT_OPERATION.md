# Options Trading Bot 2026 - Operation Guide

## 🚀 Quick Start

### Starting the Bot
```bash
./run_bot.sh
```

### Stopping the Bot
```bash
./stop_bot.sh
```

### Monitoring the Bot
- **Web Interface**: http://localhost:5001
- **View Logs**: `tail -f bot_production_*.log`
- **Check Status**: `ps aux | grep main_sync_with_web`

## 🔧 Key Features

### Single Instance Protection
The bot now includes single-instance protection to prevent multiple instances from running simultaneously:
- Uses PID file at `/tmp/options_trading_bot_2026.pid`
- Automatically checks if another instance is running
- Prevents accidental duplicate instances

### Recent Fixes Applied
1. **AsyncSyncAdapter** - Bridges async strategies with sync execution engine
2. **BarDataList Handling** - Fixed historical data processing for ib_insync format
3. **Market Data Retrieval** - Improved reliability with proper contract qualification
4. **Error Handling** - Better handling of VIX data unavailability

## 📊 Current Status

When running, the bot:
- ✅ Connects to IBKR Gateway (port 4001)
- ✅ Monitors account value ($3,756.96)
- ✅ Detects market sentiment (BULLISH/BEARISH/VOLATILE)
- ✅ Screens stocks every 5 minutes
- ✅ Executes strategies based on market conditions

## 🛠️ Troubleshooting

### Bot Won't Start
1. Check if already running: `./run_bot.sh`
2. Clear stale PID: `rm /tmp/options_trading_bot_2026.pid`
3. Check IBKR Gateway is running on port 4001

### No Trades Executing
- Strategies have strict criteria for risk management
- Bull strategy requires:
  - RSI between 40-60
  - Price above 20 & 50 day moving averages
  - Sufficient options liquidity
  - Risk/reward ratio >= 2.0

### Market Data Issues
- Ensure IBKR Gateway has market data subscriptions
- Bot uses delayed data mode for reliability
- VIX data may show as -1.00 (handled gracefully)

## 📁 Key Files

- `main_sync_with_web.py` - Main entry point
- `execution_engine_2026/sync_engine.py` - Trading orchestration
- `async_sync_adapter.py` - Async/sync bridge
- `bull_module_2026/bull.py` - Bull strategy implementation
- `web_monitor_2026/` - Web interface
- `.env` - Configuration (IBKR settings)

## 🔐 Safety Features

1. **Risk Management**
   - Max position size limits
   - Portfolio percentage constraints
   - Stop loss implementation

2. **Trading Hours**
   - Only trades during market hours (9:30 AM - 4:00 PM ET)
   - Automatic detection of market status

3. **Error Recovery**
   - Continues running on non-critical errors
   - Logs all issues for debugging
   - Graceful shutdown handling

## 📈 Performance Monitoring

Check the web monitor at http://localhost:5001 for:
- Current positions
- Daily P&L
- Market sentiment
- Recent screening results
- System status

## 🚨 Emergency Stop

To immediately stop the bot:
```bash
kill -9 $(cat /tmp/options_trading_bot_2026.pid)
rm /tmp/options_trading_bot_2026.pid
``` 