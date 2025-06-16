# Options Trading Bot 2026 - Architecture Documentation

## System Overview

The Options Trading Bot 2026 is an automated trading system designed to execute options strategies through Interactive Brokers (IBKR) Gateway. It employs sentiment analysis, technical screening, and risk management to trade bull/bear spreads and volatility strategies.

## Core Architecture

### 1. Entry Points

- **main.py**: Async version (deprecated due to event loop issues)
- **main_sync.py**: Synchronous version without web monitor
- **main_sync_with_web.py**: Production version with web monitoring
- **monitor_only.py**: Read-only mode for market analysis
- **start_bot_safe.py**: Safe startup script with pre-flight checks

### 2. Component Layers

#### Layer 1: External Integration
- **IBKR Gateway Connection** (Port 4001)
  - Market data streaming
  - Order execution
  - Account management
  - Historical data retrieval

#### Layer 2: Core Infrastructure
- **IBKRClient2026**: Main IBKR API wrapper using ib_insync
- **AsyncHandler2026**: Handles async operations in sync context
- **ConfigLoader2026**: Environment configuration management

#### Layer 3: Data Processing
- **NewsHandler2026**: 
  - Multi-source news aggregation
  - Sentiment analysis
  - Event detection
  
- **StockScreener2026**:
  - Technical indicator calculation
  - Market breadth analysis
  - Options chain analysis
  - Candidate selection

#### Layer 4: Risk Management
- **RiskManager2026**:
  - Position sizing (Kelly Criterion)
  - Portfolio limits enforcement
  - Risk/reward validation
  - Maximum loss prevention
  
- **PortfolioMonitor2026**:
  - Real-time P&L tracking
  - Position monitoring
  - Alert generation
  - Performance metrics

#### Layer 5: Strategy Implementation
- **BullModule2026**: Bull call spread strategies
- **BearModule2026**: Bear put spread strategies  
- **VolatileModule2026**: Volatility strategies (straddles, strangles, iron condors)

#### Layer 6: Execution & Monitoring
- **ExecutionEngine2026**:
  - Order construction
  - Multi-leg execution
  - Fill monitoring
  - Strategy coordination
  
- **BotMonitorServer**: 
  - Web UI (Port 5001)
  - Real-time dashboards
  - Performance visualization
  - System health monitoring

### 3. Data Flow

```
1. Market Data → IBKR Gateway → IBKRClient2026
2. News Data → NewsHandler2026 → Sentiment Scores
3. Market + News → StockScreener2026 → Candidate Stocks
4. Candidates → Strategy Modules → Trade Signals
5. Signals → RiskManager2026 → Validated Orders
6. Orders → ExecutionEngine2026 → IBKR Gateway
7. Fills → PortfolioMonitor2026 → Performance Tracking
8. All Data → BotMonitorServer → Web UI
```

### 4. Key Design Patterns

1. **Dependency Injection**: Components receive dependencies through constructors
2. **Event-Driven**: Market events trigger strategy evaluations
3. **Strategy Pattern**: Modular strategy implementations
4. **Observer Pattern**: Portfolio monitoring and alerts
5. **Singleton**: IBKR connection management

### 5. Threading Model

- **Main Thread**: Application lifecycle, IBKR connection
- **Monitor Thread**: Portfolio monitoring loop
- **Web Server Thread**: Flask application for UI
- **Update Thread**: Periodic data updates for web UI

### 6. Error Handling

1. **Connection Failures**: Automatic reconnection with exponential backoff
2. **Market Data Errors**: Fallback to cached data
3. **Execution Errors**: Order retry with modified parameters
4. **Risk Violations**: Immediate order cancellation
5. **System Errors**: Graceful shutdown with position flattening

### 7. Configuration Management

Environment variables (.env file):
- IBKR connection settings
- Risk parameters
- Strategy thresholds
- API keys for news sources
- Logging configuration

### 8. Security Features

1. **Read-only Mode**: monitor_only.py for safe observation
2. **Pre-flight Checks**: Connection validation before trading
3. **Position Limits**: Hard stops on portfolio exposure
4. **Emergency Shutdown**: Graceful exit with open position handling
5. **Audit Logging**: Complete transaction history

## Deployment Architecture

### Production Setup
```
┌─────────────────────┐     ┌──────────────────┐
│   Ubuntu Server     │     │   IBKR Gateway   │
│  - Python 3.11+     │────▶│  - Port 4001     │
│  - Virtual Env      │     │  - Paper/Live    │
│  - Systemd Service  │     └──────────────────┘
└─────────────────────┘              │
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌──────────────────┐
│   Web Monitor UI    │     │  Market Data &   │
│  - Port 5001        │     │  Order Execution │
│  - Real-time Charts │     └──────────────────┘
└─────────────────────┘
```

### Development Setup
- Local IBKR Gateway or TWS
- Python virtual environment
- Test with paper trading account
- Separate configuration for dev/test/prod

## Scalability Considerations

1. **Horizontal Scaling**: Multiple strategy modules can run independently
2. **Data Caching**: Reduce API calls with intelligent caching
3. **Async Operations**: Non-blocking I/O for market data
4. **Database Integration**: Optional PostgreSQL for historical data
5. **Message Queue**: Optional Redis for strategy coordination

## Monitoring & Observability

1. **Logging**: Structured logs with rotation
2. **Metrics**: Performance, latency, success rates
3. **Alerts**: Email/SMS for critical events
4. **Dashboard**: Real-time web UI
5. **Health Checks**: Automated system validation 