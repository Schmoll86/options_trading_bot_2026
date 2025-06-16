"""
Async Handler - Centralizes all async operations for the trading bot
This module handles all IBKR async operations and provides synchronous interfaces
"""

import asyncio
import threading
import queue
from typing import Any, Dict, Optional, List, Callable
import logging
from concurrent.futures import Future
import time
import nest_asyncio
from ib_insync import IB

# Allow nested event loops (fixes ib_insync issues)
nest_asyncio.apply()


class AsyncHandler2026:
    """
    Manages all async operations in a dedicated thread with its own event loop.
    Provides synchronous methods that can be called from anywhere in the codebase.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._loop = None
        self._thread = None
        self._started = False
        self._request_queue = queue.Queue()
        self._shutdown_event = threading.Event()
        self.ib = None
        self._connected = False
        
    def start(self):
        """Start the async handler in a separate thread"""
        if self._started:
            return
            
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._started = True
        
        # Wait for loop to be ready
        time.sleep(0.1)
        self.logger.info("Async handler started")
        
    def stop(self):
        """Stop the async handler"""
        if not self._started:
            return
            
        self._shutdown_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._started = False
        self.logger.info("Async handler stopped")
        
    def _run_loop(self):
        """Run the event loop in a separate thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._process_requests())
        except Exception as e:
            self.logger.error(f"Error in async loop: {e}")
        finally:
            self._loop.close()
            
    async def _process_requests(self):
        """Process requests from the queue"""
        while not self._shutdown_event.is_set():
            try:
                # Check for requests
                try:
                    request = self._request_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue
                    
                # Process the request
                func, args, kwargs, future = request
                try:
                    result = await func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                    
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                
    def run_async(self, coro_func: Callable, *args, **kwargs) -> Any:
        """
        Run an async function synchronously by submitting it to the async loop.
        
        Args:
            coro_func: The async function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the async function
        """
        if not self._started:
            raise RuntimeError("Async handler not started")
            
        future = Future()
        self._request_queue.put((coro_func, args, kwargs, future))
        
        # Wait for result with timeout
        try:
            return future.result(timeout=30)
        except TimeoutError:
            raise TimeoutError("Async operation timed out")

    def connect(self, host='127.0.0.1', port=4001, client_id=10):
        """Connect to IBKR synchronously"""
        try:
            self.ib = IB()
            self.ib.connect(host, port, clientId=client_id)
            
            # Switch to delayed data if live data isn't available
            self.ib.reqMarketDataType(4)  # 4 = Delayed data
            
            self.ib.sleep(0.5)  # Give time for the setting to take effect
            
            self._connected = True
            self.logger.info(f"Connected to IBKR at {host}:{port}")
        except Exception as e:
            self.logger.error(f"Error connecting to IBKR: {e}")


class IBKRSyncWrapper:
    """
    Synchronous wrapper for IBKR operations using ib_insync's built-in sync methods
    """
    
    def __init__(self, host='127.0.0.1', port=4001, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Synchronously connect to IBKR"""
        from ib_insync import IB
        
        self.ib = IB()
        self.ib.connect(self.host, self.port, clientId=self.client_id)
        
        # Switch to delayed data mode for better reliability
        self.ib.reqMarketDataType(4)  # 4 = Delayed data
        self.ib.sleep(0.5)  # Give time for the setting to take effect
        
        self.logger.info(f"Connected to IBKR at {self.host}:{self.port} (using delayed data)")
        
        # Wait for synchronization to complete
        self.logger.info("Waiting for IBKR synchronization...")
        self.ib.sleep(1)  # Give IBKR time to fully synchronize
        self.logger.info("IBKR synchronization complete")
        
    def disconnect(self):
        """Synchronously disconnect from IBKR"""
        if self.ib:
            self.ib.disconnect()
            self.logger.info("Disconnected from IBKR")
            
    def get_account_value(self, tag='NetLiquidation') -> float:
        """Synchronously get account value"""
        if not self.ib or not self.ib.isConnected():
            return 0.0
            
        account_values = self.ib.accountValues()
        for av in account_values:
            if av.tag == tag and av.currency == 'USD':
                return float(av.value)
        return 0.0
        
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get market data using the simplest approach that works"""
        if not self.ib or not self.ib.isConnected():
            self.logger.warning(f"Not connected to IBKR")
            return None
            
        self.logger.info(f"get_market_data called for {symbol}")
        
        try:
            # Create contract based on symbol type
            if symbol == 'VIX':
                from ib_insync import Index
                contract = Index('VIX', 'CBOE')
            else:
                from ib_insync import Stock
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Always qualify contracts to ensure proper setup
            try:
                qualified = self.ib.qualifyContracts(contract)
                if qualified:
                    contract = qualified[0]
                    self.logger.debug(f"Contract qualified for {symbol}: {contract}")
                else:
                    self.logger.warning(f"Could not qualify contract for {symbol}")
            except Exception as e:
                self.logger.warning(f"Error qualifying {symbol}: {e}")
            
            # Request snapshot data
            ticker = self.ib.reqMktData(contract, snapshot=True)
            
            # Wait longer for data with better checking
            max_attempts = 15  # Increased from 5
            for i in range(max_attempts):
                # Check for valid data
                if ticker.last and str(ticker.last) != 'nan' and ticker.last > 0:
                    # Cancel the market data request to free resources
                    self.ib.cancelMktData(contract)
                    
                    result = {
                        'symbol': symbol,
                        'last': ticker.last,
                        'bid': ticker.bid if ticker.bid and str(ticker.bid) != 'nan' else ticker.last,
                        'ask': ticker.ask if ticker.ask and str(ticker.ask) != 'nan' else ticker.last,
                        'volume': ticker.volume if ticker.volume else 0,
                        'close': ticker.close if ticker.close and str(ticker.close) != 'nan' else ticker.last
                    }
                    
                    self.logger.info(f"Got market data for {symbol}: ${result['last']:.2f}")
                    return result
                    
                # Also check if we have bid/ask but no last (can happen with delayed data)
                elif ticker.bid and ticker.ask and str(ticker.bid) != 'nan' and str(ticker.ask) != 'nan':
                    # Use mid price as last
                    mid_price = (ticker.bid + ticker.ask) / 2
                    self.ib.cancelMktData(contract)
                    
                    result = {
                        'symbol': symbol,
                        'last': mid_price,
                        'bid': ticker.bid,
                        'ask': ticker.ask,
                        'volume': ticker.volume if ticker.volume else 0,
                        'close': ticker.close if ticker.close and str(ticker.close) != 'nan' else mid_price
                    }
                    
                    self.logger.info(f"Got market data for {symbol} (using mid): ${result['last']:.2f}")
                    return result
                    
                # Only sleep if we don't have data yet
                self.ib.sleep(1)
                
                # Log progress every 5 attempts
                if (i + 1) % 5 == 0:
                    self.logger.debug(f"Still waiting for {symbol} data... attempt {i+1}/{max_attempts}")
            
            # Cancel the request if no data received
            self.ib.cancelMktData(contract)
            
            # If no data, return None instead of trying historical
            self.logger.warning(f"No data for {symbol} after {max_attempts} attempts")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting {symbol}: {e}")
            return None
            
    def get_historical_data(self, symbol: str, duration: str = '60 D', 
                          bar_size: str = '1 day') -> Any:
        """Synchronously get historical data"""
        if not self.ib or not self.ib.isConnected():
            return []
            
        from ib_insync import Stock
        
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True
            )
            
            return bars
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
            
    def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict]:
        """Synchronously get options chain"""
        if not self.ib or not self.ib.isConnected():
            return []
            
        from ib_insync import Stock, Option
        
        try:
            # Get the underlying
            stock = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(stock)
            
            # Get option chain
            chains = self.ib.reqSecDefOptParams(
                stock.symbol,
                stock.exchange,
                stock.secType,
                stock.conId
            )
            
            if not chains:
                return []
                
            # Get specific expiry or nearest
            chain = chains[0]
            if expiry:
                if expiry not in chain.expirations:
                    expiry = min(chain.expirations, 
                               key=lambda x: abs(int(x) - int(expiry)))
            else:
                expiry = chain.expirations[0]
                
            # Get strikes near current price
            ticker = self.ib.reqMktData(stock)
            self.ib.sleep(1)
            current_price = ticker.last or ticker.close or 100
            
            strikes = [s for s in chain.strikes 
                      if 0.8 * current_price <= s <= 1.2 * current_price][:10]
            
            options = []
            for strike in strikes:
                for right in ['C', 'P']:
                    opt = Option(symbol, expiry, strike, right, 'SMART')
                    self.ib.qualifyContracts(opt)
                    
                    opt_ticker = self.ib.reqMktData(opt)
                    self.ib.sleep(0.1)
                    
                    options.append({
                        'symbol': symbol,
                        'expiry': expiry,
                        'strike': strike,
                        'type': 'call' if right == 'C' else 'put',
                        'bid': opt_ticker.bid or 0,
                        'ask': opt_ticker.ask or 0,
                        'last': opt_ticker.last or 0,
                        'contract': opt
                    })
                    
                    self.ib.cancelMktData(opt)
                    
            self.ib.cancelMktData(stock)
            return options
            
        except Exception as e:
            self.logger.error(f"Error getting options chain for {symbol}: {e}")
            return []
            
    def place_order(self, contract, order) -> Optional[str]:
        """Synchronously place an order"""
        if not self.ib or not self.ib.isConnected():
            return None
            
        try:
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(1)  # Wait for order to be acknowledged
            
            if trade.order.orderId:
                return str(trade.order.orderId)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
            
    def get_positions(self) -> List:
        """Synchronously get positions"""
        if not self.ib or not self.ib.isConnected():
            return []
            
        return self.ib.positions()
        
    def get_account_summary(self) -> Dict:
        """Synchronously get account summary"""
        if not self.ib or not self.ib.isConnected():
            return {}
            
        summary = {}
        for av in self.ib.accountValues():
            if av.currency == 'USD':
                summary[av.tag] = float(av.value)
                
        return summary
        
    @property
    def connected(self) -> bool:
        """Check if connected"""
        return self.ib and self.ib.isConnected()
        
    # Add compatibility methods for existing code
    def reqContractDetails(self, contract):
        """Compatibility wrapper"""
        if not self.ib:
            return []
        return self.ib.reqContractDetails(contract)
    
    async def reqMktData(self, contract):
        """Async compatibility wrapper for market data"""
        return self.get_market_data(contract.symbol)
    
    async def reqHistoricalData(self, contract, *args, **kwargs):
        """Async compatibility wrapper for historical data"""
        duration = kwargs.get('duration', '2 D')
        bar_size = kwargs.get('bar_size', '1 hour')
        return self.get_historical_data(contract.symbol, duration, bar_size)
    
    async def reqNewsArticle(self, contract):
        """Async compatibility wrapper for news - returns empty for now"""
        return []
    
    def is_trading_halted(self, symbol: str) -> bool:
        """Check if trading is halted - simplified version"""
        market_data = self.get_market_data(symbol)
        if not market_data:
            return True
        return market_data.get('bid', 0) == 0 and market_data.get('ask', 0) == 0


def create_sync_ibkr_client(host='127.0.0.1', port=4001, client_id=1):
    """
    Factory function to create a synchronous IBKR client
    
    This version uses ib_insync's built-in sync methods instead of
    wrapping async calls, which is more stable.
    
    Usage:
        client = create_sync_ibkr_client()
        client.connect()
        value = client.get_account_value()
        data = client.get_market_data('AAPL')
        client.disconnect()
    """
    return IBKRSyncWrapper(host, port, client_id) 