# Quick Reference - Running the Options Trading Bot

## Pre-requisites:
1. IB Gateway running on port 4001
2. Virtual environment activated: `source venv/bin/activate`

## To Run:
```bash
python main_sync_with_web.py
```

## To Test Market Data:
```bash
python test_market_data.py
```

## Web Monitor:
Once running, access at: http://localhost:5001

## Current Status:
- Bot runs without hanging ✅
- Market data not working in bot context ❌
- Safe to run - won't make trades without market data

## To Stop:
Press Ctrl+C (bot will shutdown gracefully)

## Logs:
- Live logs: `options_bot_2026_live.log`
- Console output: Real-time in terminal

## Environment Variables (.env):
```
IBKR_HOST=127.0.0.1
IBKR_PORT=4001
IBKR_CLIENT_ID=10
``` 