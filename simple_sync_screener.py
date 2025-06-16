"""
Simple Synchronous Stock Screener
Works directly with IBKRSyncWrapper without async complexity
"""

import logging
from typing import Dict, List


class SimpleSyncScreener:
    """Simplified synchronous stock screener"""
    
    def __init__(self, ibkr_client):
        self.ibkr_client = ibkr_client
        self.logger = logging.getLogger(__name__)
        
    def screen_stocks(self, market_sentiment: Dict) -> List[str]:
        """Simple screening based on market sentiment"""
        try:
            # Use a smaller universe for faster screening
            if market_sentiment.get('bullish'):
                # Tech stocks for bullish markets
                universe = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META']
            elif market_sentiment.get('bearish'):
                # Defensive stocks for bearish markets
                universe = ['JNJ', 'PG', 'KO', 'WMT', 'PEP']
            elif market_sentiment.get('volatile'):
                # High beta stocks for volatile markets
                universe = ['TSLA', 'AMD', 'NFLX', 'COIN', 'ROKU']
            else:
                # Mixed universe for neutral markets
                universe = ['SPY', 'AAPL', 'MSFT', 'AMZN', 'GOOGL']
            
            # Get market data for each stock
            candidates = []
            import time
            for i, symbol in enumerate(universe):
                try:
                    # Add a longer delay between requests to be polite to IBKR Gateway
                    if i > 0:
                        time.sleep(3)  # Increased from 2 to 3 seconds between requests
                        
                    self.logger.debug(f"Getting data for {symbol}...")
                    market_data = self.ibkr_client.get_market_data(symbol)
                    if market_data and market_data.get('last'):
                        # Simple momentum check
                        last_price = market_data.get('last', 0)
                        close_price = market_data.get('close', last_price)
                        
                        # Calculate momentum
                        if close_price > 0:
                            momentum = (last_price - close_price) / close_price
                            self.logger.info(f"✓ {symbol}: ${last_price:.2f} (momentum: {momentum:.2%})")
                            
                            # Add to candidates if momentum is positive for bullish, negative for bearish
                            if (market_sentiment.get('bullish') and momentum > 0) or \
                               (market_sentiment.get('bearish') and momentum < 0) or \
                               market_sentiment.get('volatile'):
                                candidates.append(symbol)
                        else:
                            self.logger.debug(f"{symbol}: No close price available")
                    else:
                        self.logger.debug(f"No data for {symbol}")
                except Exception as e:
                    self.logger.debug(f"Skipping {symbol}: {e}")
                    
            self.logger.info(f"Screened {len(candidates)} candidates from {len(universe)} stocks")
            return candidates[:5]  # Return top 5
            
        except Exception as e:
            self.logger.error(f"Error in simple screening: {e}")
            return [] 