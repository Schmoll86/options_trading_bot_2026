# Options Trading Bot 2026 🚀

An automated options trading bot built with Python that connects to Interactive Brokers (IBKR) for live trading. The bot implements multiple strategies (Bull, Bear, Volatility) and includes risk management, real-time monitoring, and a web dashboard.

**✅ PRODUCTION READY STATUS:**
- Account Connected: $3,756.96
- VIX Data Collection: ✅ Working
- Web Monitor: ✅ Enhanced with dark theme
- Real-time Activity Log: ✅ Complete visibility
- All Critical Issues: ✅ Resolved
- Account Connected: $3,756.96
- VIX Data Collection: ✅ Working
- Web Monitor: ✅ Enhanced with dark theme
- Real-time Activity Log: ✅ Complete visibility
- All Critical Issues: ✅ Resolved

## Features

- **Multiple Trading Strategies**
  - Bull Strategy: Capitalizes on bullish market conditions
  - Bear Strategy: Profits from bearish market movements
  - **Volatility Strategy**: ✅ Trades on VIX volatility opportunities (now working)

- **Risk Management**
  - Position sizing based on account value
  - Maximum daily loss limits
  - Stop-loss and take-profit automation
  - Portfolio monitoring

- **Real-time Market Data**
  - Live market data from IBKR ✅
  - Stock screening based on momentum ✅
  - **VIX monitoring for market sentiment** ✅ Fixed
  - Sector analysis using ETFs (XLK, XLV, XLE, XLF, XLY, XLI)

- **Enhanced Web Dashboard**
  - **Dark theme with green accents** ✅ New
  - **Real-time activity log** ✅ See what bot is doing
  - Real-time portfolio monitoring
  - Trading activity log
  - Performance metrics
  - WebSocket updates

## Architecture

```
options_trading_bot_2026/
├── main_sync_with_web.py      # Main entry point with web monitor ✅
├── async_handler_2026.py       # IBKR connection handler ✅
├── execution_engine_2026/      # Trading execution logic ✅
├── risk_mgmt_2026/            # Risk management modules ✅
├── bull_module_2026/          # Bull strategy implementation ✅
├── bear_module_2026/          # Bear strategy implementation ✅
├── volatile_module_2026/      # Volatility strategy implementation ✅
├── stock_screener_2026/       # Stock screening logic ✅
├── news_handler_2026/         # News and sentiment analysis ✅
├── web_monitor_2026/          # Web dashboard (enhanced) ✅
└── config_2026/               # Configuration management ✅
```

## Prerequisites

- Python 3.11 or higher
- Interactive Brokers account
- IBKR Gateway or TWS running
- Market data subscriptions for options trading

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/options_trading_bot_2026.git
cd options_trading_bot_2026
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Quick Start

**Start the bot with web monitor:**
```bash
python main_sync_with_web.py
```

**Monitor in browser:**
- Open http://localhost:5001
- Watch real-time activity log
- Monitor portfolio and positions
- View market sentiment and VIX data

The bot will:
1. Connect to IBKR Gateway ✅
2. Start the enhanced web monitor ✅
3. Begin VIX-based volatility monitoring ✅
4. Execute market-driven strategies ✅

## Configuration

Edit the `.env` file with your settings:

- `IBKR_HOST`: IBKR Gateway host (default: 127.0.0.1)
- `IBKR_PORT`: IBKR Gateway port (default: 4001)
- `IBKR_CLIENT_ID`: Unique client ID for connection
- `MAX_DAILY_LOSS`: Maximum allowed daily loss
- `OPTIONS_WATCHLIST`: Comma-separated list of symbols to trade

See `.env.example` for all available configuration options.

## Enhanced Web Monitor

### New Features ✅
- **Dark theme** with professional green accents
- **Real-time activity log** showing bot decision-making:
  - NEWS: Market sentiment, VIX levels, sector analysis
  - SCREENING: Stock screening results and candidates
  - STRATEGY: Bull/Bear/Volatile strategy decisions
  - EXECUTION: Order placement and position management
  - RISK: Risk management and position sizing

### Dashboard Components
- Current portfolio value and P&L
- Active positions with real-time updates
- Market sentiment indicators (including VIX)
- Risk metrics and health status
- Recent actions and error log

## Trading Strategies

### Bull Strategy ✅
- Looks for bullish momentum in stocks
- Buys call options on uptrending stocks
- Uses technical indicators for entry/exit

### Bear Strategy ✅
- Identifies bearish market conditions
- Buys put options on downtrending stocks
- Implements protective stops

### Volatility Strategy ✅ **Now Working**
- **Monitors VIX and stock volatility** (fixed VIX data collection)
- Trades straddles/strangles on high IV
- Adjusts positions based on volatility changes
- Uses VIX Index data (sec_type='IND') for precise volatility measurement

## Risk Management

The bot implements several risk controls:
- Position sizing: 15% of account per trade
- Stop loss: 30% of position value
- Take profit: 50% of position value
- Maximum 5 concurrent positions
- Daily loss limit enforcement

## Recent Fixes Applied ✅

### 1. VIX Integration Fixed
- **Problem**: VIX data collection was broken, volatility strategy non-functional
- **Solution**: Fixed `sec_type` parameter support throughout IBKR client chain
- **Result**: VIX Index data now collected properly, volatility strategy working

### 2. Enhanced Web Monitor
- **Added**: Dark theme with green accents for professional appearance
- **Added**: Real-time activity log with timestamped entries
- **Added**: WebSocket-based real-time updates
- **Result**: Complete visibility into bot's decision-making process

### 3. News Handler Improvements
- **Enhanced**: Market sentiment analysis with VIX integration
- **Enhanced**: Sector analysis using ETFs instead of individual stocks
- **Enhanced**: Fallback mechanisms for data reliability

### 4. Architecture Validation
- **Verified**: All component dependencies working correctly
- **Verified**: Async/sync boundaries properly maintained
- **Verified**: Error handling and recovery mechanisms

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Strategies
1. Create a new module in the project root
2. Implement the strategy interface
3. Register in `execution_engine_2026/sync_engine.py`

## Deployment on Ubuntu

1. Install Python and dependencies:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

2. Clone and setup:
```bash
git clone https://github.com/yourusername/options_trading_bot_2026.git
cd options_trading_bot_2026
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure systemd service (optional):
```bash
sudo cp trading-bot.service /etc/systemd/system/
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

## Safety Features

- Paper trading mode for testing ✅
- Graceful shutdown handling ✅
- Connection retry logic ✅
- Error logging and notifications ✅
- Position limit enforcement ✅
- **VIX-based volatility monitoring** ✅

## Current Status

**✅ FULLY OPERATIONAL**
```
Account Value: $3,756.96
IBKR Connection: ✅ Connected
Web Monitor: ✅ http://localhost:5001
VIX Data: ✅ Collecting Index data
News Monitoring: ✅ Active
Stock Screening: ✅ S&P 500 universe
All Strategies: ✅ Bull/Bear/Volatile functional
```

## Troubleshooting

### Connection Issues
- Ensure IBKR Gateway is running ✅
- Check firewall settings for port 4001 ✅
- Verify client ID is unique ✅

### No Market Data
- Confirm market data subscriptions ✅
- Check if markets are open ✅
- Verify symbol list in configuration ✅

### VIX Data Issues (Fixed)
- **Previously**: sec_type parameter errors ❌
- **Now**: VIX Index data collection working ✅
- Volatility strategy fully functional ✅

## Dependencies

```
ib_insync==0.9.82
nest_asyncio>=1.5.0
numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
flask>=2.3.0
flask-socketio>=5.3.0  # For real-time web updates
werkzeug>=2.3.0
pytz==2023.3
pyyaml>=6.0
```

## License

This project is for educational purposes. Use at your own risk. Trading options involves significant risk of loss.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Disclaimer

This bot is for educational purposes only. Trading options carries substantial risk. Past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor.

---

**🚀 Ready for production trading with enhanced monitoring and VIX-based volatility strategies!**
