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
            # VIX removed - it's an index, not a stock
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
        """Get news articles with rate limiting"""
        if not await self._rate_limit_check(contract.symbol):
            return []
        
        try:
            # Request news - IBKR API doesn't support these parameters in our implementation
            news = await self.ibkr_client.reqNewsArticle(contract.symbol)
            await asyncio.sleep(0.1)  # Small delay between requests
            return news
        except Exception as e:
            self.logger.error(f"Error requesting news article: {e}")
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
        if (self.last_update and datetime.now() - self.last_update < self.update_interval):
            return
        try:
            for symbol in self.market_indexes:
                contract = Contract(symbol=symbol, secType='STK', exchange='SMART', currency='USD')
                ticker = await self.ibkr_client.reqMktData(contract)
                await asyncio.sleep(0.1)
                news = await self._get_news_with_rate_limit(contract)
                self.news_cache[symbol] = {
                    'ticker': ticker,
                    'news': news,
                    'last_update': datetime.now()
                }
            self.last_update = datetime.now()
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")

    async def _analyze_market_sentiment(self) -> Dict:
        try:
            spy_data = self.news_cache.get('SPY', {})
            if not spy_data:
                return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.5}
            ticker = spy_data['ticker']
            price_change = (ticker.last - ticker.close) / ticker.close if ticker.last and ticker.close else 0
            news_sentiment = self._analyze_news_sentiment(spy_data['news'])
            sentiment_score = (price_change * 0.6 + news_sentiment * 0.4)
            if sentiment_score > 0.2:
                sentiment = 'bullish'
            elif sentiment_score < -0.2:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            confidence = 0.7 if ticker.last and ticker.close else 0.5
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': confidence
            }
        except Exception as e:
            self.logger.error(f"Error analyzing market sentiment: {e}")
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.5}

    async def _analyze_sector_sentiment(self) -> Dict:
        sectors = {
            'technology': ['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
            'healthcare': ['JNJ', 'PFE', 'UNH', 'MRK'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB'],
            'financials': ['JPM', 'BAC', 'GS', 'MS']
        }
        sector_sentiment = {}
        for sector, symbols in sectors.items():
            try:
                sector_scores = []
                for symbol in symbols:
                    contract = Contract(symbol=symbol, secType='STK', exchange='SMART', currency='USD')
                    news = await self._get_news_with_rate_limit(contract)
                    score = self._analyze_news_sentiment(news)
                    sector_scores.append(score)
                if sector_scores:
                    sector_sentiment[sector] = sum(sector_scores) / len(sector_scores)
                else:
                    sector_sentiment[sector] = 0.0
            except Exception as e:
                self.logger.error(f"Error analyzing {sector} sector sentiment: {e}")
                sector_sentiment[sector] = 0.0
        return sector_sentiment

    async def _get_technical_sentiment(self) -> Dict:
        try:
            # VIX is an index, not a tradeable stock, so we'll use a default value
            # In production, you would get VIX data from a different source
            vix_level = 20.0  # Default VIX level
            
            spy_data = self.news_cache.get('SPY', {})
            if spy_data and spy_data['ticker'].last and spy_data['ticker'].close:
                momentum = (spy_data['ticker'].last - spy_data['ticker'].close) / spy_data['ticker'].close
            else:
                momentum = 0.0
            bull_bear_ratio = await self._calculate_bull_bear_ratio()
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
        try:
            earnings_season = await self._check_earnings_season()
            fed_announcement = await self._check_fed_announcement()
            geopolitical_risk = await self._get_geopolitical_risk()
            market_events = await self._get_market_events()
            return {
                'earnings_season': earnings_season,
                'fed_announcement': fed_announcement,
                'geopolitical_risk': geopolitical_risk,
                'market_events': market_events
            }
        except Exception as e:
            self.logger.error(f"Error getting news factors: {e}")
            return {
                'earnings_season': False,
                'fed_announcement': False,
                'geopolitical_risk': 0.0,
                'market_events': []
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
        return False

    async def _get_geopolitical_risk(self) -> float:
        return 0.0

    async def _get_market_events(self) -> List[str]:
        return []

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
                'financials': 0.0
            },
            'news_factors': {
                'earnings_season': False,
                'fed_announcement': False,
                'geopolitical_risk': 0.0,
                'market_events': []
            },
            'technical_sentiment': {
                'vix_level': 20.0,
                'bull_bear_ratio': 0.5,
                'market_momentum': 0.0
            },
            'timestamp': datetime.now().isoformat(),
            'data_sources': ['default']
        }
