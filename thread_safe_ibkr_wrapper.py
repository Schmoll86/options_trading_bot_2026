"""
Thread-Safe IBKR Wrapper - Clean Version
Provides thread-safe access to IBKR functionality with all required methods.
"""

import logging
import threading
from datetime import datetime, time
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class ThreadSafeIBKRWrapper:
    """Thread-safe wrapper for IBKR operations"""
    
    def __init__(self, sync_client):
        """
        Initialize with sync IBKR client (IBKRSyncWrapper)
        
        Args:
            sync_client: IBKRSyncWrapper instance
        """
        self.sync_client = sync_client
        self._lock = threading.Lock()
        
    def get_account_value(self) -> float:
        """Get current account value"""
        with self._lock:
            try:
                return self.sync_client.get_account_value()
            except Exception as e:
                logger.error(f"Error getting account value: {e}")
                return 0.0
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for symbol"""
        with self._lock:
            try:
                return self.sync_client.get_market_data(symbol) or {}
            except Exception as e:
                logger.error(f"Error getting market data for {symbol}: {e}")
                return {}
    
    def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict]:
        """Get options chain for symbol"""
        with self._lock:
            try:
                return self.sync_client.get_options_chain(symbol, expiry) or []
            except Exception as e:
                logger.error(f"Error getting options chain for {symbol}: {e}")
                return []
    
    def get_historical_data(self, symbol: str, duration: str = "60 D", bar_size: str = "1 day") -> Any:
        """Get historical data for symbol"""
        with self._lock:
            try:
                return self.sync_client.get_historical_data(symbol, duration, bar_size)
            except Exception as e:
                logger.error(f"Error getting historical data for {symbol}: {e}")
                return []
    
    def place_order(self, contract, order) -> Optional[str]:
        """Place an order"""
        with self._lock:
            try:
                return self.sync_client.place_order(contract, order)
            except Exception as e:
                logger.error(f"Error placing order: {e}")
                return None
    
    def get_positions(self) -> List:
        """Get current positions"""
        with self._lock:
            try:
                return self.sync_client.get_positions() or []
            except Exception as e:
                logger.error(f"Error getting positions: {e}")
                return []
    
    def reqContractDetails(self, contract) -> List:
        """Get contract details"""
        with self._lock:
            try:
                return self.sync_client.reqContractDetails(contract) or []
            except Exception as e:
                logger.error(f"Error getting contract details: {e}")
                return []
    
    def calculate_max_trade_size(self, symbol: str) -> float:
        """Calculate maximum trade size based on account value and risk management"""
        try:
            account_value = self.get_account_value()
            # Use 10% of account value as maximum position size
            max_position_value = account_value * 0.10
            
            # Get current market price
            market_data = self.get_market_data(symbol)
            if not market_data or 'last' not in market_data:
                logger.warning(f"No market data for {symbol}, using conservative size")
                return max_position_value / 100  # Conservative fallback
            
            current_price = market_data['last']
            if current_price <= 0:
                logger.warning(f"Invalid price for {symbol}: {current_price}")
                return max_position_value / 100
            
            # Calculate number of shares based on position value
            max_shares = int(max_position_value / current_price)
            return max(1, max_shares)  # At least 1 share
            
        except Exception as e:
            logger.error(f"Error calculating max trade size for {symbol}: {e}")
            return 1  # Conservative fallback
    
    def is_trading_halted(self, symbol: str) -> bool:
        """Check if trading is halted for a symbol"""
        try:
            # Check market hours first
            now = datetime.now().time()
            market_open = time(9, 30)  # 9:30 AM
            market_close = time(16, 0)  # 4:00 PM
            
            # Check if within market hours (basic check)
            if not (market_open <= now <= market_close):
                return True
            
            # Get market data to check if symbol is tradeable
            market_data = self.get_market_data(symbol)
            if not market_data:
                logger.warning(f"No market data for {symbol}, assuming halted")
                return True
            
            # Check if we have valid bid/ask or last price
            bid = market_data.get('bid', 0)
            ask = market_data.get('ask', 0)
            last = market_data.get('last', 0)
            
            # If we have a last price, consider it tradeable
            if last > 0:
                return False
            
            # Otherwise check bid/ask
            if bid <= 0 or ask <= 0:
                logger.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
                return True
            
            # Check spread - if too wide, consider halted
            spread_pct = abs(ask - bid) / ((ask + bid) / 2) if (ask + bid) > 0 else 1
            if spread_pct > 0.1:  # 10% spread threshold
                logger.warning(f"Wide spread for {symbol}: {spread_pct:.2%}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if trading halted for {symbol}: {e}")
            return True  # Conservative approach - assume halted if error
    
    @property
    def connected(self) -> bool:
        """Check if connected to IBKR"""
        try:
            return getattr(self.sync_client, 'connected', False)
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        try:
            if hasattr(self.sync_client, 'disconnect'):
                self.sync_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def __getattr__(self, name):
        """Delegate any other attributes to the sync client"""
        if hasattr(self.sync_client, name):
            return getattr(self.sync_client, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") 