# execution_engine_2026/engine.py
import asyncio
import logging
from typing import Dict, List
from datetime import datetime

class ExecutionEngine2026:
    """Central execution engine coordinating all strategies"""

    def __init__(self, ibkr_client, risk_manager, bull_module, bear_module,
                 volatile_module, news_handler, stock_screener):
        self.ibkr_client = ibkr_client
        self.risk_manager = risk_manager
        self.bull_module = bull_module
        self.bear_module = bear_module
        self.volatile_module = volatile_module
        self.news_handler = news_handler
        self.stock_screener = stock_screener
        self.logger = logging.getLogger(__name__)
        self.running = False
        self._cycle_semaphore = asyncio.Semaphore(1)  # Ensure only one trading cycle at a time
        self._execution_semaphore = asyncio.Semaphore(3)  # Limit concurrent executions
        self._last_execution_time = None
        self._min_execution_interval = 2  # Minimum seconds between executions

    async def start(self):
        """Start the execution engine"""
        self.running = True
        self.logger.info("🚀 Execution engine started")

    def stop(self):
        """Stop the execution engine"""
        self.running = False
        self.logger.info("🛑 Execution engine stopped")

    async def run_trading_cycle(self):
        """Run a single trading cycle with proper concurrency control"""
        if not self.running:
            return
        
        async with self._cycle_semaphore:  # Ensure only one cycle runs at a time
            try:
                self.logger.info("🔄 Starting trading cycle...")
                
                # Check if trading is halted
                if self.risk_manager.is_trading_halted():
                    self.logger.warning("Trading halted - skipping cycle")
                    return
                
                # Get market data and sentiment concurrently
                market_data_tasks = [
                    self.news_handler.get_market_sentiment(),
                    self.stock_screener.get_dynamic_universe(),
                    self.risk_manager.get_risk_metrics()
                ]
                market_sentiment, stock_universe, risk_metrics = await asyncio.gather(*market_data_tasks)
                
                self.logger.info(f"Market sentiment: {market_sentiment}")
                
                # Update market data
                await self.stock_screener._update_market_data(stock_universe)
                
                # Screen stocks
                candidate_symbols = await self.stock_screener.screen_stocks(market_sentiment)
                self.logger.info(f"Candidate symbols: {candidate_symbols}")
                
                if not candidate_symbols:
                    self.logger.info("No candidate symbols found")
                    return
                
                # Scan for opportunities concurrently based on sentiment
                opportunity_tasks = []
                if market_sentiment.get('bullish', False):
                    opportunity_tasks.append(self.bull_module.scan_opportunities(candidate_symbols))
                if market_sentiment.get('bearish', False):
                    opportunity_tasks.append(self.bear_module.scan_opportunities(candidate_symbols))
                if market_sentiment.get('volatile', False):
                    opportunity_tasks.append(self.volatile_module.scan_opportunities(candidate_symbols, market_sentiment))
                
                # Wait for all opportunity scans to complete
                opportunity_results = await asyncio.gather(*opportunity_tasks, return_exceptions=True)
                
                # Filter out exceptions and flatten results
                all_opportunities = []
                for result in opportunity_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Error scanning opportunities: {result}")
                        continue
                    all_opportunities.extend(result)
                
                # Execute opportunities if any found
                if all_opportunities:
                    await self._execute_best_opportunities(all_opportunities, risk_metrics)
                else:
                    self.logger.info("No trading opportunities found")
                
                # Manage existing positions
                await self._manage_existing_positions()
                
                self.logger.info("✅ Trading cycle complete")
            except Exception as e:
                self.logger.error(f"Error in trading cycle: {e}")

    async def _execute_best_opportunities(self, opportunities: List[Dict], risk_metrics: Dict):
        """Execute the best trading opportunities with proper concurrency control"""
        # Sort opportunities by score and filter by risk metrics
        sorted_opps = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)
        filtered_opps = self._filter_opportunities_by_risk(sorted_opps, risk_metrics)
        
        if not filtered_opps:
            self.logger.info("No opportunities passed risk checks")
            return
        
        # Create execution tasks for the best opportunities
        execution_tasks = []
        for opp in filtered_opps[:3]:  # Limit to top 3 opportunities
            execution_tasks.append(self._execute_single_opportunity(opp))
        
        # Execute opportunities with proper concurrency control
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Process results
        successful_executions = 0
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error executing opportunity: {result}")
                continue
            if result:
                successful_executions += 1
        
        if successful_executions > 0:
            self.logger.info(f"🎯 Successfully executed {successful_executions} trades this cycle")

    async def _execute_single_opportunity(self, opportunity: Dict) -> bool:
        """Execute a single trading opportunity with rate limiting"""
        async with self._execution_semaphore:  # Limit concurrent executions
            try:
                # Check execution timing
                now = datetime.now()
                if self._last_execution_time:
                    time_since_last = (now - self._last_execution_time).total_seconds()
                    if time_since_last < self._min_execution_interval:
                        await asyncio.sleep(self._min_execution_interval - time_since_last)
                
                # Execute the strategy
                strategy_type = opportunity.get('type', opportunity.get('strategy', ''))
                if 'bull' in strategy_type:
                    trade_id = await self.bull_module.execute_trade(opportunity)
                elif 'bear' in strategy_type:
                    trade_id = await self.bear_module.execute_trade(opportunity)
                elif 'volatile' in strategy_type:
                    trade_id = await self.volatile_module.execute_trade(opportunity)
                else:
                    return False
                
                if trade_id:
                    self._last_execution_time = datetime.now()
                    self.logger.info(f"✅ Executed {strategy_type} for {opportunity['symbol']}: {trade_id}")
                    return True
                
                return False
            except Exception as e:
                self.logger.error(f"Error executing opportunity {opportunity}: {e}")
                return False

    async def _manage_existing_positions(self):
        """Manage existing positions using strategy-specific rules"""
        try:
            # Get current positions
            positions = await self.ibkr_client.get_positions()
            
            if not positions:
                return
            
            # Group positions by strategy type
            strategy_positions = {
                'bull': [],
                'bear': [],
                'volatile': []
            }
            
            # Categorize positions
            for position in positions:
                if position.contract.secType in ['OPT', 'BAG']:
                    # Simple categorization based on contract type
                    if position.contract.right == 'C' and position.position > 0:
                        strategy_positions['bull'].append(position)
                    elif position.contract.right == 'P' and position.position > 0:
                        strategy_positions['bear'].append(position)
                    else:
                        strategy_positions['volatile'].append(position)
            
            # Let each strategy manage its positions
            management_tasks = []
            
            if strategy_positions['bull']:
                management_tasks.append(
                    self._process_strategy_management(self.bull_module, strategy_positions['bull'])
                )
            if strategy_positions['bear']:
                management_tasks.append(
                    self._process_strategy_management(self.bear_module, strategy_positions['bear'])
                )
            if strategy_positions['volatile']:
                management_tasks.append(
                    self._process_strategy_management(self.volatile_module, strategy_positions['volatile'])
                )
            
            # Execute management tasks concurrently
            if management_tasks:
                await asyncio.gather(*management_tasks, return_exceptions=True)
                
        except Exception as e:
            self.logger.error(f"Error managing existing positions: {e}")

    async def _process_strategy_management(self, strategy, positions):
        """Process position management for a specific strategy"""
        try:
            # Get management actions from strategy
            actions = await strategy.manage_positions(positions)
            
            # Execute closing orders for positions that need to be closed
            for action in actions:
                if action['action'] == 'close':
                    await self._close_position(action['position'], action['reason'])
                    
        except Exception as e:
            self.logger.error(f"Error in strategy position management: {e}")

    async def _close_position(self, position, reason: str):
        """Close a position based on strategy recommendation"""
        try:
            from ib_insync import MarketOrder
            
            # Determine action (opposite of current position)
            action = 'SELL' if position.position > 0 else 'BUY'
            quantity = abs(position.position)
            
            # Create market order for immediate execution
            order = MarketOrder(
                action=action,
                totalQuantity=quantity
            )
            
            # Place the closing order
            self.logger.info(f"Closing position {position.contract.symbol} - Reason: {reason}")
            order_id = await self.ibkr_client.place_order(position.contract, order)
            
            if order_id:
                self.logger.info(f"✅ Position closed: {position.contract.symbol} - {reason}")
                
                # Update daily loss if it was a stop loss
                if reason == 'stop_loss' and hasattr(position, 'unrealizedPNL'):
                    loss = position.unrealizedPNL
                    if loss < 0:
                        self.risk_manager.update_daily_loss(abs(loss))
                        
        except Exception as e:
            self.logger.error(f"Error closing position {position.contract.symbol}: {e}")

    def _filter_opportunities_by_risk(self, opportunities: List[Dict], risk_metrics: Dict) -> List[Dict]:
        """Filter opportunities based on risk metrics"""
        filtered_opps = []
        for opp in opportunities:
            try:
                # Check position limits
                if not self.risk_manager.can_open_position(opp['symbol']):
                    continue
                
                # Check risk exposure
                if not self.risk_manager.check_risk_exposure(opp):
                    continue
                
                # Check volatility limits
                if not self.risk_manager.check_volatility_limits(opp):
                    continue
                
                filtered_opps.append(opp)
            except Exception as e:
                self.logger.error(f"Error filtering opportunity {opp}: {e}")
                continue
        return filtered_opps

    def is_running(self) -> bool:
        """Return the current running status."""
        return self.running
