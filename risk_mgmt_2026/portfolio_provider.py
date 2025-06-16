# risk_mgmt_2026/portfolio_provider.py
from typing import Dict

class PortfolioProvider2026:
    """Provides portfolio data to strategy modules"""

    def __init__(self, risk_manager):
        self.risk_manager = risk_manager

    def get_available_capital(self) -> float:
        """Get available capital for new trades"""
        return self.risk_manager.calculate_max_trade_size()

    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        return self.risk_manager.get_portfolio_value()

    def can_trade(self, trade_size: float) -> bool:
        """Check if trade is allowed"""
        if self.risk_manager.is_trading_halted():
            return False
        return self.risk_manager.validate_trade_size(trade_size)

    def get_risk_limits(self) -> Dict:
        """Get current risk limits for strategy modules"""
        return {
            'max_trade_size': self.risk_manager.calculate_max_trade_size(),
            'portfolio_value': self.risk_manager.get_portfolio_value(),
            'trading_halted': self.risk_manager.is_trading_halted(),
            'daily_loss': self.risk_manager.daily_loss,
            'daily_limit': self.risk_manager.daily_loss_limit
        }
