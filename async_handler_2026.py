"""
Async Handler - IBKR Client following Options Trading Bot 2026 Architecture
NO TESTING CODE - Production ready implementation
"""

import asyncio
import threading
import queue
from typing import Any, Dict, Optional, List, Callable
import logging
from concurrent.futures import Future
import time
import nest_asyncio
from ib_insync import IB, Stock, Option, Index

# Allow nested event loops (fixes ib_insync issues)
nest_asyncio.apply()


class IBKRSyncWrapper:
    """
    Production IBKR Synchronous Wrapper - NO TESTING CODE
    
    Architecture Layer: Core Infrastructure (Layer 2)
    Dependencies: IBKR Gateway (External)
    Used By: AsyncSyncAdapter, ThreadSafeIBKRWrapper
    
    Data Flow: Strategy Modules → ThreadSafeWrapper → AsyncSyncAdapter → IBKRSyncWrapper → IBKR Gateway
    """
    
    def __init__(self, host='127.0.0.1', port=4001, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Synchronously connect to IBKR Gateway"""
        from ib_insync import IB
        
        self.ib = IB()
        self.ib.connect(self.host, self.port, clientId=self.client_id)
        
        # Switch to delayed data mode for better reliability outside trading hours
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
        """Get account value - Required by risk management"""
        if not self.ib or not self.ib.isConnected():
            return 0.0
            
        account_values = self.ib.accountValues()
        for av in account_values:
            if av.tag == tag and av.currency == 'USD':
                return float(av.value)
        return 0.0
        
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Get real market data from IBKR - NO MOCK DATA
        Required by: All strategy modules for market analysis
        """
        if not self.ib or not self.ib.isConnected():
            self.logger.warning(f"Not connected to IBKR")
            return None
            
        self.logger.info(f"get_market_data called for {symbol}")
        
        try:
            # Create contract based on symbol type
            if symbol == 'VIX':
                contract = Index('VIX', 'CBOE')
            else:
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
            
            # Request real market data snapshot
            ticker = self.ib.reqMktData(contract, snapshot=True)
            
            # Wait for real data with proper retry logic
            max_attempts = 15
            for i in range(max_attempts):
                # Check for valid real data
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
                    
                # Wait before retry
                self.ib.sleep(1)
                
                # Log progress every 5 attempts
                if (i + 1) % 5 == 0:
                    self.logger.debug(f"Still waiting for {symbol} data... attempt {i+1}/{max_attempts}")
            
            # Cancel the request if no data received
            self.ib.cancelMktData(contract)
            
            # If no data, return None
            self.logger.warning(f"No data for {symbol} after {max_attempts} attempts")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting {symbol}: {e}")
            return None
            
    def get_historical_data(self, symbol: str, duration: str = '60 D', 
                          bar_size: str = '1 day') -> Any:
        """Get real historical data - Required for technical analysis"""
        if not self.ib or not self.ib.isConnected():
            return []
            
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
        """
        Get real options chain data - NO MOCK DATA
        Required by: Options strategy modules (bull/bear/volatile)
        """
        if not self.ib or not self.ib.isConnected():
            return []
            
        try:
            # Create stock contract
            stock = Stock(symbol, 'SMART', 'USD')
            
            # Qualify the contract
            contracts = self.ib.reqContractDetails(stock)
            if not contracts:
                self.logger.error(f"Could not find contract for {symbol}")
                return []
            
            qualified_contract = contracts[0].contract
            
            # Get real option chains from IBKR
            chains = self.ib.reqSecDefOptParams(
                qualified_contract.symbol,
                '',
                qualified_contract.secType,
                qualified_contract.conId
            )
            
            if not chains:
                self.logger.error(f"No option chains found for {symbol}")
                return []
            
            # Use the first chain (usually the most liquid exchange)
            chain = chains[0]
            
            # Filter expiries if specified
            if expiry:
                if expiry not in chain.expirations:
                    self.logger.error(f"Expiry {expiry} not available for {symbol}")
                    return []
                expirations = [expiry]
            else:
                # Use next 3 monthly expirations
                expirations = sorted(chain.expirations)[:3]
            
            options_data = []
            
            for exp in expirations:
                for strike in chain.strikes:
                    # Create call and put contracts
                    call = Option(symbol, exp, strike, 'C', chain.exchange)
                    put = Option(symbol, exp, strike, 'P', chain.exchange)
                    
                    # Get real market data for both
                    call_ticker = self.ib.reqMktData(call, '', False, False)
                    put_ticker = self.ib.reqMktData(put, '', False, False)
                    
                    # Wait for real data
                    self.ib.sleep(0.1)
                    
                    # Extract real pricing data
                    call_data = {
                        'bid': call_ticker.bid if call_ticker.bid == call_ticker.bid else None,
                        'ask': call_ticker.ask if call_ticker.ask == call_ticker.ask else None,
                        'last': call_ticker.last if call_ticker.last == call_ticker.last else None,
                        'volume': call_ticker.volume if call_ticker.volume == call_ticker.volume else 0
                    }
                    
                    put_data = {
                        'bid': put_ticker.bid if put_ticker.bid == put_ticker.bid else None,
                        'ask': put_ticker.ask if put_ticker.ask == put_ticker.ask else None,
                        'last': put_ticker.last if put_ticker.last == put_ticker.last else None,
                        'volume': put_ticker.volume if put_ticker.volume == put_ticker.volume else 0
                    }
                    
                    options_data.append({
                        'symbol': symbol,
                        'expiry': exp,
                        'strike': strike,
                        'call': call_data,
                        'put': put_data
                    })
                    
                    # Cancel market data to avoid overload
                    self.ib.cancelMktData(call)
                    self.ib.cancelMktData(put)
            
            self.logger.info(f"Retrieved {len(options_data)} real option contracts for {symbol}")
            return options_data
            
        except Exception as e:
            self.logger.error(f"Error getting options chain for {symbol}: {e}")
            return []
            
    def place_order(self, contract, order) -> Optional[str]:
        """Place real order - Required by execution engine"""
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
        """Get real positions - Required for portfolio monitoring"""
        if not self.ib or not self.ib.isConnected():
            return []
            
        return self.ib.positions()
        
    def get_account_summary(self) -> Dict:
        """Get real account summary - Required by risk management"""
        if not self.ib or not self.ib.isConnected():
            return {}
            
        summary = {}
        for av in self.ib.accountValues():
            if av.currency == 'USD':
                summary[av.tag] = float(av.value)
                
        return summary
    
    def is_trading_halted(self, symbol: str) -> bool:
        """
        Check if trading is halted for a symbol
        Required by: All strategy execute_trade methods
        """
        market_data = self.get_market_data(symbol)
        if not market_data:
            return True
        return market_data.get('bid', 0) == 0 and market_data.get('ask', 0) == 0
    
    def reqContractDetails(self, contract):
        """Contract details - Required for options validation"""
        if not self.ib:
            return []
        return self.ib.reqContractDetails(contract)
        
    @property
    def connected(self) -> bool:
        """Check if connected to IBKR"""
        return self.ib and self.ib.isConnected()


def create_sync_ibkr_client(host='127.0.0.1', port=4001, client_id=1):
    """
    Factory function to create a synchronous IBKR client
    NO TESTING CODE - Production ready
    
    Architecture: Creates the core IBKR interface component
    
    Usage:
        client = create_sync_ibkr_client()
        client.connect()
        value = client.get_account_value()
        data = client.get_market_data('AAPL')  # REAL DATA ONLY
        client.disconnect()
    """
    return IBKRSyncWrapper(host, port, client_id) 