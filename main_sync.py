#!/usr/bin/env python3
"""
Options Trading Bot 2026 - Synchronous Main Entry Point
This version uses synchronous code throughout for better stability
"""

import logging
import time
import sys
import signal
from datetime import datetime
from async_handler_2026 import create_sync_ibkr_client
from config_2026.config_loader import ConfigLoader2026
from risk_mgmt_2026.risk_manager import RiskManager2026
from risk_mgmt_2026.portfolio_provider import PortfolioProvider2026
from risk_mgmt_2026.portfolio_monitor import PortfolioMonitor2026
from bull_module_2026.bull import BullModule2026
from bear_module_2026.bear import BearModule2026
from volatile_module_2026.volatile import VolatileModule2026
from news_handler_2026.news import NewsHandler2026
from stock_screener_2026.screener import StockScreener2026
from execution_engine_2026.sync_engine import SyncExecutionEngine2026


class OptionsTradingBot2026:
    """Main trading bot class - fully synchronous"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = None
        self.ibkr_client = None
        self.portfolio_provider = None
        self.risk_manager = None
        self.portfolio_monitor = None
        self.strategies = []
        self.news_analyzer = None
        self.stock_screener = None
        self.execution_engine = None
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    def initialize(self):
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing trading bot...")
            
            # Load configuration
            config_loader = ConfigLoader2026()
            self.config = config_loader.get_all_config()
            self.logger.info("Configuration loaded")
            
            # Initialize IBKR client with sync wrapper
            self.ibkr_client = create_sync_ibkr_client(
                host=self.config['IBKR_HOST'],
                port=self.config['IBKR_PORT'],
                client_id=self.config['IBKR_CLIENT_ID']
            )
            
            # Connect to IBKR
            self.ibkr_client.connect()
            self.logger.info("Connected to IBKR Gateway")
            
            # Wait for connection to stabilize
            time.sleep(1)
            
            # Verify connection
            account_value = self.ibkr_client.get_account_value()
            self.logger.info(f"Account value: ${account_value:,.2f}")
            
            # Initialize portfolio provider
            self.portfolio_provider = PortfolioProvider2026(self.ibkr_client)
            
            # Initialize risk manager with portfolio value
            self.risk_manager = RiskManager2026(
                portfolio_value=account_value if account_value > 0 else self.config.get('INITIAL_PORTFOLIO_VALUE', 10000)
            )
            self.logger.info("Risk management initialized")
            
            # Initialize portfolio monitor (only needs risk_manager and ibkr_client)
            self.portfolio_monitor = PortfolioMonitor2026(
                risk_manager=self.risk_manager,
                ibkr_client=self.ibkr_client
            )
            
            # Initialize strategies (bull/bear/volatile modules need ibkr_client and portfolio_provider)
            self.strategies = [
                BullModule2026(self.ibkr_client, self.portfolio_provider),
                BearModule2026(self.ibkr_client, self.portfolio_provider),
                VolatileModule2026(self.ibkr_client, self.portfolio_provider)
            ]
            self.logger.info("Strategy modules initialized")
            
            # Initialize news analyzer (only needs ibkr_client)
            self.news_analyzer = NewsHandler2026(self.ibkr_client)
            
            # Initialize stock screener (needs ibkr_client and portfolio_provider)
            self.stock_screener = StockScreener2026(
                ibkr_client=self.ibkr_client,
                portfolio_provider=self.portfolio_provider
            )
            self.logger.info("News handler and stock screener initialized")
            
            # Initialize execution engine (sync version)
            self.execution_engine = SyncExecutionEngine2026(
                config=self.config,
                ibkr_client=self.ibkr_client,
                strategies=self.strategies,
                news_analyzer=self.news_analyzer,
                stock_screener=self.stock_screener
            )
            self.logger.info("Execution engine initialized")
            
            # Note: Web monitor has a different structure, so we'll skip it for now
            self.logger.info("Web monitor disabled for sync version")
                
            self.running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing trading bot: {e}", exc_info=True)
            return False
            
    def run(self):
        """Main bot loop"""
        self.logger.info("Trading bot started")
        
        # Start portfolio monitoring
        self.portfolio_monitor.start_monitoring()
        
        # Start execution engine
        self.execution_engine.start()
        
        try:
            while self.running:
                # Main loop - the execution engine handles the trading logic
                time.sleep(1)
                
                # Check if we're still connected
                if not self.ibkr_client.connected:
                    self.logger.error("Lost connection to IBKR")
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Shutdown all bot components"""
        self.logger.info("Shutting down trading bot...")
        self.running = False
        
        # Stop components in reverse order
        if self.portfolio_monitor:
            self.portfolio_monitor.stop_monitoring()
            
        if self.execution_engine:
            self.execution_engine.stop()
            
        if self.ibkr_client:
            self.ibkr_client.disconnect()
            
        self.logger.info("Trading bot shutdown complete")


def setup_logging():
    """Configure logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('options_bot_2026_sync.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Options Trading Bot 2026 (Synchronous Version)")
    logger.info(f"Starting at {datetime.now()}")
    logger.info("="*60)
    
    bot = OptionsTradingBot2026()
    
    if bot.initialize():
        bot.run()
    else:
        logger.error("Bot initialization failed")
        bot.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main() 