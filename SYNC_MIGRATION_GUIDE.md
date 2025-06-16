# Synchronous Architecture Migration Guide

## Overview

This guide explains how to migrate from the current async-heavy implementation to a more stable hybrid approach where async operations are isolated in a dedicated handler.

## Benefits of the Hybrid Approach

### 1. **Stability**
- No more "event loop already running" errors
- Easier debugging without async stack traces
- Predictable execution flow

### 2. **Simplicity**
- Synchronous code is easier to understand
- No need to manage event loops throughout the codebase
- Traditional error handling with try/catch

### 3. **Maintainability**
- Clear separation between sync and async code
- Async complexity isolated to one module
- Easier to add new features

### 4. **Performance**
- Still get async benefits where needed (IBKR API calls)
- Simpler threading model
- No overhead from unnecessary async operations

## Architecture Comparison

### Current (Async Everywhere)
```
main.py (async) → modules (async) → IBKR (async)
   ↓
Event loop conflicts, complex error handling
```

### New (Hybrid)
```
main_sync.py → modules (sync) → async_handler → IBKR (async)
                                     ↓
                              Isolated event loop
```

## Key Components

### 1. `async_handler_2026.py`
- Manages a dedicated event loop in a separate thread
- Provides synchronous wrappers for all async operations
- Handles all IBKR API communication

### 2. `main_sync.py`
- Completely synchronous main entry point
- Simple initialization and shutdown
- No event loop management

### 3. `sync_engine.py`
- Synchronous execution engine
- Uses threading for background tasks
- Clean, readable trading logic

## Migration Steps

### Step 1: Test the New Architecture
```bash
# Run the sync version alongside the async version
python main_sync.py
```

### Step 2: Update Modules Gradually
Convert modules from async to sync one at a time:

1. **Remove async/await keywords**
   ```python
   # Before
   async def execute_trade(self, symbol):
       data = await self.ibkr_client.get_market_data(symbol)
   
   # After
   def execute_trade(self, symbol):
       data = self.ibkr_client.get_market_data(symbol)
   ```

2. **Update method signatures**
   ```python
   # Before
   async def analyze_market(self) -> MarketCondition:
   
   # After
   def analyze_market(self) -> MarketCondition:
   ```

3. **Replace asyncio.create_task with threading**
   ```python
   # Before
   task = asyncio.create_task(self._monitor_loop())
   
   # After
   thread = threading.Thread(target=self._monitor_loop)
   thread.start()
   ```

### Step 3: Update Configuration
No changes needed - the sync version uses the same configuration.

### Step 4: Testing
1. **Unit Tests**: Update tests to remove async
2. **Integration Tests**: Test with paper trading first
3. **Monitor Logs**: Check for any async-related errors

## Usage Examples

### Starting the Bot
```bash
# Old way (async)
python main.py

# New way (sync)
python main_sync.py
```

### Calling IBKR Methods
```python
# All methods work the same, just without await
client = create_sync_ibkr_client()
client.connect()

# Get market data
data = client.get_market_data('AAPL')

# Place order
order_id = client.place_order(contract, order)

# Get positions
positions = client.get_positions()

client.disconnect()
```

## Troubleshooting

### Issue: Module still using async
**Solution**: Check all methods in the module and remove async/await keywords.

### Issue: Event loop errors
**Solution**: Ensure you're using the sync client wrapper, not the raw IBKR client.

### Issue: Performance concerns
**Solution**: The async operations still happen in the background - performance should be the same or better.

## Best Practices

1. **Keep it Simple**: Don't add async unless absolutely necessary
2. **Use Threading Sparingly**: Only for long-running background tasks
3. **Error Handling**: Use standard try/except blocks
4. **Logging**: Add clear logging at each step

## Rollback Plan

If you need to rollback:
1. The original async code is still in `main.py`
2. All async modules are unchanged
3. Simply switch back to running `python main.py`

## Conclusion

The hybrid approach gives us the best of both worlds:
- Async performance where needed (IBKR API)
- Synchronous simplicity everywhere else
- Better stability and maintainability

Start with running `main_sync.py` in parallel with your existing setup, then gradually migrate once you're comfortable with the improved stability. 