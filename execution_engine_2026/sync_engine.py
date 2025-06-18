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
        self._news_thread = None
        
        # Continuous news monitoring
        self.news_running = False
        self.news_update_interval = 60  # Update news every 60 seconds
        self.current_market_sentiment = None
        self.last_news_update = None
        
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
        
        # Start continuous news monitoring
        self.news_running = True
        self._news_thread = threading.Thread(target=self._news_monitor_run, daemon=True)
        self._news_thread.start()
        
        self.logger.info("🚀 Execution engine started")
        self.logger.info("📰 News monitor started - running continuously")
        
    def stop(self):
        """Stop the execution engine"""
        self.running = False
        self.news_running = False
        
        if self._thread:
            self._thread.join(timeout=10)
        if self._news_thread:
            self._news_thread.join(timeout=10)
            
        self.logger.info("🛑 Execution engine stopped")
        self.logger.info("📰 News monitor stopped")
        
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
                
    def _news_monitor_run(self):
        """Continuous news monitoring loop - runs 24/7 when bot is active"""
        self.logger.info("📰 Starting continuous news monitoring...")
        
        while self.news_running:
            try:
                # Update market sentiment continuously
                self._update_news_sentiment()
                
                # Sleep for update interval
                time.sleep(self.news_update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in news monitoring loop: {e}", exc_info=True)
                # Don't stop news monitoring on errors, just wait and retry
                time.sleep(60)  # Wait 1 minute before retrying
                continue
                
        self.logger.info("📰 News monitoring loop ended")
                
    def _update_news_sentiment(self):
        """Update market sentiment from news sources - runs continuously"""
        try:
            # Get fresh market sentiment from news handler
            import asyncio
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Get market sentiment asynchronously
                sentiment_data = loop.run_until_complete(
                    self.news_analyzer.get_market_sentiment()
                )
                
                # Store the updated sentiment
                self.current_market_sentiment = sentiment_data
                self.last_news_update = time.time()
                
                # Log sentiment updates (less verbose during off-hours)
                current_time = datetime.now()
                overall_sentiment = sentiment_data.get('overall_sentiment', 'unknown')
                sentiment_score = sentiment_data.get('sentiment_score', 0)
                vix_level = sentiment_data.get('technical_sentiment', {}).get('vix_level', 20.0)
                
                if self._is_trading_hours():
                    self.logger.info(f"📊 Market sentiment updated: {overall_sentiment} "
                                   f"(score: {sentiment_score:.3f})")
                    if self.web_monitor:
                        self.web_monitor.log_activity("NEWS", "success", 
                            f"📊 Market sentiment: {overall_sentiment.upper()} "
                            f"(VIX: {vix_level:.1f}, Score: {sentiment_score:.2f})")
                else:
                    # Log less frequently during off-hours (every 10 updates)
                    if not hasattr(self, '_news_update_count'):
                        self._news_update_count = 0
                    self._news_update_count += 1
                    
                    if self._news_update_count % 10 == 0:
                        self.logger.info(f"📊 After-hours sentiment: {overall_sentiment} "
                                       f"(updates: {self._news_update_count})")
                        if self.web_monitor:
                            self.web_monitor.log_activity("NEWS", "info", 
                                f"🌙 After-hours update #{self._news_update_count}: {overall_sentiment.upper()}")
                
                # Update web monitor if available
                if self.web_monitor and sentiment_data:
                    market_sentiment = {
                        'current_sentiment': sentiment_data.get('overall_sentiment', 'neutral'),
                        'sentiment_score': sentiment_data.get('sentiment_score', 0),
                        'last_update': datetime.now().isoformat(),
                        'confidence': sentiment_data.get('confidence', 0.5),
                        'volatility_expected': sentiment_data.get('volatility_expected', 0.5),
                        'news_sources': sentiment_data.get('data_sources', []),
                        'sector_sentiment': sentiment_data.get('sector_sentiment', {}),
                        'technical_sentiment': sentiment_data.get('technical_sentiment', {})
                    }
                    self.web_monitor.update_market_sentiment(market_sentiment)
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error updating news sentiment: {e}")
            # Set fallback sentiment data
            self.current_market_sentiment = {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.5,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
                
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
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", "🚀 Starting new trading cycle")
                
            self.last_analysis_time = time.time()
            
            # Step 1: Get market sentiment
            self.logger.debug("Analyzing sentiment...")
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", "📰 Analyzing market sentiment...")
                
            sentiment = self._analyze_sentiment()
            self.logger.info(f"Market sentiment: {sentiment}")
            
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "success", 
                    f"📊 Market sentiment determined: {sentiment.value}")
            
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
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", "🔍 Screening stocks for opportunities...")
                
            candidates = self._screen_stocks(sentiment)
            self.logger.info(f"Found {len(candidates)} candidates")
            
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", 
                    f"📈 Stock screening complete: {len(candidates)} candidates found")
            
            if not candidates:
                self.logger.info("No suitable candidates found")
                if self.web_monitor:
                    self.web_monitor.log_activity("EXECUTION", "warning", 
                        "⚠️ No suitable stock candidates found for current market conditions")
                    self.web_monitor.add_trade_action(
                        'scan', 'MARKET', 'screening', 
                        {'result': 'no_candidates', 'sentiment': sentiment.value}
                    )
                return
                
            # Step 3: Execute appropriate strategy
            self.logger.debug("Executing strategies...")
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", 
                    f"⚡ Executing {sentiment.value} strategy for {len(candidates)} candidates...")
                    
            self._execute_strategies(sentiment, candidates)
            
            # Step 4: Update positions
            self.logger.debug("Updating positions...")
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", "📊 Updating position tracking...")
                
            self._update_positions()
            
            # Step 5: Manage existing positions
            self.logger.debug("Managing positions...")
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "info", "🔧 Managing existing positions...")
                
            self._manage_positions()
            
            self.logger.info("Trading cycle completed")
            if self.web_monitor:
                self.web_monitor.log_activity("EXECUTION", "success", "✅ Trading cycle completed successfully")
            
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
        """Analyze overall market sentiment using continuously updated news data"""
        try:
            self.logger.debug("Analyzing sentiment from continuous news monitoring...")
            
            # Use continuously updated sentiment data
            if self.current_market_sentiment:
                sentiment_data = self.current_market_sentiment
                
                # Check if data is recent (within last 5 minutes)
                data_age = time.time() - (self.last_news_update or 0)
                if data_age > 300:  # 5 minutes
                    self.logger.warning(f"News sentiment data is {data_age:.0f}s old, using fallback")
                
                # Extract sentiment information
                overall_sentiment = sentiment_data.get('overall_sentiment', 'neutral')
                sentiment_score = sentiment_data.get('sentiment_score', 0.0)
                volatility_expected = sentiment_data.get('volatility_expected', 0.5)
                
                # Store for web monitor
                tech_sentiment = sentiment_data.get('technical_sentiment', {})
                self._last_vix_level = tech_sentiment.get('vix_level', 20.0)
                self._last_spy_price = 0  # Will be updated by news handler
                self._last_spy_change = tech_sentiment.get('market_momentum', 0.0)
                
                # Convert news sentiment to MarketCondition
                if volatility_expected > 0.7:  # High volatility expected
                    condition = MarketCondition.HIGH_VOLATILITY
                    self.logger.info(f"High volatility expected: {volatility_expected:.2f}")
                elif overall_sentiment == 'bullish' or sentiment_score > 0.2:
                    condition = MarketCondition.BULLISH
                elif overall_sentiment == 'bearish' or sentiment_score < -0.2:
                    condition = MarketCondition.BEARISH
                else:
                    condition = MarketCondition.NEUTRAL
                
                self.logger.info(f"News-based sentiment: {condition.value} "
                               f"(score: {sentiment_score:.3f}, volatility: {volatility_expected:.2f})")
                return condition
                
            else:
                # Fallback: No news data available, get basic market data
                self.logger.warning("No news sentiment data available, using basic market analysis")
                return self._fallback_sentiment_analysis()
                
        except Exception as e:
            self.logger.error(f"Error analyzing news sentiment: {e}", exc_info=True)
            return self._fallback_sentiment_analysis()
            
    def _fallback_sentiment_analysis(self) -> MarketCondition:
        """Fallback sentiment analysis using direct market data"""
        try:
            self.logger.debug("Running fallback sentiment analysis...")
            
            # Initialize defaults for web monitor
            self._last_spy_price = 0
            self._last_spy_change = 0
            self._last_vix_level = 20.0
            
            # Get basic SPY data for trend
            try:
                spy_data = self.ibkr_client.get_market_data('SPY')
                
                if (spy_data and 
                    spy_data.get('last') and 
                    spy_data.get('last', 0) > 0 and 
                    not spy_data.get('error')):
                    
                    last_price = spy_data.get('last', 0)
                    close_price = spy_data.get('close', 0)
                    
                    self._last_spy_price = last_price
                    
                    if close_price and close_price != last_price:
                        change_pct = (last_price - close_price) / close_price
                        self._last_spy_change = change_pct
                        
                        if change_pct > 0.005:  # 0.5% threshold
                            return MarketCondition.BULLISH
                        elif change_pct < -0.005:
                            return MarketCondition.BEARISH
                            
            except Exception as e:
                self.logger.debug(f"Fallback SPY analysis failed: {e}")
            
            self.logger.info("Fallback analysis complete: NEUTRAL")
            return MarketCondition.NEUTRAL
            
        except Exception as e:
            self.logger.error(f"Error in fallback sentiment analysis: {e}")
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
            if self.web_monitor:
                self.web_monitor.log_activity("SCREENER", "info", 
                    f"🔍 Screening S&P 500 universe for {sentiment.value} opportunities...")
            
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
                if self.web_monitor:
                    self.web_monitor.log_activity("SCREENER", "success", 
                        f"📈 Found {len(candidates)} qualified candidates: {', '.join(candidates[:5])}" + 
                        (f" +{len(candidates)-5} more" if len(candidates) > 5 else ""))
                
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
        if self.web_monitor:
            self.web_monitor.log_activity("STRATEGY", "info", 
                f"🎯 Executing {strategy_name.upper()} strategy for {len(candidates[:5])} top candidates")
        
        # Execute trades for each candidate
        for symbol in candidates[:5]:  # Limit to top 5
            try:
                self.logger.info(f"Evaluating {symbol} for {strategy_name} strategy")
                if self.web_monitor:
                    self.web_monitor.log_activity("STRATEGY", "info", 
                        f"🔎 Analyzing {symbol} for {strategy_name} options opportunities...")
                
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
                    
                    if self.web_monitor:
                        self.web_monitor.log_activity("STRATEGY", "success", 
                            f"✅ {symbol}: Found viable {strategy_name} opportunity "
                            f"(Score: {opportunity.get('score', 0):.2f}, "
                            f"P(profit): {opportunity.get('probability_profit', 0):.1%})")
                    
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
                        
                        if self.web_monitor:
                            self.web_monitor.log_activity("STRATEGY", "success", 
                                f"💰 {symbol}: {strategy_name.upper()} trade executed! "
                                f"Order ID: {order_id} | Cost: ${opportunity.get('max_loss', 0):.0f}")
                        
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
                        
                        if self.web_monitor:
                            self.web_monitor.log_activity("STRATEGY", "error", 
                                f"❌ {symbol}: Trade execution failed for {strategy_name} strategy")
                        
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