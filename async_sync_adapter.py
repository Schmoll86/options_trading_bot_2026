"""
Async/Sync adapter for strategy compatibility
Wraps synchronous IBKR client methods as async methods
"""

import asyncio
from typing import Any, Dict, List, Optional


class AsyncSyncAdapter:
    """
    Adapter that wraps synchronous IBKR client methods as async methods.
    This allows async strategies to work with the sync execution engine.
    """
    
    def __init__(self, sync_client):
        self.sync_client = sync_client
        
    async def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Wrap sync get_market_data as async"""
        # Run sync method in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.sync_client.get_market_data, 
            symbol
        )
        
    async def get_historical_data(self, symbol: str, duration: str = '60 D', 
                                bar_size: str = '1 day') -> Any:
        """Wrap sync get_historical_data as async"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.sync_client.get_historical_data,
            symbol,
            duration,
            bar_size
        )
        
    async def get_options_chain(self, symbol: str, expiry: str) -> Optional[List[Dict]]:
        """Wrap sync get_options_chain as async"""
        loop = asyncio.get_event_loop()
        # Check if method exists on sync client
        if hasattr(self.sync_client, 'get_options_chain'):
            return await loop.run_in_executor(
                None,
                self.sync_client.get_options_chain,
                symbol,
                expiry
            )
        else:
            # Return empty chain if method not implemented
            return []
            
    async def reqContractDetails(self, contract: Any) -> List[Any]:
        """Wrap sync reqContractDetails as async"""
        loop = asyncio.get_event_loop()
        if hasattr(self.sync_client, 'reqContractDetails'):
            return await loop.run_in_executor(
                None,
                self.sync_client.reqContractDetails,
                contract
            )
        else:
            return []
            
    async def place_order(self, contract: Any, order: Any) -> Optional[str]:
        """Wrap sync place_order as async"""
        loop = asyncio.get_event_loop()
        if hasattr(self.sync_client, 'place_order'):
            return await loop.run_in_executor(
                None,
                self.sync_client.place_order,
                contract,
                order
            )
        else:
            # Log that actual trading is not implemented
            import logging
            logging.getLogger(__name__).info(
                f"Would place order for {contract.symbol if hasattr(contract, 'symbol') else 'unknown'}"
            )
            return None
            
    def get_positions(self) -> List[Any]:
        """Direct passthrough for sync methods"""
        return self.sync_client.get_positions()
        
    def get_account_value(self) -> float:
        """Direct passthrough for sync methods"""
        return self.sync_client.get_account_value()
        
    def can_trade(self, cost: float) -> bool:
        """Direct passthrough for sync methods"""
        if hasattr(self.sync_client, 'can_trade'):
            return self.sync_client.can_trade(cost)
        return True  # Default to allowing trades if method not implemented
        
    def __getattr__(self, name):
        """Fallback to sync client for any other attributes"""
        return getattr(self.sync_client, name) 