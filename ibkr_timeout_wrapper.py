"""
IBKR Timeout Wrapper
Wraps IBKR client methods with timeouts to prevent hanging
"""

import time
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


class IBKRTimeoutWrapper:
    """Wraps IBKR client with timeout functionality"""
    
    def __init__(self, ibkr_client, default_timeout=10):
        self.client = ibkr_client
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def get_market_data(self, symbol: str, sec_type: str = 'STK', timeout: Optional[int] = None) -> Optional[Dict]:
        """Get market data with timeout and sec_type support"""
        timeout = timeout or self.default_timeout
        
        try:
            # Check if client supports sec_type parameter
            if hasattr(self.client, 'get_market_data'):
                method = getattr(self.client, 'get_market_data')
                import inspect
                sig = inspect.signature(method)
                
                if 'sec_type' in sig.parameters:
                    # Client supports sec_type, pass it through
                    future = self.executor.submit(self.client.get_market_data, symbol, sec_type)
                else:
                    # Legacy client - just pass symbol
                    future = self.executor.submit(self.client.get_market_data, symbol)
            else:
                self.logger.error(f"Client does not have get_market_data method")
                return None
            
            result = future.result(timeout=timeout)
            self.logger.debug(f"Got market data for {symbol}: {result}")
            return result
        except FutureTimeoutError:
            self.logger.warning(f"Timeout getting market data for {symbol} after {timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, duration: str = '60 D', 
                          bar_size: str = '1 day', timeout: Optional[int] = None) -> Any:
        """Get historical data with timeout"""
        timeout = timeout or self.default_timeout
        
        try:
            future = self.executor.submit(
                self.client.get_historical_data, 
                symbol, duration, bar_size
            )
            return future.result(timeout=timeout)
        except FutureTimeoutError:
            self.logger.warning(f"Timeout getting historical data for {symbol} after {timeout}s")
            return []
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    def __getattr__(self, name):
        """Pass through other attributes to the wrapped client"""
        return getattr(self.client, name)
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 