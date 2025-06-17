# risk_mgmt_2026/risk_manager.py
import logging
from typing import Dict, Tuple, Any
from datetime import date
import threading
import asyncio

class RiskManager2026:
    """Centralised risk-management for live trading.

    Notes
    -----
    1.  ExecutionEngine expects the following API:
        • can_open_position(symbol)
        • check_risk_exposure(opportunity_dict)
        • check_volatility_limits(opportunity_dict)
        • get_risk_metrics()

    2.  The constructor historically accepted a *float* `portfolio_value`, but
        the bot initialiser was passing an `IBKRClient2026` instance instead.
        We now accept *either* and resolve appropriately so that existing
        call-sites do not break.  When an `IBKRClient2026` is supplied we pull
        NetLiquidation asynchronously (blocking the loop for a short moment
        is acceptable at start-up).
    """

    def __init__(self, portfolio_source, config=None):
        # Deferred import to avoid circular deps when portfolio_source is IBKR
        from ibkr_client_2026.client import IBKRClient2026

        if isinstance(portfolio_source, (int, float)):
            self.portfolio_value: float = float(portfolio_source)
        elif isinstance(portfolio_source, IBKRClient2026):
            # Blocking call is fine inside __init__ (runs in bot init phase)
            loop = asyncio.get_event_loop()
            # In case __init__ is invoked outside an event loop use run_until_complete
            if loop.is_running():
                # Synchronous helper
                self.portfolio_value = loop.run_until_complete(
                    portfolio_source.get_account_value())
            else:
                self.portfolio_value = asyncio.run(
                    portfolio_source.get_account_value())
        else:
            raise ValueError("RiskManager2026 requires either a float portfolio value or an IBKRClient2026 instance")

        # Use config value if provided, otherwise default to 10%
        self.max_trade_size_pct = config.get('MAX_TRADE_SIZE_PCT', 0.10) if config else 0.10
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

        # Track currently open positions by symbol so we can prevent duplicates
        self._open_symbols = set()

    def update_portfolio_value(self, new_value: float):
        with self._lock:
            self.portfolio_value = new_value
            self.logger.info(f"Portfolio value updated: ${new_value:,.2f}")

    def get_portfolio_value(self) -> float:
        return self.portfolio_value

    def calculate_max_trade_size(self) -> float:
        """Calculate maximum allowed trade size based on risk limits"""
        # Use configured trade size percentage (default 10% if not set)
        max_per_trade = self.portfolio_value * self.max_trade_size_pct
        
        # Reduce if we're approaching daily loss limit
        remaining_daily_budget = self.daily_loss_limit - abs(self.daily_loss)
        if remaining_daily_budget < max_per_trade:
            max_per_trade = max(0, remaining_daily_budget * 0.5)  # Use 50% of remaining budget
            
        return max_per_trade

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
        """Check if trading should be halted due to risk conditions"""
        # Halt if daily loss limit exceeded
        if abs(self.daily_loss) >= self.daily_loss_limit:
            return True
            
        # Halt if portfolio value dropped too much (20% drawdown from initial value)
        initial_value = getattr(self, 'initial_portfolio_value', self.portfolio_value)
        if self.portfolio_value < initial_value * 0.8:
            return True
            
        return False

    def cleanup_trade(self, trade_id: str):
        with self._lock:
            self.trailing_stops.pop(trade_id, None)
            self.highest_profits.pop(trade_id, None)

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary for monitoring"""
        return {
            'portfolio_value': self.portfolio_value,
            'daily_loss': self.daily_loss,
            'daily_loss_limit': self.daily_loss_limit,
            'max_trade_size': self.calculate_max_trade_size(),
            'trading_halted': self.is_trading_halted(),
            'open_positions': len(self._open_symbols),
            'risk_level': 'HIGH' if self.daily_loss > self.daily_loss_limit * 0.8 else 'NORMAL'
        }

    # ------------------------------------------------------------------
    # Interfaces required by ExecutionEngine2026
    # ------------------------------------------------------------------

    def can_open_position(self, symbol: str) -> bool:
        """Return True if a new position in *symbol* is allowed under current
        risk limits (no trading halt, position not already open, etc.)."""
        if self.trading_halted:
            self.logger.warning("Trading currently halted – rejecting new position for %s", symbol)
            return False
        if symbol in self._open_symbols:
            # Simple duplicate-prevention; multi-leg spreads per symbol count as one.
            self.logger.info("Position for %s already open – skipping duplicate", symbol)
            return False
        return True

    def check_risk_exposure(self, opportunity: Dict) -> bool:
        """Validate that the theoretical *max loss* of the opportunity is within
        per-trade sizing limits."""
        try:
            pct_cap = self.max_trade_size_pct
            max_portfolio_risk = self.portfolio_value * pct_cap

            max_loss = opportunity.get('max_loss')
            quantity = opportunity.get('position_size', 1)
            # options are quoted per share – multiply by 100 to get contract value
            if max_loss is None:
                # Fall back to debit cost if max_loss not present
                max_loss = opportunity.get('debit', 0)
            trade_risk = float(max_loss) * quantity * 100

            if trade_risk > max_portfolio_risk:
                self.logger.warning(
                    "Trade risk $%.2f exceeds %.0f%% of portfolio ($%.2f) – REJECTED",
                    trade_risk, pct_cap*100, max_portfolio_risk)
                return False
            return True
        except Exception as e:
            self.logger.error("Error during risk exposure check: %s", e)
            return False

    def check_volatility_limits(self, opportunity: Dict) -> bool:
        """Placeholder – real implementation might, e.g., block trades when IV is
        outside acceptable bands.  For now we simply return True."""
        return True

    def get_risk_metrics(self) -> Dict:
        """Light-weight metrics snapshot used by ExecutionEngine and web UI."""
        return {
            'portfolio_value': self.portfolio_value,
            'max_trade_size': self.calculate_max_trade_size(),
            'daily_loss': self.daily_loss,
            'daily_loss_limit': self.daily_loss_limit,
            'trading_halted': self.trading_halted
        }

    # ------------------------------------------------------------------
    # Utility methods for ExecutionEngine to keep _open_symbols updated
    # ------------------------------------------------------------------

    def register_open_position(self, symbol: str):
        with self._lock:
            self._open_symbols.add(symbol)

    def unregister_closed_position(self, symbol: str):
        with self._lock:
            self._open_symbols.discard(symbol)
