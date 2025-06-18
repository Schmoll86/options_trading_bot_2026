# ibkr_client_2026/client.py
import asyncio
from ib_insync import IB, Contract, Order, Stock, Option, util, MarketOrder, LimitOrder
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import pandas as pd

class IBKRClient2026:
    """
    Client for interacting with Interactive Brokers API.
    Properly uses ib_insync async methods.
    """
    def __init__(self, host='127.0.0.1', port=4001, client_id=1):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.logger = logging.getLogger(__name__)
        self.market_data_cache = {}
        self.connected = False
        self._tickers = {}  # Store active ticker subscriptions

    async def connect(self):
        """Connect to the IBKR Gateway."""
        if self.connected:
            return
        try:
            # For ib_insync, we need to ensure it's connected properly
            await self.ib.connectAsync(self.host, self.port, self.client_id)
            self.connected = True
            self.logger.info(f"Connected to IBKR Gateway at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to IBKR Gateway: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the IBKR Gateway."""
        if self.connected:
            # Cancel all market data subscriptions
            for ticker in self._tickers.values():
                self.ib.cancelMktData(ticker)
            self._tickers.clear()
            
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from IBKR")

    async def is_connected(self) -> bool:
        """Check if connected to IBKR."""
        return self.connected and self.ib.isConnected()

    async def get_account_value(self, tag='NetLiquidation') -> float:
        """Get account value for a specific tag."""
        try:
            # Request account summary
            self.ib.reqAccountSummary()
            await asyncio.sleep(1)  # Wait for data
            
            account_values = self.ib.accountSummary()
            
            for value in account_values:
                if value.tag == tag:
                    return float(value.value)
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting account value: {e}")
            return 0.0

    async def get_positions(self):
        """Get current positions."""
        try:
            positions = await self.ib.reqPositionsAsync()
            return positions
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    async def get_market_data(self, symbol: str, sec_type: str = 'STK') -> Optional[Dict]:
        """Get current market data for a symbol."""
        try:
            # Create contract based on security type
            if sec_type == 'IND' or symbol == 'VIX':
                from ib_insync import Index
                contract = Index(symbol, 'CBOE' if symbol == 'VIX' else 'SMART')
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Check if we already have a ticker for this symbol
            if symbol in self._tickers:
                ticker = self._tickers[symbol]
            else:
                # Request market data
                ticker = self.ib.reqMktData(contract, '', False, False)
                self._tickers[symbol] = ticker
                # Wait a bit for data to come in
                await asyncio.sleep(2)
            
            # Return market data
            if ticker.last and ticker.last > 0:
                return {
                    'symbol': symbol,
                    'last': float(ticker.last) if ticker.last else None,
                    'bid': float(ticker.bid) if ticker.bid and ticker.bid > 0 else None,
                    'ask': float(ticker.ask) if ticker.ask and ticker.ask > 0 else None,
                    'volume': int(ticker.volume) if ticker.volume else 0,
                    'high': float(ticker.high) if ticker.high else None,
                    'low': float(ticker.low) if ticker.low else None,
                    'close': float(ticker.close) if ticker.close else None
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol: str, duration: str = '2 D', 
                                bar_size: str = '1 hour', what_to_show: str = 'TRADES') -> Optional[pd.DataFrame]:
        """Get historical data for a symbol."""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request historical data
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,
                formatDate=1
            )
            
            if bars:
                # Convert to pandas DataFrame
                df = util.df(bars)
                return df
            return None
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None

    async def get_options_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict]:
        """Get options chain for a symbol."""
        try:
            # Get the underlying contract
            underlying = Stock(symbol, 'SMART', 'USD')
            
            # Request contract details to get available expiries
            chains = await self.ib.reqSecDefOptParamsAsync(
                underlying.symbol,
                '',
                underlying.secType,
                underlying.conId
            )
            
            if not chains:
                return []
            
            chain = chains[0]
            
            # If no expiry specified, use the nearest one
            if not expiry:
                expiries = sorted(chain.expirations)
                if expiries:
                    expiry = expiries[0]
            
            # Get strikes for the expiry
            strikes = chain.strikes
            
            options_data = []
            
            # Get data for a subset of strikes around ATM
            underlying_price = await self._get_underlying_price(symbol)
            if not underlying_price:
                return []
            
            # Filter strikes to reasonable range (e.g., +/- 20% of underlying)
            min_strike = underlying_price * 0.8
            max_strike = underlying_price * 1.2
            filtered_strikes = [s for s in strikes if min_strike <= s <= max_strike]
            
            # Limit to avoid too many requests
            filtered_strikes = filtered_strikes[::2][:10]  # Every other strike, max 10
            
            for strike in filtered_strikes:
                try:
                    # Create call and put contracts
                    call = Option(symbol, expiry, strike, 'C', 'SMART')
                    put = Option(symbol, expiry, strike, 'P', 'SMART')
                    
                    # Get market data for both
                    call_ticker = self.ib.reqMktData(call, '', False, False)
                    put_ticker = self.ib.reqMktData(put, '', False, False)
                    
                    await asyncio.sleep(1)  # Wait for data
                    
                    option_data = {
                        'strike': strike,
                        'expiry': expiry,
                        'call': {
                            'bid': float(call_ticker.bid) if call_ticker.bid and call_ticker.bid > 0 else None,
                            'ask': float(call_ticker.ask) if call_ticker.ask and call_ticker.ask > 0 else None,
                            'last': float(call_ticker.last) if call_ticker.last else None,
                            'volume': int(call_ticker.volume) if call_ticker.volume else 0
                        },
                        'put': {
                            'bid': float(put_ticker.bid) if put_ticker.bid and put_ticker.bid > 0 else None,
                            'ask': float(put_ticker.ask) if put_ticker.ask and put_ticker.ask > 0 else None,
                            'last': float(put_ticker.last) if put_ticker.last else None,
                            'volume': int(put_ticker.volume) if put_ticker.volume else 0
                        }
                    }
                    
                    options_data.append(option_data)
                    
                    # Cancel market data to avoid hitting limits
                    self.ib.cancelMktData(call_ticker)
                    self.ib.cancelMktData(put_ticker)
                    
                except Exception as e:
                    self.logger.error(f"Error getting option data for strike {strike}: {e}")
                    continue
            
            return options_data
            
        except Exception as e:
            self.logger.error(f"Error getting options chain for {symbol}: {e}")
            return []

    async def _get_underlying_price(self, symbol: str) -> Optional[float]:
        """Helper to get current price of underlying."""
        market_data = await self.get_market_data(symbol)
        if market_data and market_data.get('last'):
            return market_data['last']
        return None

    async def place_order(self, contract: Contract, order: Order) -> Optional[str]:
        """Place an order."""
        try:
            trade = self.ib.placeOrder(contract, order)
            # Wait a bit for order to be acknowledged
            await asyncio.sleep(1)
            
            if trade.order.orderId:
                self.logger.info(f"Order placed: {trade.order.orderId} for {contract.symbol}")
                return str(trade.order.orderId)
            return None
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    async def get_order_status(self, order_id: str):
        """Get status of an order."""
        try:
            trades = self.ib.trades()
            for trade in trades:
                if str(trade.order.orderId) == order_id:
                    return {
                        'status': trade.orderStatus.status,
                        'filled': trade.orderStatus.filled,
                        'remaining': trade.orderStatus.remaining,
                        'avgFillPrice': trade.orderStatus.avgFillPrice
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            trades = self.ib.trades()
            for trade in trades:
                if str(trade.order.orderId) == order_id:
                    self.ib.cancelOrder(trade.order)
                    self.logger.info(f"Order {order_id} cancelled")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False

    async def get_account_summary(self) -> Dict:
        """Get comprehensive account summary."""
        try:
            self.ib.reqAccountSummary()
            await asyncio.sleep(1)  # Wait for data
            
            summary = self.ib.accountSummary()
            
            result = {}
            for item in summary:
                result[item.tag] = float(item.value) if item.tag in [
                    'NetLiquidation', 'TotalCashValue', 'BuyingPower',
                    'GrossPositionValue', 'MaintMarginReq', 'AvailableFunds',
                    'UnrealizedPnL', 'RealizedPnL', 'ExcessLiquidity'
                ] else item.value
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting account summary: {e}")
            return {}

    async def is_trading_halted(self, symbol: str) -> bool:
        """Check if trading is halted for a symbol."""
        try:
            # Get market data to check trading status
            market_data = await self.get_market_data(symbol)
            
            if not market_data:
                # If we can't get market data, assume halted
                return True
            
            # Check if we have valid bid/ask prices
            bid = market_data.get('bid')
            ask = market_data.get('ask')
            last = market_data.get('last')
            
            # If bid and ask are both None or 0, likely halted
            if (not bid or bid == 0) and (not ask or ask == 0):
                return True
            
            # If last price exists but no bid/ask, might be halted
            if last and last > 0 and (not bid or not ask):
                # Could be after-hours or halted
                contract = Stock(symbol, 'SMART', 'USD')
                details = await self.reqContractDetails(contract)
                if details:
                    # Check trading hours if available
                    # For now, assume not halted if we have contract details
                    return False
                return True
            
            # If we have valid bid/ask, not halted
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if {symbol} is halted: {e}")
            # On error, assume not halted to avoid blocking trades
            return False

    # Compatibility methods for existing code
    async def reqMktData(self, contract: Contract):
        """Compatibility wrapper for market data requests."""
        if isinstance(contract, Stock):
            symbol = contract.symbol
        else:
            symbol = f"{contract.symbol}_{contract.secType}"
        
        data = await self.get_market_data(contract.symbol)
        
        # Create a mock ticker object with the expected attributes
        class MockTicker:
            def __init__(self, data):
                self.last = data.get('last') if data else None
                self.bid = data.get('bid') if data else None
                self.ask = data.get('ask') if data else None
                self.volume = data.get('volume') if data else None
                self.high = data.get('high') if data else None
                self.low = data.get('low') if data else None
        
        return MockTicker(data)

    async def reqHistoricalData(self, contract: Contract, *args, **kwargs):
        """Compatibility wrapper for historical data requests."""
        return await self.get_historical_data(contract.symbol)

    async def reqContractDetails(self, contract: Contract):
        """Get contract details."""
        try:
            details = await self.ib.reqContractDetailsAsync(contract)
            return details
        except Exception as e:
            self.logger.error(f"Error getting contract details: {e}")
            return []

    async def reqNewsArticle(self, symbol: str):
        """Retrieve recent news articles for *symbol* via IBKR Historical News API.

        Returns a list of `ib_insync.objects.NewsArticle`.  Requires that your
        account has the *News* subscription enabled in TWS / Gateway.
        """
        try:
            # 1) Retrieve available news providers once and cache them
            if not hasattr(self, '_news_providers_cache'):
                providers = await self.ib.reqNewsProvidersAsync()
                self._news_providers_cache = providers or []

            if not self._news_providers_cache:
                self.logger.warning("No news providers returned; is the News subscription enabled?")
                return []

            # Prefer real-time breaking news provider (e.g., 'BRFG') or the first provider
            provider_code = None
            for p in self._news_providers_cache:
                if p.code.upper().startswith('BRF'):
                    provider_code = p.code
                    break
            if provider_code is None:
                provider_code = self._news_providers_cache[0].code

            # 2) Qualify contract to obtain conId
            contract_details = await self.reqContractDetails(Stock(symbol, 'SMART', 'USD'))
            if not contract_details:
                self.logger.warning(f"Cannot qualify contract for {symbol}; skipping news fetch")
                return []
            con_id = contract_details[0].contract.conId

            # 3) Fetch historical news headlines (latest 10)
            headlines = await self.ib.reqHistoricalNewsAsync(
                conId=con_id,
                providerCodes=provider_code,
                startDateTime='',   # empty string = now
                endDateTime='',
                totalResults=10,
                useTimeZone=False
            )

            if not headlines:
                return []

            # 4) For each headline, request full article text (optional)
            articles = []
            for h in headlines:
                try:
                    article = await self.ib.reqNewsArticleAsync(h.providerCode, h.articleId)
                    articles.append(article)
                except Exception as inner_exc:
                    self.logger.debug(f"Unable to fetch article {h.articleId}: {inner_exc}")
                    continue

            return articles

        except Exception as e:
            self.logger.error(f"Error fetching news for {symbol}: {e}")
            return []
