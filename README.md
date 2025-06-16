# Options Trading Bot 2026 🚀

An automated options trading bot built with Python that connects to Interactive Brokers (IBKR) for live trading. The bot implements multiple strategies (Bull, Bear, Volatility) and includes risk management, real-time monitoring, and a web dashboard.

## Features

- **Multiple Trading Strategies**
  - Bull Strategy: Capitalizes on bullish market conditions
  - Bear Strategy: Profits from bearish market movements
  - Volatility Strategy: Trades on high volatility opportunities

- **Risk Management**
  - Position sizing based on account value
  - Maximum daily loss limits
  - Stop-loss and take-profit automation
  - Portfolio monitoring

- **Real-time Market Data**
  - Live market data from IBKR
  - Stock screening based on momentum
  - VIX monitoring for market sentiment

- **Web Dashboard**
  - Real-time portfolio monitoring
  - Trading activity log
  - Performance metrics
  - WebSocket updates

## Architecture

```
options_trading_bot_2026/
├── main_sync_with_web.py      # Main entry point with web monitor
├── async_handler_2026.py       # IBKR connection handler
├── execution_engine_2026/      # Trading execution logic
├── risk_mgmt_2026/            # Risk management modules
├── bull_module_2026/          # Bull strategy implementation
├── bear_module_2026/          # Bear strategy implementation
├── volatile_module_2026/      # Volatility strategy implementation
├── stock_screener_2026/       # Stock screening logic
├── web_monitor_2026/          # Web dashboard
└── config_2026/               # Configuration management
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

## Configuration

Edit the `.env` file with your settings:

- `IBKR_HOST`: IBKR Gateway host (default: 127.0.0.1)
- `IBKR_PORT`: IBKR Gateway port (default: 4001)
- `IBKR_CLIENT_ID`: Unique client ID for connection
- `MAX_DAILY_LOSS`: Maximum allowed daily loss
- `OPTIONS_WATCHLIST`: Comma-separated list of symbols to trade

See `.env.example` for all available configuration options.

## Usage

### Start the Trading Bot

```bash
python main_sync_with_web.py
```

The bot will:
1. Connect to IBKR Gateway
2. Start the web monitor on http://localhost:5001
3. Begin monitoring markets and executing trades

### Monitor Performance

Open http://localhost:5001 in your browser to view:
- Current portfolio value
- Active positions
- Recent trades
- Performance metrics

### Stop the Bot

Press `Ctrl+C` to gracefully shutdown the bot.

## Trading Strategies

### Bull Strategy
- Looks for bullish momentum in stocks
- Buys call options on uptrending stocks
- Uses technical indicators for entry/exit

### Bear Strategy
- Identifies bearish market conditions
- Buys put options on downtrending stocks
- Implements protective stops

### Volatility Strategy
- Monitors VIX and stock volatility
- Trades straddles/strangles on high IV
- Adjusts positions based on volatility changes

## Risk Management

The bot implements several risk controls:
- Position sizing: 15% of account per trade
- Stop loss: 30% of position value
- Take profit: 50% of position value
- Maximum 5 concurrent positions
- Daily loss limit enforcement

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

- Paper trading mode for testing
- Graceful shutdown handling
- Connection retry logic
- Error logging and notifications
- Position limit enforcement

## Troubleshooting

### Connection Issues
- Ensure IBKR Gateway is running
- Check firewall settings for port 4001
- Verify client ID is unique

### No Market Data
- Confirm market data subscriptions
- Check if markets are open
- Verify symbol list in configuration

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
