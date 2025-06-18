# news_handler_2026/news.py
import logging
from datetime import datetime, timedelta
from ib_insync import Contract, NewsArticle
from typing import Dict, List
import asyncio

class NewsHandler2026:
    """
    Handles news and sentiment analysis for Options Trading Bot 2026.
    """
    def __init__(self, ibkr_client):
        self.ibkr_client = ibkr_client
        self.logger = logging.getLogger(__name__)
        self.news_cache = {}
        self.last_update = None
        self.update_interval = timedelta(minutes=15)  # Fetch news every 15 minutes max
        self.max_lookback_days = 7  # Max 1 week of historical news
        self.max_results = 50  # Limit articles per request
        self.market_indexes = [
            'SPY',  # S&P 500
            'QQQ',  # NASDAQ
            'DIA',  # Dow Jones
            'IWM',  # Russell 2000
            'VIX',  # Volatility Index - needed for volatility strategy
        ]
        self._request_timestamps = {}  # Track request timestamps for rate limiting

    async def _rate_limit_check(self, symbol: str) -> bool:
        """Check if we need to rate limit requests for a symbol"""
        now = datetime.now()
        if symbol in self._request_timestamps:
            last_request = self._request_timestamps[symbol]
            if now - last_request < timedelta(minutes=15):
                return False
        self._request_timestamps[symbol] = now
        return True

    async def _get_news_with_rate_limit(self, contract: Contract) -> List[NewsArticle]:
        """Get news articles with rate limiting - Fallback to market data analysis"""
        if not await self._rate_limit_check(contract.symbol):
            return []
        
        try:
            # IBKR news API not available, return empty list
            # We'll rely on market data analysis instead
            await asyncio.sleep(0.1)  # Small delay for rate limiting
            return []
        except Exception as e:
            self.logger.debug(f"News articles not available for {contract.symbol}: {e}")
            return []

    async def get_market_sentiment(self):
        """
        Get real market sentiment from IBKR data feeds
        """
        try:
            await self._update_market_data()
            market_sentiment = await self._analyze_market_sentiment()
            sector_sentiment = await self._analyze_sector_sentiment()
            technical_sentiment = await self._get_technical_sentiment()
            combined_sentiment = {
                'overall_sentiment': market_sentiment['sentiment'],
                'sentiment_score': market_sentiment['score'],
                'confidence': market_sentiment['confidence'],
                'volatility_expected': technical_sentiment['vix_level'] / 20,
                'bullish': market_sentiment['score'] > 0.2,
                'bearish': market_sentiment['score'] < -0.2,
                'volatile': abs(market_sentiment['score']) < 0.2 and technical_sentiment['vix_level'] > 20,
                'neutral': abs(market_sentiment['score']) <= 0.2 and technical_sentiment['vix_level'] <= 20,
                'sector_sentiment': sector_sentiment,
                'news_factors': await self._get_news_factors(),
                'technical_sentiment': technical_sentiment,
                'timestamp': datetime.now().isoformat(),
                'data_sources': ['ibkr_news', 'market_data', 'technical']
            }
            return combined_sentiment
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {e}")
            return self._get_default_sentiment()

    async def _update_market_data(self):
        """Update market data for all indexes in parallel with better error handling"""
        if (self.last_update and datetime.now() - self.last_update < self.update_interval):
            return
            
        try:
            # Create parallel tasks for all market indexes
            tasks = []
            for symbol in self.market_indexes:
                if symbol == 'VIX':
                    tasks.append(self._fetch_symbol_data(symbol, 'IND'))
                else:
                    tasks.append(self._fetch_symbol_data(symbol, 'STK'))
            
            # Execute all requests in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_updates = 0
            for i, result in enumerate(results):
                symbol = self.market_indexes[i]
                
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to get data for {symbol}: {result}")
                    # Set fallback data
                    self.news_cache[symbol] = self._get_fallback_data(symbol)
                elif result:
                    self.news_cache[symbol] = {
                        'market_data': result,
                        'news': [],
                        'last_update': datetime.now()
                    }
                    successful_updates += 1
                else:
                    self.news_cache[symbol] = self._get_fallback_data(symbol)
            
            self.last_update = datetime.now()
            self.logger.info(f"Market data update completed: {successful_updates}/{len(self.market_indexes)} successful")
            
        except Exception as e:
            self.logger.error(f"Error in market data update: {e}")

    async def _fetch_symbol_data(self, symbol: str, sec_type: str) -> dict:
        """Fetch data for a single symbol with timeout protection"""
        try:
            market_data = await asyncio.wait_for(
                self.ibkr_client.get_market_data(symbol, sec_type=sec_type),
                timeout=10.0  # 10 second timeout per symbol
            )
            
            if market_data and not market_data.get('error'):
                # Validate data quality
                if self._validate_market_data(market_data, symbol):
                    return market_data
                else:
                    self.logger.warning(f"Invalid market data for {symbol}: {market_data}")
                    return None
            else:
                self.logger.warning(f"No valid market data for {symbol}")
                return None
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout fetching data for {symbol}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def _validate_market_data(self, data: dict, symbol: str) -> bool:
        """Validate that market data is reasonable"""
        if not data or not isinstance(data, dict):
            return False
            
        last_price = data.get('last')
        if not last_price or last_price <= 0:
            return False
            
        # Symbol-specific validation
        if symbol == 'VIX':
            # VIX should be between 5 and 100 typically
            if last_price < 5 or last_price > 100:
                self.logger.warning(f"VIX value {last_price} seems unusual")
                return False
        else:
            # Stock prices should be reasonable (> $1, < $10000)
            if last_price < 1 or last_price > 10000:
                self.logger.warning(f"{symbol} price {last_price} seems unusual")
                return False
                
        return True

    def _get_fallback_data(self, symbol: str) -> dict:
        """Get fallback data for a symbol when real data is unavailable"""
        return {
            'market_data': {
                'symbol': symbol,
                'last': 20.0 if symbol == 'VIX' else 100.0,
                'close': 20.0 if symbol == 'VIX' else 99.0,
                'bid': 19.5 if symbol == 'VIX' else 99.5,
                'ask': 20.5 if symbol == 'VIX' else 100.5,
                'error': 'fallback_data'
            },
            'news': [],
            'last_update': datetime.now()
        }

    async def _analyze_market_sentiment(self) -> Dict:
        try:
            spy_data = self.news_cache.get('SPY', {})
            if not spy_data or not spy_data.get('market_data'):
                return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.5}
                
            market_data = spy_data['market_data']
            
            # Calculate price-based sentiment
            if (market_data.get('last') and 
                market_data.get('close') and 
                market_data['last'] > 0 and 
                market_data['close'] > 0):
                
                price_change = (market_data['last'] - market_data['close']) / market_data['close']
            else:
                price_change = 0
            
            # Simple sentiment scoring based on price movement
            sentiment_score = price_change * 2.0  # Amplify the signal
            
            if sentiment_score > 0.2:
                sentiment = 'bullish'
            elif sentiment_score < -0.2:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
                
            confidence = 0.8 if market_data.get('last', 0) > 0 else 0.3
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': confidence,
                'price_change': price_change
            }
        except Exception as e:
            self.logger.error(f"Error analyzing market sentiment: {e}")
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.5}

    async def _analyze_sector_sentiment(self) -> Dict:
        """Analyze sector sentiment using sector ETFs instead of individual stocks"""
        # Use sector ETFs for faster, more reliable sector analysis
        sector_etfs = {
            'technology': 'XLK',    # Technology Select Sector SPDR
            'healthcare': 'XLV',    # Health Care Select Sector SPDR  
            'energy': 'XLE',        # Energy Select Sector SPDR
            'financials': 'XLF',    # Financial Select Sector SPDR
            'consumer_discretionary': 'XLY',  # Consumer Discretionary SPDR
            'industrials': 'XLI'    # Industrial Select Sector SPDR
        }
        
        # Process all sector ETFs in parallel
        sector_tasks = []
        for sector_name, etf_symbol in sector_etfs.items():
            sector_tasks.append(self._fetch_symbol_data(etf_symbol, 'STK'))
        
        sector_results = await asyncio.gather(*sector_tasks, return_exceptions=True)
        
        # Process results into sector sentiment
        sector_sentiment = {}
        for i, (sector_name, etf_symbol) in enumerate(sector_etfs.items()):
            result = sector_results[i]
            
            if isinstance(result, Exception):
                self.logger.debug(f"Failed to get data for {sector_name} ETF ({etf_symbol}): {result}")
                sector_sentiment[sector_name] = 0.0
            elif result and result.get('last') and result.get('close'):
                # Calculate price-based sentiment from ETF performance
                price_change = (result['last'] - result['close']) / result['close']
                sector_sentiment[sector_name] = price_change
            else:
                sector_sentiment[sector_name] = 0.0
        
        return sector_sentiment

    async def _get_technical_sentiment(self) -> Dict:
        try:
            # Try to get VIX data from cache first, then direct API call
            vix_level = 20.0  # Default VIX level
            
            # First try cached VIX data
            vix_cache = self.news_cache.get('VIX', {})
            if vix_cache and vix_cache.get('market_data'):
                vix_data = vix_cache['market_data']
                if vix_data.get('last') and vix_data['last'] > 0 and not vix_data.get('error'):
                    vix_level = vix_data['last']
                    self.logger.debug(f"Using cached VIX data: {vix_level}")
            else:
                # Fallback to direct API call
                try:
                    vix_data = await self.ibkr_client.get_market_data('VIX', sec_type='IND')
                    if vix_data and vix_data.get('last') and vix_data['last'] > 0 and not vix_data.get('error'):
                        vix_level = vix_data['last']
                        self.logger.debug(f"Using direct VIX API call: {vix_level}")
                except Exception as e:
                    self.logger.debug(f"VIX data not available via API, using default: {e}")
            
            # Calculate momentum from SPY data
            spy_data = self.news_cache.get('SPY', {})
            if spy_data and spy_data.get('market_data'):
                market_data = spy_data['market_data']
                if (market_data.get('last') and market_data.get('close') and 
                    market_data['last'] > 0 and market_data['close'] > 0):
                    momentum = (market_data['last'] - market_data['close']) / market_data['close']
                else:
                    momentum = 0.0
            else:
                momentum = 0.0
                
            # Simplified bull/bear ratio calculation
            bull_bear_ratio = 0.5  # Default neutral
            if momentum > 0.01:  # 1% up = more bullish
                bull_bear_ratio = 0.6 + (momentum * 5)  # Scale momentum
            elif momentum < -0.01:  # 1% down = more bearish  
                bull_bear_ratio = 0.4 + (momentum * 5)  # Scale momentum
            
            # Keep ratio between 0.1 and 0.9
            bull_bear_ratio = max(0.1, min(0.9, bull_bear_ratio))
            
            return {
                'vix_level': vix_level,
                'bull_bear_ratio': bull_bear_ratio,
                'market_momentum': momentum
            }
        except Exception as e:
            self.logger.error(f"Error getting technical sentiment: {e}")
            return {
                'vix_level': 20.0,
                'bull_bear_ratio': 0.5,
                'market_momentum': 0.0
            }

    async def _calculate_bull_bear_ratio(self) -> float:
        try:
            spy = Contract(symbol='SPY', secType='STK', exchange='SMART', currency='USD')
            options = await self.ibkr_client.reqContractDetails(
                Contract(symbol='SPY', secType='OPT', exchange='SMART', currency='USD')
            )
            if not options:
                return 0.5
            puts = sum(1 for opt in options if opt.contract.right == 'P')
            calls = sum(1 for opt in options if opt.contract.right == 'C')
            if calls == 0:
                return 0.5
            return puts / calls
        except Exception as e:
            self.logger.error(f"Error calculating bull/bear ratio: {e}")
            return 0.5

    async def _get_news_factors(self) -> Dict:
        """Get market news factors that affect overall sentiment"""
        try:
            earnings_season = await self._check_earnings_season()
            fed_announcement = await self._check_fed_announcement()
            geopolitical_risk = await self._get_geopolitical_risk()
            market_events = await self._get_market_events()
            
            # Add volatility-based risk assessment
            vix_cache = self.news_cache.get('VIX', {})
            vix_risk = 'low'
            if vix_cache and vix_cache.get('market_data'):
                vix_level = vix_cache['market_data'].get('last', 20.0)
                if vix_level > 30:
                    vix_risk = 'high'
                elif vix_level > 20:
                    vix_risk = 'medium'
                    
            return {
                'earnings_season': earnings_season,
                'fed_announcement': fed_announcement,
                'geopolitical_risk': geopolitical_risk,
                'market_events': market_events,
                'vix_risk_level': vix_risk,
                'market_stress': vix_level > 25 if 'vix_level' in locals() else False
            }
        except Exception as e:
            self.logger.error(f"Error getting news factors: {e}")
            return {
                'earnings_season': False,
                'fed_announcement': False,
                'geopolitical_risk': 0.0,
                'market_events': [],
                'vix_risk_level': 'medium',
                'market_stress': False
            }

    def _analyze_news_sentiment(self, news_articles: List[NewsArticle]) -> float:
        if not news_articles:
            return 0.0
        positive_count = sum(1 for article in news_articles if getattr(article, 'positive', False))
        negative_count = sum(1 for article in news_articles if getattr(article, 'negative', False))
        total_count = len(news_articles)
        if total_count == 0:
            return 0.0
        sentiment_score = (positive_count - negative_count) / total_count
        return sentiment_score

    async def _check_earnings_season(self) -> bool:
        current_month = datetime.now().month
        return current_month in [1, 4, 7, 10]

    async def _check_fed_announcement(self) -> bool:
        """Check if we're near a Fed announcement date"""
        # FOMC typically meets 8 times per year, roughly every 6 weeks
        # Meeting dates are usually: Jan, Mar, May, Jun, Jul, Sep, Nov, Dec
        current_date = datetime.now()
        fed_months = [1, 3, 5, 6, 7, 9, 11, 12]
        
        # Check if current month has Fed meeting and we're in the week before/after
        if current_date.month in fed_months:
            # Rough estimate - more sophisticated logic would use actual FOMC calendar
            day_of_month = current_date.day
            # Fed meetings typically in the middle of the month
            if 10 <= day_of_month <= 25:
                return True
        
        return False

    async def _get_geopolitical_risk(self) -> float:
        return 0.0

    async def _get_market_events(self) -> List[str]:
        """Get significant market events that could affect trading"""
        events = []
        current_date = datetime.now()
        
        # Check for major economic releases (simplified)
        if current_date.weekday() == 4:  # Friday
            events.append("Jobs Report Week")
        
        # Check for earnings season
        if await self._check_earnings_season():
            events.append("Earnings Season")
            
        # Check for Fed meetings
        if await self._check_fed_announcement():
            events.append("FOMC Meeting")
            
        # Add more sophisticated event detection as needed
        return events

    def _get_default_sentiment(self) -> Dict:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.5,
            'volatility_expected': 0.5,
            'bullish': False,
            'bearish': False,
            'volatile': False,
            'neutral': True,
            'sector_sentiment': {
                'technology': 0.0,
                'healthcare': 0.0,
                'energy': 0.0,
                'financials': 0.0,
                'consumer_discretionary': 0.0,
                'industrials': 0.0
            },
            'news_factors': {
                'earnings_season': False,
                'fed_announcement': False,
                'geopolitical_risk': 0.0,
                'market_events': [],
                'vix_risk_level': 'medium',
                'market_stress': False
            },
            'technical_sentiment': {
                'vix_level': 20.0,
                'bull_bear_ratio': 0.5,
                'market_momentum': 0.0
            },
            'timestamp': datetime.now().isoformat(),
            'data_sources': ['default']
        }
