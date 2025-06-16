# stock_screener_2026/screener.py
import logging
from typing import Dict, List
import asyncio
from ib_insync import Contract, BarData, util
from datetime import datetime, timedelta
import threading

def run_async_in_thread(coro):
    """Helper function to run async code in a thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class StockScreener2026:
    def __init__(self, ibkr_client, portfolio_provider, max_stocks_per_category=10, logger=None):
        self.ibkr_client = ibkr_client
        self.portfolio_provider = portfolio_provider
        self.max_stocks = max_stocks_per_category
        self.logger = logger or logging.getLogger('screener_2026')
        self.market_data_cache = {}
        self.last_update = None
        self.update_interval = timedelta(minutes=5)
        self._dynamic_universe = None
        self._universe_last_update = None
        self._universe_update_interval = timedelta(hours=1)
        self._update_semaphore = asyncio.Semaphore(1)  # Ensure only one update at a time

    async def get_dynamic_universe(self) -> List[str]:
        """Fetch a dynamic universe of commonly traded stocks (e.g., S&P 500, NASDAQ 100, or IBKR's most active)."""
        now = datetime.now()
        if self._dynamic_universe and self._universe_last_update and (now - self._universe_last_update < self._universe_update_interval):
            return self._dynamic_universe
        try:
            # Example: Use IBKR's most active stocks (or fallback to S&P 500 from a static list or config)
            # This is a placeholder; replace with actual IBKR API call if available
            # For now, fallback to a static S&P 500 list (could be loaded from a file or config)
            # You can also use a public API or a file for S&P 500 tickers
            sp500 = await self._get_sp500_list()
            self._dynamic_universe = sp500
            self._universe_last_update = now
            return self._dynamic_universe
        except Exception as e:
            self.logger.error(f"Error fetching dynamic universe: {e}")
            # Fallback to a minimal list
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    async def _get_sp500_list(self) -> List[str]:
        # Placeholder: In production, fetch from a reliable source or config
        # Here, a static subset for demonstration
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'CRM',
            'ORCL', 'ADBE', 'PYPL', 'INTC', 'CSCO', 'JPM', 'BAC', 'WMT', 'V', 'UNH',
            'HD', 'PG', 'MA', 'DIS', 'XOM', 'CVX', 'PFE', 'KO', 'PEP', 'T', 'VZ', 'MRK', 'ABBV', 'TMO', 'COST', 'AVGO', 'MCD', 'DHR', 'ABT', 'ACN', 'LLY', 'LIN', 'WFC', 'TXN', 'NEE', 'UNP', 'MS', 'GS', 'QCOM', 'AMGN', 'LOW', 'MDT', 'RTX', 'HON', 'PM', 'IBM', 'SBUX', 'CAT', 'CVS', 'BLK', 'DE', 'GE', 'LMT', 'SPGI', 'AXP', 'ISRG', 'PLD', 'SYK', 'ZTS', 'GILD', 'TGT', 'ADP', 'MO', 'MDLZ', 'C', 'CB', 'DUK', 'MMC', 'SO', 'CI', 'PNC', 'USB', 'BDX', 'SCHW', 'ICE', 'GM', 'F', 'GM', 'BK', 'AIG', 'AON', 'AEP', 'APD', 'ADI', 'AFL', 'ALL', 'AEE', 'AAL', 'A', 'AAP', 'AA', 'AAPL' # ...
        ]

    async def screen_stocks(self, market_sentiment: Dict) -> List[str]:
        try:
            stock_universe = await self.get_dynamic_universe()
            await self._update_market_data(stock_universe)
            technical_data = await self._get_technical_indicators(stock_universe)
            sentiment_data = await self._get_sentiment_for_universe(stock_universe, market_sentiment)
            combined_data = self._merge_data(stock_universe, technical_data, sentiment_data)
            screened_results = self.screen(combined_data)
            candidate_symbols = self._extract_candidates_by_sentiment(screened_results, market_sentiment)
            self.logger.info(f"Screened {len(candidate_symbols)} candidate symbols: {candidate_symbols}")
            return candidate_symbols
        except Exception as e:
            self.logger.error(f"Error screening stocks: {e}")
            return []

    async def _update_market_data(self, stock_universe: List[str]):
        """Update market data with rate limiting and concurrency control"""
        if (self.last_update and datetime.now() - self.last_update < self.update_interval):
            return
        
        async with self._update_semaphore:  # Ensure only one update at a time
            try:
                # Create tasks for all symbols
                tasks = []
                for symbol in stock_universe:
                    tasks.append(self._update_symbol_data(symbol))
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks)
                self.last_update = datetime.now()
            except Exception as e:
                self.logger.error(f"Error updating market data: {e}")

    async def _update_symbol_data(self, symbol: str):
        """Update data for a single symbol"""
        try:
            contract = Contract(symbol=symbol, secType='STK', exchange='SMART', currency='USD')
            
            # Request market data and historical data concurrently
            ticker_task = self.ibkr_client.reqMktData(contract)
            bars_task = self.ibkr_client.reqHistoricalData(
                contract,
                duration='2 D',
                bar_size='1 hour'
            )
            
            # Wait for both requests to complete
            ticker, bars = await asyncio.gather(ticker_task, bars_task)
            
            if bars:
                self.market_data_cache[symbol] = {
                    'ticker': ticker,
                    'bars': bars,
                    'last_update': datetime.now()
                }
        except Exception as e:
            self.logger.error(f"Error updating market data for {symbol}: {e}")

    async def _get_technical_indicators(self, stock_universe: List[str]) -> Dict:
        technical_data = {}
        for symbol in stock_universe:
            data = self.market_data_cache.get(symbol)
            try:
                if not data or not data['bars']:
                    continue
                bars = data['bars']
                closes = [bar['close'] for bar in bars]
                volumes = [bar['volume'] for bar in bars]
                current_price = closes[-1]
                prev_price = closes[-2] if len(closes) > 1 else closes[-1]
                price_change = (current_price - prev_price) / prev_price if prev_price else 0
                avg_volume = sum(volumes) / len(volumes)
                current_volume = volumes[-1]
                volume_ratio = current_volume / avg_volume if avg_volume else 1
                momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0
                technical_data[symbol] = {
                    'price': current_price,
                    'price_change': price_change,
                    'volume_ratio': volume_ratio,
                    'momentum': momentum,
                    'technical_score': self._calculate_technical_score(
                        price_change, volume_ratio, momentum
                    )
                }
            except Exception as e:
                self.logger.error(f"Error calculating technical indicators for {symbol}: {e}")
                continue
        return technical_data

    def _calculate_technical_score(self, price_change, volume_ratio, momentum) -> float:
        price_weight = 0.4
        volume_weight = 0.3
        momentum_weight = 0.3
        price_score = min(max(price_change * 10, -1), 1)
        volume_score = min(max((volume_ratio - 1) * 0.5, -1), 1)
        momentum_score = min(max(momentum * 5, -1), 1)
        technical_score = (
            price_score * price_weight +
            volume_score * volume_weight +
            momentum_score * momentum_weight
        )
        return technical_score

    def _merge_data(self, stock_universe: List[str], technical_data: Dict, sentiment_data: Dict) -> Dict:
        merged_data = {}
        for symbol in stock_universe:
            if symbol not in technical_data or symbol not in sentiment_data:
                continue
            tech = technical_data[symbol]
            sent = sentiment_data[symbol]
            combined_score = (tech['technical_score'] * 0.6 + sent['score'] * 0.4)
            if combined_score > 0.2:
                category = 'bullish'
            elif combined_score < -0.2:
                category = 'bearish'
            elif abs(combined_score) > 0.1:
                category = 'volatile'
            else:
                category = 'neutral'
            merged_data[symbol] = {
                'score': combined_score,
                'category': category,
                'technical': tech,
                'sentiment': sent
            }
        return merged_data

    async def _get_sentiment_for_universe(self, stock_universe: List[str], market_sentiment: Dict) -> Dict:
        sentiment_data = {}
        for symbol in stock_universe:
            try:
                contract = Contract(symbol=symbol, secType='STK', exchange='SMART', currency='USD')
                news = await self.ibkr_client.reqNewsArticle(contract)
                news_sentiment = self._analyze_news_sentiment(news)
                base_score = market_sentiment.get('sentiment_score', 0.0)
                symbol_score = (base_score * 0.7 + news_sentiment * 0.3)
                if symbol_score > 0.2:
                    category = 'bullish'
                elif symbol_score < -0.2:
                    category = 'bearish'
                elif abs(symbol_score) > 0.1:
                    category = 'volatile'
                else:
                    category = 'neutral'
                sentiment_data[symbol] = {
                    'score': symbol_score,
                    'category': category
                }
            except Exception as e:
                self.logger.error(f"Error getting sentiment for {symbol}: {e}")
                sentiment_data[symbol] = {'score': 0.0, 'category': 'neutral'}
        return sentiment_data

    def _analyze_news_sentiment(self, news_articles) -> float:
        if not news_articles:
            return 0.0
        positive_count = sum(1 for article in news_articles if getattr(article, 'positive', False))
        negative_count = sum(1 for article in news_articles if getattr(article, 'negative', False))
        total_count = len(news_articles)
        if total_count == 0:
            return 0.0
        sentiment_score = (positive_count - negative_count) / total_count
        return sentiment_score

    def screen(self, sentiment_data):
        if not sentiment_data:
            self.logger.warning("No sentiment data provided to screener")
            return {'bull': [], 'bear': [], 'volatile': []}
        bull_stocks = []
        bear_stocks = []
        volatile_stocks = []
        for symbol, data in sentiment_data.items():
            try:
                category = data.get('category', 'neutral')
                score = data.get('score', 0.0)
                if category == 'bullish':
                    bull_stocks.append((symbol, score))
                elif category == 'bearish':
                    bear_stocks.append((symbol, score))
                elif category == 'volatile':
                    volatile_stocks.append((symbol, score))
            except Exception as e:
                self.logger.error(f"Error processing sentiment data for {symbol}: {e}")
                continue
        bull_stocks.sort(key=lambda x: x[1], reverse=True)
        bear_stocks.sort(key=lambda x: x[1])
        volatile_stocks.sort(key=lambda x: abs(x[1]), reverse=True)
        bull_stocks = bull_stocks[:self.max_stocks]
        bear_stocks = bear_stocks[:self.max_stocks]
        volatile_stocks = volatile_stocks[:self.max_stocks]
        def assign_rank(stocks):
            return [(symbol, score, rank + 1) for rank, (symbol, score) in enumerate(stocks)]
        bull_ranked = assign_rank(bull_stocks)
        bear_ranked = assign_rank(bear_stocks)
        volatile_ranked = assign_rank(volatile_stocks)
        self.logger.info(f"Screened stocks - Bull: {len(bull_ranked)}, Bear: {len(bear_ranked)}, Volatile: {len(volatile_ranked)}")
        for category, stocks in [('Bull', bull_ranked), ('Bear', bear_ranked), ('Volatile', volatile_ranked)]:
            if stocks:
                top_stock = stocks[0]
                self.logger.info(f"Top {category} stock: {top_stock[0]} (score: {top_stock[1]:.3f})")
        return {
            'bull': bull_ranked,
            'bear': bear_ranked,
            'volatile': volatile_ranked
        }

    def get_top_stocks(self, screened_results, category, count=5):
        if category not in screened_results:
            self.logger.warning(f"Invalid category: {category}")
            return []
        return screened_results[category][:count]

    def get_all_symbols(self, screened_results):
        all_symbols = []
        for category_stocks in screened_results.values():
            all_symbols.extend([stock[0] for stock in category_stocks])
        return all_symbols

    def filter_by_minimum_score(self, screened_results, min_score_threshold=0.3):
        filtered = {}
        for category, stocks in screened_results.items():
            filtered_stocks = []
            for symbol, score, rank in stocks:
                if abs(score) >= min_score_threshold:
                    filtered_stocks.append((symbol, score, rank))
            filtered[category] = filtered_stocks
        self.logger.info(f"Filtered by min score {min_score_threshold} - "
                        f"Bull: {len(filtered['bull'])}, "
                        f"Bear: {len(filtered['bear'])}, "
                        f"Volatile: {len(filtered['volatile'])}")
        return filtered

    def _extract_candidates_by_sentiment(self, screened_results: Dict, market_sentiment: Dict) -> List[str]:
        candidates = []
        if market_sentiment.get('bullish', False):
            bull_stocks = self.get_top_stocks(screened_results, 'bull', count=5)
            candidates.extend([stock[0] for stock in bull_stocks])
        if market_sentiment.get('bearish', False):
            bear_stocks = self.get_top_stocks(screened_results, 'bear', count=5)
            candidates.extend([stock[0] for stock in bear_stocks])
        if market_sentiment.get('volatile', False):
            volatile_stocks = self.get_top_stocks(screened_results, 'volatile', count=5)
            candidates.extend([stock[0] for stock in volatile_stocks])
        if not candidates or market_sentiment.get('neutral', False):
            all_symbols = self.get_all_symbols(screened_results)
            candidates = all_symbols[:8]
        seen = set()
        unique_candidates = []
        for symbol in candidates:
            if symbol not in seen:
                seen.add(symbol)
                unique_candidates.append(symbol)
        return unique_candidates[:10]
