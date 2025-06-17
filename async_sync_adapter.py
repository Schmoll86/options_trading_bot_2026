"""
Async-Sync Adapter for IBKR Client following Options Trading Bot 2026 Architecture
Bridges synchronous strategy modules with asynchronous IBKR operations
"""

import asyncio
import logging
from typing import Any, Optional, Dict, List


class AsyncSyncAdapter:
    """
    Adapter that makes async IBKR operations available to synchronous strategy modules.
    
    Architecture Layer: Core Infrastructure (Layer 2)
    Dependencies: AsyncHandler2026 (async IBKR client)
    Used By: ThreadSafeIBKRWrapper, Execution Engine
    
    Data Flow: Sync Strategy → AsyncSyncAdapter → AsyncHandler → IBKR Gateway
    """
    
    def __init__(self, sync_client):
        """
        Initialize with sync IBKR client
        
        Args:
            sync_client: IBKRSyncWrapper or ThreadSafeIBKRWrapper instance
        """
        self.sync_client = sync_client
        self.logger = logging.getLogger(__name__)
        
    # =============================================================================
    # CORE MARKET DATA METHODS
    # =============================================================================
    
    async def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Async wrapper for sync get_market_data
        Required by: All strategy modules
        """
        try:
            # Call the sync method directly
            return self.sync_client.get_market_data(symbol)
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, duration: str = '60 D', bar_size: str = '1 day') -> Any:
        """
        Async wrapper for sync get_historical_data
        Required by: Strategy modules for technical analysis
        """
        try:
            # Call the sync method directly
            return self.sync_client.get_historical_data(symbol, duration, bar_size)
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    async def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict]:
        """
        Async wrapper for sync get_options_chain
        Required by: Options strategy modules (bull/bear/volatile)
        """
        try:
            # Call the sync method directly
            return self.sync_client.get_options_chain(symbol, expiry) or []
        except Exception as e:
            self.logger.error(f"Error getting options chain for {symbol}: {e}")
            return []
    
    # =============================================================================
    # ACCOUNT & PORTFOLIO METHODS
    # =============================================================================
    
    async def get_account_value(self, tag='NetLiquidation') -> float:
        """
        Async wrapper for sync get_account_value
        Required by: Risk management, position sizing
        """
        try:
            # Call the sync method directly
            result = self.sync_client.get_account_value()
            return float(result) if result else 0.0
        except Exception as e:
            self.logger.error(f"Error getting account value: {e}")
            return 0.0
    
    async def get_positions(self) -> List:
        """
        Async wrapper for sync get_positions
        Required by: Portfolio monitoring, position management
        """
        try:
            # Call the sync method directly
            return self.sync_client.get_positions() or []
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_summary(self) -> Dict:
        """
        Async wrapper for sync get_account_summary
        Required by: Risk management
        """
        try:
            # Call the sync method directly if available
            if hasattr(self.sync_client, 'get_account_summary'):
                return self.sync_client.get_account_summary() or {}
            else:
                # Fallback to account value only
                account_value = self.sync_client.get_account_value()
                return {'NetLiquidation': account_value} if account_value else {}
        except Exception as e:
            self.logger.error(f"Error getting account summary: {e}")
            return {}
    
    # =============================================================================
    # ORDER EXECUTION METHODS
    # =============================================================================
    
    async def place_order(self, contract: Any, order: Any) -> Optional[str]:
        """
        Async wrapper for sync place_order
        Required by: Execution engine
        """
        try:
            # Call the sync method directly
            return self.sync_client.place_order(contract, order)
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
    
    async def reqContractDetails(self, contract) -> List:
        """
        Async wrapper for sync reqContractDetails
        Required by: Options contract validation
        """
        try:
            # Call the sync method directly
            return self.sync_client.reqContractDetails(contract) or []
        except Exception as e:
            self.logger.error(f"Error getting contract details: {e}")
            return []
    
    # =============================================================================
    # TRADING STATE METHODS
    # =============================================================================
    
    async def is_trading_halted(self, symbol: str) -> bool:
        """
        Check if trading is halted for a symbol
        Required by: All strategy execute_trade methods
        """
        try:
            # Call the sync method directly
            return self.sync_client.is_trading_halted(symbol)
        except Exception as e:
            self.logger.error(f"Error checking trading halt for {symbol}: {e}")
            return False

    def calculate_max_trade_size(self, symbol: str) -> float:
        """
        Calculate maximum trade size based on account value and risk management
        Required by: All strategy modules for position sizing
        """
        try:
            # Call the sync method directly
            return self.sync_client.calculate_max_trade_size(symbol)
        except Exception as e:
            self.logger.error(f"Error calculating max trade size for {symbol}: {e}")
            return 1.0  # Conservative fallback
    
    # =============================================================================
    # RISK MANAGEMENT INTERFACE
    # =============================================================================
    
    def can_trade(self, cost: float) -> bool:
        """
        Check if trade is within risk limits
        Required by: Strategy modules
        """
        try:
            if hasattr(self.sync_client, 'can_trade'):
                return self.sync_client.can_trade(cost)
            return True  # Default to allowing trades if method not implemented
        except Exception as e:
            self.logger.error(f"Error checking can_trade: {e}")
            return True
    
    # =============================================================================
    # CONNECTION MANAGEMENT
    # =============================================================================
    
    @property
    def connected(self) -> bool:
        """Check if connected to IBKR"""
        try:
            return getattr(self.sync_client, 'connected', False)
        except Exception:
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        try:
            if hasattr(self.sync_client, 'disconnect'):
                self.sync_client.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    # =============================================================================
    # FALLBACK DELEGATION
    # =============================================================================
    
    def __getattr__(self, name):
        """
        Fallback to sync client for any other attributes
        Ensures complete interface compatibility
        """
        if hasattr(self.sync_client, name):
            attr = getattr(self.sync_client, name)
            if callable(attr):
                self.logger.debug(f"Delegating method call: {name}")
            return attr
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") 