# Options Trading Bot 2026 - Strategy Integration Guide

## Architecture Overview

The bot follows a sophisticated sentiment-driven approach:

```
Market Sentiment Analysis → Stock Screening → Strategy Selection → Trade Execution
```

## Strategy Modules

### 1. Bull Module (bull_module_2026)
**Strategy**: Bull Call Spreads
- **When Active**: Bullish market sentiment detected
- **Entry Criteria**:
  - RSI between 40-70 (not oversold/overbought)
  - Price above 20 & 50 day moving averages
  - Upward trend strength > 2%
  - IV rank < 50% (not overpaying for options)
- **Risk Management**:
  - 2:1 minimum risk/reward ratio
  - 65% minimum probability of profit
  - Position sizing via Kelly Criterion
  - Max 2% portfolio risk per trade

### 2. Bear Module (bear_module_2026)
**Strategy**: Bear Put Spreads
- **When Active**: Bearish market sentiment detected
- **Entry Criteria**:
  - RSI between 30-60
  - Price below 20 & 50 day moving averages
  - Minimum 5 days in downtrend
  - Support level analysis
- **Risk Management**:
  - 2:1 minimum risk/reward ratio
  - 65% minimum probability of profit
  - Dynamic position sizing
  - Stop loss at 30% of debit paid

### 3. Volatile Module (volatile_module_2026)
**Strategies**: Straddles, Strangles, Iron Condors
- **When Active**: High volatility expected or uncertain market
- **Entry Criteria**:
  - IV rank > 70%
  - IV/HV ratio > 1.2
  - Event-driven volatility
  - Market uncertainty signals
- **Strategy Selection**:
  - **Straddle**: IV > 80%, volatility increasing
  - **Strangle**: IV > 70%, cheaper entry desired
  - **Iron Condor**: IV > 60%, range-bound expected

## Integration Flow

### 1. Sentiment Analysis (news_handler_2026)
```python
sentiment = {
    'bullish': True/False,     # Bull module activated
    'bearish': True/False,     # Bear module activated
    'volatile': True/False,    # Volatile module activated
    'confidence': 0.0-1.0,     # Conviction level
    'volatility_expected': 0.0-1.0
}
```

### 2. Stock Screening (stock_screener_2026)
- Filters universe based on sentiment
- Applies technical filters
- Returns ranked candidates

### 3. Strategy Execution (execution_engine_2026)
```python
# Concurrent strategy scanning based on sentiment
if sentiment['bullish']:
    bull_opportunities = await bull_module.scan_opportunities(symbols)
if sentiment['bearish']:
    bear_opportunities = await bear_module.scan_opportunities(symbols)
if sentiment['volatile']:
    volatile_opportunities = await volatile_module.scan_opportunities(symbols)
```

## Advanced Features

### Position Sizing
All modules use sophisticated position sizing:
1. **Kelly Criterion**: Optimal bet sizing based on edge
2. **Risk Limits**: Max 2-3% portfolio risk per trade
3. **Volatility Adjustment**: Smaller sizes in high volatility

### Probability Calculations
- Uses simplified Black-Scholes for probability estimates
- Adjusts for trend strength and volatility regime
- Incorporates historical volatility analysis

### Risk Metrics
Each opportunity includes:
- `probability_profit`: Win probability
- `risk_reward_ratio`: Potential profit/loss ratio
- `return_on_risk`: Expected value calculation
- `score`: Weighted combination of factors

## Configuration Parameters

### Bull Module
```python
long_call_delta_target = 0.40  # 40 delta
short_call_delta_target = 0.25  # 25 delta
min_probability_profit = 0.65   # 65%
optimal_days_to_expiry = 45
```

### Bear Module
```python
long_put_delta_target = -0.40   # -40 delta
short_put_delta_target = -0.25  # -25 delta
min_down_trend_days = 5
require_below_moving_averages = True
```

### Volatile Module
```python
min_iv_rank = 70               # 70th percentile
min_iv_to_hv_ratio = 1.2       # 20% premium
straddle_iv_threshold = 80     # Very high IV
iron_condor_iv_threshold = 60  # Elevated IV
```

## Trade Management

All modules implement position management:

1. **Profit Targets**:
   - Bull/Bear: 50% of max profit
   - Straddles: 25% profit
   - Iron Condors: 50% of credit

2. **Stop Losses**:
   - Directional spreads: 30% of debit
   - Straddles: 40% loss
   - Iron Condors: 30% of credit

3. **Active Monitoring**:
   - Real-time P&L tracking
   - Automatic exit execution
   - Risk limit enforcement

## Best Practices

1. **Start Small**: Use minimum position sizes initially
2. **Monitor Sentiment**: Watch for regime changes
3. **Respect Risk Limits**: Never override safety checks
4. **Review Logs**: Analyze trades for improvement
5. **Market Hours**: Best performance during liquid hours

## Performance Optimization

1. **Concurrent Processing**: All scans run in parallel
2. **Caching**: Market data cached to reduce API calls
3. **Smart Filtering**: Only top candidates analyzed deeply
4. **Efficient Orders**: Combo orders for multi-leg strategies

## Safety Features

1. **Portfolio Provider**: Centralized risk checking
2. **Position Limits**: Max concurrent trades enforced
3. **Capital Preservation**: Daily loss limits
4. **Connectivity Monitoring**: Automatic reconnection

## Future Enhancements

1. **Machine Learning**: Sentiment prediction models
2. **Greeks Management**: Real-time delta hedging
3. **Advanced Strategies**: Calendars, diagonals, butterflies
4. **Backtesting**: Historical strategy validation
5. **Multi-Broker**: Support for multiple brokers

## Risk Warning

⚠️ **All strategies involve substantial risk**:
- Options can expire worthless
- Spreads have defined but significant risk
- Market gaps can exceed stop losses
- Always use proper position sizing
- Never risk more than you can afford to lose 