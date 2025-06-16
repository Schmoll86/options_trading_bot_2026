"""
Thread-safe wrapper for IBKR client
Allows safe access from multiple threads by marshaling calls to the main thread
"""

import queue
import threading
import time
import logging
from typing import Any, Optional, Dict, List, Callable
from concurrent.futures import Future


class ThreadSafeIBKRWrapper:
    """
    Thread-safe wrapper for IBKR client that marshals all calls
    to the main thread where the IB connection lives.
    """
    
    def __init__(self, ibkr_client):
        self.ibkr_client = ibkr_client
        self.logger = logging.getLogger(__name__)
        self._request_queue = queue.Queue()
        self._response_futures = {}
        self._request_id = 0
        self._running = True
        self._main_thread_id = threading.current_thread().ident
        
    def _process_requests(self):
        """Process pending requests from other threads"""
        if threading.current_thread().ident != self._main_thread_id:
            return  # Only process in main thread
            
        try:
            # Process all pending requests
            while not self._request_queue.empty():
                try:
                    request_id, method_name, args, kwargs = self._request_queue.get_nowait()
                    future = self._response_futures.get(request_id)
                    
                    if future is None:
                        continue
                        
                    try:
                        # Call the actual method
                        method = getattr(self.ibkr_client, method_name)
                        result = method(*args, **kwargs)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                        
                except queue.Empty:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error processing requests: {e}")
    
    def _call_from_thread(self, method_name: str, *args, **kwargs):
        """Call a method from any thread"""
        # If we're in the main thread, call directly
        if threading.current_thread().ident == self._main_thread_id:
            method = getattr(self.ibkr_client, method_name)
            return method(*args, **kwargs)
            
        # Otherwise, queue the request
        self._request_id += 1
        request_id = self._request_id
        future = Future()
        
        self._response_futures[request_id] = future
        self._request_queue.put((request_id, method_name, args, kwargs))
        
        # Wait for response with timeout
        try:
            result = future.result(timeout=30)
            return result
        except Exception as e:
            self.logger.error(f"Error calling {method_name}: {e}")
            raise
        finally:
            # Clean up
            self._response_futures.pop(request_id, None)
    
    # Proxy all the main methods we need
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Thread-safe get_market_data"""
        return self._call_from_thread('get_market_data', symbol)
        
    def get_account_value(self, tag='NetLiquidation') -> float:
        """Thread-safe get_account_value"""
        return self._call_from_thread('get_account_value', tag)
        
    def get_positions(self) -> List:
        """Thread-safe get_positions"""
        return self._call_from_thread('get_positions')
        
    def get_historical_data(self, symbol: str, duration: str = '60 D', 
                          bar_size: str = '1 day') -> Any:
        """Thread-safe get_historical_data"""
        return self._call_from_thread('get_historical_data', symbol, duration, bar_size)
        
    def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict]:
        """Thread-safe get_options_chain"""
        return self._call_from_thread('get_options_chain', symbol, expiry)
        
    def place_order(self, contract, order) -> Optional[str]:
        """Thread-safe place_order"""
        return self._call_from_thread('place_order', contract, order)
        
    def get_account_summary(self) -> Dict:
        """Thread-safe get_account_summary"""
        return self._call_from_thread('get_account_summary')
        
    def is_trading_halted(self, symbol: str) -> bool:
        """Thread-safe is_trading_halted"""
        return self._call_from_thread('is_trading_halted', symbol)
        
    @property
    def connected(self) -> bool:
        """Check if connected"""
        return self.ibkr_client.connected if self.ibkr_client else False
        
    def disconnect(self):
        """Disconnect from IBKR"""
        self._running = False
        if self.ibkr_client:
            self.ibkr_client.disconnect()
            
    def stop(self):
        """Stop the wrapper"""
        self._running = False 