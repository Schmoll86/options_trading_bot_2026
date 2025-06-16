# risk_mgmt_2026/risk_manager.py
import logging
from typing import Dict, Tuple
from datetime import date
import threading

class RiskManager2026:
    """Simplified risk management with conditional trailing stops"""

    def __init__(self, portfolio_value: float):
        self.portfolio_value = portfolio_value
        self.max_trade_size_pct = 0.10
        self.stop_loss_pct = {
            'bull': 0.20,
            'bear': 0.15,
            'volatile': 0.30
        }
        self.trailing_stop_threshold = 0.80
        self.trailing_stop_pct = 0.08
        self.take_profit_pct = 0.30
        self.daily_loss_limit = 1000
        self.daily_loss = 0
        self.trading_halted = False
        self.current_date = date.today()
        self.trailing_stops = {}
        self.highest_profits = {}
        self._lock = threading.Lock()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def update_portfolio_value(self, new_value: float):
        with self._lock:
            self.portfolio_value = new_value
            self.logger.info(f"Portfolio value updated: ${new_value:,.2f}")

    def get_portfolio_value(self) -> float:
        return self.portfolio_value

    def calculate_max_trade_size(self) -> float:
        return self.portfolio_value * self.max_trade_size_pct

    def validate_trade_size(self, trade_size: float) -> bool:
        max_size = self.calculate_max_trade_size()
        is_valid = trade_size <= max_size
        if not is_valid:
            self.logger.warning(f"Trade size ${trade_size:,.2f} exceeds limit ${max_size:,.2f}")
        return is_valid

    def check_exit_conditions(self, trade_id: str, entry_price: float, current_price: float, trade_type: str) -> Tuple[bool, str]:
        profit_pct = (current_price - entry_price) / entry_price
        if profit_pct > 0:
            if profit_pct >= self.trailing_stop_threshold:
                return self._handle_trailing_stop(trade_id, current_price, profit_pct)
            elif profit_pct >= self.take_profit_pct:
                return True, 'take_profit'
        else:
            loss_pct = abs(profit_pct)
            threshold = self.stop_loss_pct.get(trade_type, 0.20)
            if loss_pct >= threshold:
                return True, 'stop_loss'
        return False, 'hold'

    def _handle_trailing_stop(self, trade_id: str, current_price: float, profit_pct: float) -> Tuple[bool, str]:
        with self._lock:
            if trade_id not in self.trailing_stops:
                self.trailing_stops[trade_id] = current_price * (1 - self.trailing_stop_pct)
                self.highest_profits[trade_id] = profit_pct
                return False, 'trailing_active'
            if profit_pct > self.highest_profits[trade_id]:
                self.highest_profits[trade_id] = profit_pct
                new_stop = current_price * (1 - self.trailing_stop_pct)
                if new_stop > self.trailing_stops[trade_id]:
                    self.trailing_stops[trade_id] = new_stop
            if current_price <= self.trailing_stops[trade_id]:
                return True, 'trailing_stop'
            return False, 'trailing_active'

    def update_daily_loss(self, loss_amount: float) -> bool:
        with self._lock:
            if date.today() != self.current_date:
                self.daily_loss = 0
                self.trading_halted = False
                self.current_date = date.today()
            self.daily_loss += loss_amount
            if self.daily_loss >= self.daily_loss_limit and not self.trading_halted:
                self.trading_halted = True
                self.logger.critical(f"CIRCUIT BREAKER: Daily loss ${self.daily_loss:.2f}")
                return True
            return False

    def is_trading_halted(self) -> bool:
        return self.trading_halted

    def cleanup_trade(self, trade_id: str):
        with self._lock:
            self.trailing_stops.pop(trade_id, None)
            self.highest_profits.pop(trade_id, None)

    def get_risk_summary(self) -> Dict:
        return {
            'portfolio_value': self.portfolio_value,
            'max_trade_size': self.calculate_max_trade_size(),
            'daily_loss': self.daily_loss,
            'daily_loss_limit': self.daily_loss_limit,
            'trading_halted': self.trading_halted,
            'active_trailing_stops': len(self.trailing_stops)
        }
