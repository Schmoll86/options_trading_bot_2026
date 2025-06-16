# risk_mgmt_2026/portfolio_monitor.py
import time
import threading
from datetime import datetime
import logging
from typing import Dict, List

class PortfolioMonitor2026:
    """Continuous monitoring with position management"""

    def __init__(self, risk_manager, ibkr_client):
        self.risk_manager = risk_manager
        self.ibkr_client = ibkr_client
        self.current_positions = {}
        self.position_entry_prices = {}  # Track entry prices
        self.monitoring = False
        self.monitor_thread = None
        self.update_interval = 10
        self.portfolio_update_interval = 60
        self.last_portfolio_update = 0
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Portfolio monitoring started")

    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Portfolio monitoring stopped")

    def _monitor_loop(self):
        while self.monitoring:
            try:
                current_time = time.time()
                if current_time - self.last_portfolio_update > self.portfolio_update_interval:
                    self._update_portfolio_value()
                    self.last_portfolio_update = current_time
                if self.risk_manager.is_trading_halted():
                    time.sleep(self.update_interval)
                    continue
                self._check_positions()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(self.update_interval)

    def _update_portfolio_value(self):
        try:
            # Get real account value
            account_value = self.ibkr_client.get_account_value()
            if account_value > 0:
                self.risk_manager.update_portfolio_value(account_value)
                self.logger.info(f"Portfolio value updated: ${account_value:,.2f}")
        except Exception as e:
            self.logger.error(f"Failed to update portfolio value: {e}")

    def _check_positions(self):
        """Check all positions for exit conditions"""
        try:
            # Get current positions from IBKR
            positions = self.ibkr_client.get_positions()
            
            for position in positions:
                try:
                    symbol = position.contract.symbol
                    position_size = position.position
                    
                    # Skip if not an option position
                    if position.contract.secType not in ['OPT', 'BAG']:
                        continue
                    
                    # Get or store entry price
                    position_id = f"{symbol}_{position.contract.conId}"
                    if position_id not in self.position_entry_prices:
                        # Use average cost as entry price
                        self.position_entry_prices[position_id] = position.avgCost
                        self.logger.info(f"Tracking new position: {symbol} at ${position.avgCost:.2f}")
                    
                    entry_price = self.position_entry_prices[position_id]
                    
                    # Get current market value per unit
                    current_value = position.marketValue / abs(position.position) if position.position != 0 else 0
                    
                    # Determine trade type from position
                    trade_type = self._determine_trade_type(position)
                    
                    # Check exit conditions
                    should_exit, exit_reason = self.risk_manager.check_exit_conditions(
                        position_id, 
                        entry_price, 
                        current_value, 
                        trade_type
                    )
                    
                    if should_exit:
                        self.logger.info(f"🚨 Exit signal for {symbol}: {exit_reason}")
                        self._close_position(position, exit_reason)
                        
                        # Clean up tracking
                        self.risk_manager.cleanup_trade(position_id)
                        del self.position_entry_prices[position_id]
                    else:
                        # Log position status
                        pnl_pct = ((current_value - entry_price) / entry_price) * 100 if entry_price != 0 else 0
                        self.logger.debug(f"Position {symbol}: PnL {pnl_pct:.1f}%, Status: {exit_reason}")
                        
                except Exception as e:
                    self.logger.error(f"Error checking position {position.contract.symbol}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in position check: {e}")

    def _determine_trade_type(self, position) -> str:
        """Determine if position is bull, bear, or volatile based on contract type"""
        if position.contract.secType == 'BAG':
            # For combo orders, check the legs
            if hasattr(position.contract, 'comboLegs') and position.contract.comboLegs:
                # Simple heuristic: if buying calls or selling puts = bullish
                # If buying puts or selling calls = bearish
                # Mixed = volatile
                return 'bull'  # Default for now
        elif position.contract.secType == 'OPT':
            # Single option - determine by right and action
            if position.contract.right == 'C' and position.position > 0:
                return 'bull'
            elif position.contract.right == 'P' and position.position > 0:
                return 'bear'
        
        return 'volatile'  # Default

    def _close_position(self, position, reason: str):
        """Close a position"""
        try:
            # Create closing order
            from ib_insync import MarketOrder, Order
            
            # Determine action (opposite of current position)
            action = 'SELL' if position.position > 0 else 'BUY'
            quantity = abs(position.position)
            
            # Create market order for immediate execution
            order = MarketOrder(
                action=action,
                totalQuantity=quantity
            )
            
            # Place the closing order
            self.logger.info(f"Placing closing order for {position.contract.symbol}: {action} {quantity}")
            trade = self.ibkr_client.ib.placeOrder(position.contract, order)
            
            # Log the exit
            self.logger.info(f"✅ Position closed for {position.contract.symbol} - Reason: {reason}")
            
            # If it was a loss, update daily loss tracking
            if reason == 'stop_loss':
                loss = position.unrealizedPNL if hasattr(position, 'unrealizedPNL') else 0
                if loss < 0:
                    self.risk_manager.update_daily_loss(abs(loss))
                    
        except Exception as e:
            self.logger.error(f"Error closing position {position.contract.symbol}: {e}")

    def is_monitoring(self) -> bool:
        """Return the current monitoring status."""
        return self.monitoring
