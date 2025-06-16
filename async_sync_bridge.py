"""
Async-Sync Bridge for IBKR Client
Provides async methods that internally call sync methods
"""

import asyncio
from typing import Any, Dict, Optional
import logging


class AsyncIBKRBridge:
    """
    Bridge that provides async methods but internally uses the sync IBKR client.
    This allows the async screener to work with the sync wrapper.
    """
    
    def __init__(self, sync_client):
        self.sync_client = sync_client
        self.logger = logging.getLogger(__name__)
        
    async def reqMktData(self, contract):
        """Async wrapper for market data request"""
        # Run sync method in executor to not block the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.sync_client.get_market_data, 
            contract.symbol
        )
    
    async def reqHistoricalData(self, contract, duration='2 D', bar_size='1 hour', **kwargs):
        """Async wrapper for historical data request"""
        loop = asyncio.get_event_loop()
        
        # Get historical data and convert to expected format
        bars = await loop.run_in_executor(
            None,
            self.sync_client.get_historical_data,
            contract.symbol,
            duration,
            bar_size
        )
        
        # Convert bars to list of dicts if needed
        if bars and hasattr(bars, '__iter__'):
            result = []
            for bar in bars:
                if hasattr(bar, '__dict__'):
                    result.append(bar.__dict__)
                elif hasattr(bar, 'asdict'):
                    result.append(bar.asdict())
                else:
                    # Assume it's already a dict or create one
                    result.append({
                        'date': getattr(bar, 'date', None),
                        'open': getattr(bar, 'open', 0),
                        'high': getattr(bar, 'high', 0),
                        'low': getattr(bar, 'low', 0),
                        'close': getattr(bar, 'close', 0),
                        'volume': getattr(bar, 'volume', 0)
                    })
            return result
        return []
    
    async def reqNewsArticle(self, contract):
        """Async wrapper for news - returns empty list as IBKR news requires special permissions"""
        return []
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Direct pass-through for sync methods"""
        return self.sync_client.get_market_data(symbol)
    
    def get_historical_data(self, symbol: str, duration: str = '60 D', bar_size: str = '1 day'):
        """Direct pass-through for sync methods"""
        return self.sync_client.get_historical_data(symbol, duration, bar_size)
    
    def is_trading_halted(self, symbol: str) -> bool:
        """Check if trading is halted"""
        return self.sync_client.is_trading_halted(symbol)
    
    @property
    def connected(self):
        """Check if connected"""
        return self.sync_client.connected
    
    # Add other pass-through methods as needed
    def __getattr__(self, name):
        """Pass through any other attributes to the sync client"""
        return getattr(self.sync_client, name) 