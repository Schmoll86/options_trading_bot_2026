"""
Synchronous Execution Engine for Options Trading Bot 2026
Manages trading workflow without async complexity
"""

import logging
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import pytz
import asyncio
import nest_asyncio

# Allow nested event loops for running async code in sync context
nest_asyncio.apply()


class MarketCondition(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish" 
    VOLATILE = "volatile"
    NEUTRAL = "neutral"
    NORMAL_VOLATILITY = "normal_volatility"
    HIGH_VOLATILITY = "high_volatility"


class SyncExecutionEngine2026:
    """
    Synchronous execution engine that manages the trading workflow.
    No async/await complexity - just simple threading for background tasks.
    """
    
    def __init__(self, config: Dict, ibkr_client, strategies: List, 
                 news_analyzer, stock_screener, web_monitor=None):
        self.config = config
        self.ibkr_client = ibkr_client
        self.strategies = strategies
        self.news_analyzer = news_analyzer
        self.stock_screener = stock_screener
        self.web_monitor = web_monitor
        self.logger = logging.getLogger(__name__)
        
        # Engine state
        self.running = False
        self.trading_enabled = True
        self.last_analysis_time = None
        self.analysis_interval = config.get('ANALYSIS_INTERVAL', 300)  # 5 minutes
        
        # Threading
        self._thread = None
        
        # Performance tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.active_positions = {}
        
    def start(self):
        """Start the execution engine in a background thread"""
        if self.running:
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger.info("🚀 Execution engine started")
        
    def stop(self):
        """Stop the execution engine"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=10)
        self.logger.info("🛑 Execution engine stopped")
        
    def _run(self):
        """Main execution loop"""
        while self.running:
            try:
                # Check if it's time to analyze
                if self._should_analyze():
                    self._execute_trading_cycle()
                    
                # Sleep briefly
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}", exc_info=True)
                # Don't stop the bot on errors
                time.sleep(30)  # Wait before retrying
                continue  # Keep the loop running
                
    def _should_analyze(self) -> bool:
        """Check if we should run analysis"""
        if not self.trading_enabled:
            return False
            
        # Check trading hours
        if not self._is_trading_hours():
            return False
            
        # Check analysis interval
        if self.last_analysis_time:
            elapsed = time.time() - self.last_analysis_time
            if elapsed < self.analysis_interval:
                return False
                
        return True
        
    def _is_trading_hours(self) -> bool:
        """Check if market is open"""
        # Get current time in ET directly
        et_tz = pytz.timezone('US/Eastern')
        et_time = datetime.now(et_tz)
        weekday = et_time.weekday()
        
        # Skip weekends
        if weekday >= 5:
            return False
            
        # Market hours: 9:30 AM - 4:00 PM ET
        hour = et_time.hour
        minute = et_time.minute
        
        # Convert to minutes for easier comparison
        current_minutes = hour * 60 + minute
        market_open = 9 * 60 + 30  # 9:30 AM
        market_close = 16 * 60     # 4:00 PM
        
        return market_open <= current_minutes <= market_close
        
    def _execute_trading_cycle(self):
        """Execute one complete trading cycle"""
        try:
            self.logger.info("Starting trading cycle...")
            self.last_analysis_time = time.time()
            
            # Step 1: Get market sentiment
            self.logger.debug("Analyzing sentiment...")
            sentiment = self._analyze_sentiment()
            self.logger.info(f"Market sentiment: {sentiment}")
            
            # Update web monitor with market sentiment
            if self.web_monitor:
                sentiment_data = {
                    'current_sentiment': sentiment.value,
                    'last_update': datetime.now().isoformat(),
                    'spy_last': getattr(self, '_last_spy_price', 0),
                    'spy_change': getattr(self, '_last_spy_change', 0),
                    'vix_level': getattr(self, '_last_vix_level', 0)
                }
                self.web_monitor.update_market_sentiment(sentiment_data)
            
            # Step 2: Screen stocks based on sentiment
            self.logger.debug("Screening stocks...")
            candidates = self._screen_stocks(sentiment)
            self.logger.info(f"Found {len(candidates)} candidates")
            
            if not candidates:
                self.logger.info("No suitable candidates found")
                # Log this as an action for monitoring
                if self.web_monitor:
                    self.web_monitor.add_trade_action(
                        'scan', 'MARKET', 'screening', 
                        {'result': 'no_candidates', 'sentiment': sentiment.value}
                    )
                return
                
            # Step 3: Execute appropriate strategy
            self.logger.debug("Executing strategies...")
            self._execute_strategies(sentiment, candidates)
            
            # Step 4: Update positions
            self.logger.debug("Updating positions...")
            self._update_positions()
            
            # Step 5: Manage existing positions
            self.logger.debug("Managing positions...")
            self._manage_positions()
            
            self.logger.info("Trading cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}", exc_info=True)
            # Log error to web monitor
            if self.web_monitor:
                self.web_monitor.add_error(
                    'trading_cycle_error', 
                    str(e), 
                    {'phase': 'trading_cycle', 'timestamp': datetime.now().isoformat()}
                )
            # Don't re-raise the exception - let the bot continue running
            return
            
    def _analyze_sentiment(self) -> MarketCondition:
        """Analyze overall market sentiment"""
        try:
            # Analyze market sentiment
            self.logger.debug("Analyzing sentiment...")
            self.logger.debug("Getting SPY market data...")
            
            # Initialize defaults for web monitor
            self._last_spy_price = 0
            self._last_spy_change = 0
            self._last_vix_level = 0
            
            # Add timeout protection and better error handling
            try:
                self.logger.debug(f"Calling get_market_data for SPY at {datetime.now()}")
                spy_data = self.ibkr_client.get_market_data('SPY')
                self.logger.debug(f"Got SPY data response: {spy_data}")
            except Exception as e:
                self.logger.error(f"Error getting SPY data: {e}")
                spy_data = None
            
            if not spy_data or not spy_data.get('last'):
                self.logger.warning("No SPY data available, returning NEUTRAL")
                return MarketCondition.NEUTRAL
                
            # Simple market condition logic based on SPY movement
            last_price = spy_data.get('last', 0)
            close_price = spy_data.get('close', 0)
            
            # Store for web monitor
            self._last_spy_price = last_price
            
            # If we don't have close price, use last price with small threshold
            if close_price == 0 or close_price == last_price:
                self.logger.debug("No close price available, using neutral sentiment")
                market_trend = MarketCondition.NEUTRAL
                self._last_spy_change = 0
            else:
                change_pct = (last_price - close_price) / close_price
                self._last_spy_change = change_pct
                self.logger.info(f"SPY change: {change_pct:.3%} (Last: ${last_price:.2f}, Close: ${close_price:.2f})")
                
                # Simple 0.5% threshold (reduced from 1%)
                if change_pct > 0.005:
                    market_trend = MarketCondition.BULLISH
                elif change_pct < -0.005:
                    market_trend = MarketCondition.BEARISH
                else:
                    market_trend = MarketCondition.NEUTRAL
            
            # Get VIX data for volatility assessment (optional)
            volatility = MarketCondition.NORMAL_VOLATILITY
            try:
                self.logger.debug("Getting VIX market data...")
                vix_data = self.ibkr_client.get_market_data('VIX')
                self.logger.debug(f"Got VIX data response: {vix_data}")
                
                if vix_data and vix_data.get('last') and vix_data['last'] > 0:
                    vix_level = vix_data['last']
                    self._last_vix_level = vix_level  # Store for web monitor
                    self.logger.info(f"VIX level: {vix_level:.2f}")
                    # High VIX = high volatility
                    if vix_level > 20:
                        volatility = MarketCondition.HIGH_VOLATILITY
                        self.logger.info(f"High volatility detected: VIX={vix_level:.2f}")
                else:
                    self.logger.debug("No valid VIX data available, using normal volatility")
            except Exception as e:
                self.logger.debug(f"Could not get VIX data: {e}, continuing without it")
                # Continue without VIX data rather than crashing
            
            # Return HIGH_VOLATILITY if detected, otherwise return trend
            if volatility == MarketCondition.HIGH_VOLATILITY:
                self.logger.info(f"Market analysis complete: {volatility.value}")
                return volatility
            
            self.logger.info(f"Market analysis complete: {market_trend.value}")
            return market_trend
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}", exc_info=True)
            return MarketCondition.NEUTRAL
            
    def _screen_stocks(self, sentiment: MarketCondition) -> List[str]:
        """Screen stocks based on market condition"""
        try:
            # Create market sentiment dict for sophisticated screener
            market_sentiment = {
                'sentiment_score': 0.0,
                'bullish': sentiment == MarketCondition.BULLISH,
                'bearish': sentiment == MarketCondition.BEARISH,
                'volatile': sentiment in [MarketCondition.VOLATILE, MarketCondition.HIGH_VOLATILITY],
                'neutral': sentiment == MarketCondition.NEUTRAL,
                'volatility_expected': 0.7 if sentiment == MarketCondition.HIGH_VOLATILITY else 0.3
            }
            
            # Use sophisticated StockScreener2026 (passed in constructor)
            self.logger.info("Using sophisticated StockScreener2026 with full S&P 500 universe")
            
            # Run async screening in sync context
            import asyncio
            import nest_asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use the sophisticated screener's screen_stocks method
                candidates = loop.run_until_complete(
                    self.stock_screener.screen_stocks(market_sentiment)
                )
                
                self.logger.info(f"Sophisticated screener found {len(candidates)} candidates: {candidates[:5]}...")
                
                # Update web monitor with sophisticated screening results if available
                if self.web_monitor and candidates:
                    # Get full screening results for web display
                    try:
                        full_results = loop.run_until_complete(
                            self._get_full_screening_results_sync(market_sentiment)
                        )
                        if full_results:
                            self.web_monitor.update_screening_results(full_results)
                    except Exception as e:
                        self.logger.warning(f"Could not update web screening results: {e}")
                
                return candidates
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error with sophisticated screener: {e}")
            # Fallback to simple screener only if sophisticated fails
            self.logger.warning("Falling back to simple screener")
            return self._fallback_screen_stocks(sentiment)
            
    def _fallback_screen_stocks(self, sentiment: MarketCondition) -> List[str]:
        """Fallback screening using simple screener if sophisticated fails"""
        try:
            from simple_sync_screener import SimpleSyncScreener
            
            market_sentiment = {
                'sentiment_score': 0.0,
                'bullish': sentiment == MarketCondition.BULLISH,
                'bearish': sentiment == MarketCondition.BEARISH,
                'volatile': sentiment in [MarketCondition.VOLATILE, MarketCondition.HIGH_VOLATILITY],
                'neutral': sentiment == MarketCondition.NEUTRAL,
                'volatility_expected': 0.7 if sentiment == MarketCondition.HIGH_VOLATILITY else 0.3
            }
            
            simple_screener = SimpleSyncScreener(self.ibkr_client)
            candidates = simple_screener.screen_stocks(market_sentiment)
            
            self.logger.warning(f"Using fallback simple screener with {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error with fallback screener: {e}")
            return []
            
    async def _get_full_screening_results_sync(self, market_sentiment):
        """Get full screening results with scores using the sophisticated screener"""
        try:
            # Get stock universe from sophisticated screener
            stock_universe = await self.stock_screener.get_dynamic_universe()
            
            # Get technical and sentiment data
            await self.stock_screener._update_market_data(stock_universe)
            technical_data = await self.stock_screener._get_technical_indicators(stock_universe)
            sentiment_data = await self.stock_screener._get_sentiment_for_universe(stock_universe, market_sentiment)
            
            # Merge and screen
            combined_data = self.stock_screener._merge_data(stock_universe, technical_data, sentiment_data)
            screened_results = self.stock_screener.screen(combined_data)
            
            return screened_results
            
        except Exception as e:
            self.logger.error(f"Error getting full screening results: {e}")
            return None
            
    def _execute_strategies(self, sentiment: MarketCondition, candidates: List[str]):
        """Execute strategies based on market condition"""
        # Map conditions to strategies
        strategy_map = {
            MarketCondition.BULLISH: 0,   # Bull strategy
            MarketCondition.BEARISH: 1,   # Bear strategy
            MarketCondition.VOLATILE: 2,  # Volatile strategy
            MarketCondition.HIGH_VOLATILITY: 2,  # Also map HIGH_VOLATILITY to volatile strategy
        }
        
        # Select ONE strategy based on market sentiment
        strategy_idx = strategy_map.get(sentiment)
        
        if strategy_idx is None:
            self.logger.warning(f"No strategy mapped for sentiment: {sentiment}")
            return
            
        # Execute the selected strategy
        strategy_names = ['bull', 'bear', 'volatility']
        strategy = self.strategies[strategy_idx]
        strategy_name = strategy_names[strategy_idx]
        
        self.logger.info(f"🎯 Market sentiment: {sentiment.value} → Executing {strategy_name} strategy")
        
        # Execute trades for each candidate
        for symbol in candidates[:5]:  # Limit to top 5
            try:
                self.logger.info(f"Evaluating {symbol} for {strategy_name} strategy")
                
                # Run async strategy methods synchronously
                import asyncio
                from async_sync_adapter import AsyncSyncAdapter
                
                # Create async adapter for the sync client
                async_client = AsyncSyncAdapter(self.ibkr_client)
                
                # Temporarily replace strategy's client with async adapter
                original_client = strategy.ibkr_client
                strategy.ibkr_client = async_client
                
                # Scan for opportunities
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create market sentiment dict for strategies that need it
                market_sentiment_dict = {
                    'sentiment_score': 0.0,
                    'bullish': sentiment == MarketCondition.BULLISH,
                    'bearish': sentiment == MarketCondition.BEARISH,
                    'volatile': sentiment in [MarketCondition.VOLATILE, MarketCondition.HIGH_VOLATILITY],
                    'neutral': sentiment == MarketCondition.NEUTRAL,
                    'volatility_expected': 0.8 if sentiment == MarketCondition.HIGH_VOLATILITY else 0.3
                }
                
                # Call appropriate scan method based on strategy type
                if strategy_name == 'volatility':
                    opportunities = loop.run_until_complete(
                        strategy.scan_opportunities([symbol], market_sentiment_dict)
                    )
                else:
                    opportunities = loop.run_until_complete(
                        strategy.scan_opportunities([symbol])
                    )
                
                if opportunities:
                    opportunity = opportunities[0]  # Take the best opportunity
                    self.logger.info(f"📊 Found opportunity for {symbol}: "
                                   f"Score={opportunity.get('score', 0):.2f}, "
                                   f"P(profit)={opportunity.get('probability_profit', 0):.2%}")
                    
                    # Log opportunity found to web monitor
                    if self.web_monitor:
                        self.web_monitor.add_trade_action(
                            'scan', symbol, strategy_name,
                            {
                                'score': opportunity.get('score', 0),
                                'probability_profit': opportunity.get('probability_profit', 0),
                                'max_profit': opportunity.get('max_profit', 0),
                                'max_loss': opportunity.get('max_loss', 0),
                                'risk_reward_ratio': opportunity.get('risk_reward_ratio', 0)
                            }
                        )
                    
                    # Execute the trade
                    order_id = loop.run_until_complete(
                        strategy.execute_trade(opportunity)
                    )
                    
                    if order_id:
                        self.logger.info(f"✅ Trade executed for {symbol}: Order ID {order_id}")
                        self.daily_trades += 1
                        
                        # Log successful trade execution to web monitor
                        if self.web_monitor:
                            self.web_monitor.add_trade_action(
                                'open', symbol, strategy_name,
                                {
                                    'order_id': order_id,
                                    'entry_price': opportunity.get('current_price', 0),
                                    'position_size': opportunity.get('position_size', 0),
                                    'max_profit': opportunity.get('max_profit', 0),
                                    'max_loss': opportunity.get('max_loss', 0),
                                    'strategy_details': {
                                        'long_strike': opportunity.get('long_strike'),
                                        'short_strike': opportunity.get('short_strike'),
                                        'expiry': opportunity.get('expiry'),
                                        'debit': opportunity.get('debit')
                                    }
                                }
                            )
                    else:
                        self.logger.warning(f"Trade execution failed for {symbol}")
                        
                        # Log failed trade execution to web monitor
                        if self.web_monitor:
                            self.web_monitor.add_error(
                                'trade_execution_failed', 
                                f"Failed to execute {strategy_name} trade for {symbol}",
                                {'symbol': symbol, 'strategy': strategy_name, 'opportunity': opportunity}
                            )
                else:
                    self.logger.info(f"No viable opportunity found for {symbol}")
                    
                    # Log no opportunity found
                    if self.web_monitor:
                        self.web_monitor.add_trade_action(
                            'scan', symbol, strategy_name,
                            {'result': 'no_opportunity', 'reason': 'criteria_not_met'}
                        )
                
                # Restore original client
                strategy.ibkr_client = original_client
                    
                loop.close()
                    
            except Exception as e:
                self.logger.error(f"Error executing strategy for {symbol}: {e}")
                
    def _update_positions(self):
        """Update active positions tracking"""
        try:
            positions = self.ibkr_client.get_positions()
            self.active_positions = {
                pos.contract.symbol: pos for pos in positions
            }
            
            # Calculate daily P&L
            self.daily_pnl = sum(
                getattr(pos, 'unrealizedPNL', 0) for pos in positions
            )
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
            
    def _manage_positions(self):
        """Check each strategy's position management rules"""
        try:
            # Get current positions
            positions = list(self.active_positions.values())
            
            if not positions:
                return
                
            # Let each strategy check its positions
            for strategy in self.strategies:
                try:
                    # Check if strategy has manage_positions method
                    if hasattr(strategy, 'manage_positions'):
                        # Note: manage_positions is async in the strategy modules
                        # For sync engine, we'll need to handle this differently
                        # For now, we'll rely on the portfolio monitor
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error in strategy position management: {e}")
                    
            self.logger.debug(f"Managed {len(positions)} positions")
            
        except Exception as e:
            self.logger.error(f"Error managing positions: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'running': self.running,
            'trading_enabled': self.trading_enabled,
            'last_analysis': self.last_analysis_time,
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'active_positions': len(self.active_positions),
            'market_open': self._is_trading_hours()
        }
        
    def enable_trading(self):
        """Enable trading"""
        self.trading_enabled = True
        self.logger.info("Trading enabled")
        
    def disable_trading(self):
        """Disable trading"""
        self.trading_enabled = False
        self.logger.info("Trading disabled")
        
    def force_analysis(self):
        """Force an immediate analysis cycle"""
        self.last_analysis_time = 0
        self.logger.info("Forced analysis requested") 