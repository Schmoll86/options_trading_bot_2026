# config_2026/config_loader.py
import os
from dotenv import load_dotenv
import logging

class ConfigLoader2026:
    """Configuration loader for Options Trading Bot 2026"""

    def __init__(self, env_file='.env'):
        self.logger = logging.getLogger(__name__)

        # Load environment variables - force override existing ones
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            self.logger.info(f"Loaded configuration from {env_file}")
        else:
            self.logger.warning(f"Environment file {env_file} not found")

    def get(self, key: str, default=None):
        """Get configuration value"""
        value = os.getenv(key, default)

        # Convert to appropriate type
        if isinstance(default, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        elif isinstance(default, float):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        elif isinstance(default, bool):
            return str(value).lower() in ('true', '1', 'yes', 'on')

        return value

    def get_all_config(self):
        """Get all configuration as dictionary"""
        return {
            'IBKR_HOST': self.get('IBKR_HOST', '127.0.0.1'),
            'IBKR_PORT': self.get('IBKR_PORT', 4001),
            'IBKR_CLIENT_ID': self.get('IBKR_CLIENT_ID', 1),
            'INITIAL_PORTFOLIO_VALUE': self.get('INITIAL_PORTFOLIO_VALUE', 10000),
            'MAX_DAILY_LOSS': self.get('MAX_DAILY_LOSS', 1000),
            'MAX_CONCURRENT_TRADES': self.get('MAX_CONCURRENT_TRADES', 5),
            'CYCLE_INTERVAL_SECONDS': self.get('CYCLE_INTERVAL_SECONDS', 30),
            'MAX_TRADE_SIZE_PCT': self.get('MAX_TRADE_SIZE_PCT', 0.10),
            'LOG_LEVEL': self.get('LOG_LEVEL', 'INFO')
        }


def load_config():
    """Load configuration - convenience function"""
    return ConfigLoader2026().get_all_config()
