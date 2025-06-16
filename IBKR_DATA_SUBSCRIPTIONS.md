# IBKR Market Data Subscriptions Guide

## How to Check Your Data Subscriptions

### Via IBKR Gateway/TWS:
1. Open IB Gateway or Trader Workstation
2. Go to **Account → Account Management**
3. Navigate to **Settings → User Settings → Market Data Subscriptions**

### Common Subscription Levels:

#### Free/Basic:
- **Delayed data only** (15-20 min delay)
- **Snapshots**: Limited or not available for some symbols
- **Streaming**: Not available

#### IBKR Pro (Real-time):
- **US Securities Snapshot**: $1.50/month
- **US Equity and Options Add-On Streaming Bundle**: $4.95/month
- **NASDAQ (Network C/UTP)**: $1.50/month (waived with $30+ commissions)

## What Works with Limited Subscriptions:

### Snapshot Mode (Current Implementation):
- ✅ Works with basic subscriptions
- ✅ No streaming required
- ✅ Lower data usage
- ❌ Less frequent updates
- ❌ May have daily limits

### Alternative Solutions:
1. **Use delayed data** - Add `delayed=True` parameter
2. **Reduce symbols** - Monitor fewer stocks
3. **Use daily bars** - Historical data instead of real-time
4. **Paper trading** - Full data access in paper account

## Current Bot Configuration:
The bot now uses **snapshot-only mode** which should work with basic subscriptions.
Each `reqMktData` call with `snapshot=True`:
- Gets a single data point
- Doesn't maintain a subscription
- Has a limit (typically 100/sec)

## To Enable Real-Time Data:
1. Log into Account Management
2. Subscribe to appropriate data packages
3. Wait 10-15 minutes for activation
4. Restart IB Gateway 