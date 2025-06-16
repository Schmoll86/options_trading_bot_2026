#!/usr/bin/env python3
"""
Options Trading Bot 2026 - Synchronous Version with Web Monitor
Complete bot with all components including web interface
"""

import logging
import time
import sys
import signal
import threading
from datetime import datetime
import random
from async_handler_2026 import create_sync_ibkr_client
from thread_safe_ibkr_wrapper import ThreadSafeIBKRWrapper
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
from web_monitor_2026.monitor_server import BotMonitorServer


class OptionsTradingBot2026:
    """Main trading bot class with web monitor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = None
        self.base_ibkr_client = None  # Base client for main thread
        self.ibkr_client = None  # Thread-safe wrapper
        self.portfolio_provider = None
        self.risk_manager = None
        self.portfolio_monitor = None
        self.strategies = []
        self.news_analyzer = None
        self.stock_screener = None
        self.execution_engine = None
        self.web_monitor = None
        self.web_thread = None
        
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
            self.logger.info("Initializing trading bot with web monitor...")
            
            # Load configuration
            config_loader = ConfigLoader2026()
            self.config = config_loader.get_all_config()
            self.logger.info("Configuration loaded")
            
            # Generate a unique client ID to avoid conflicts
            # Use timestamp modulo 1000 plus random to ensure uniqueness
            base_client_id = self.config.get('IBKR_CLIENT_ID', 1)
            unique_client_id = (int(time.time()) % 900) + 100 + random.randint(0, 99)
            
            self.logger.info(f"Using dynamic client ID: {unique_client_id}")
            
            # Initialize IBKR client with sync wrapper
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    base_client = create_sync_ibkr_client(
                        host=self.config['IBKR_HOST'],
                        port=self.config['IBKR_PORT'],
                        client_id=unique_client_id
                    )
                    
                    # Connect to IBKR
                    base_client.connect()
                    self.logger.info("Connected to IBKR Gateway")
                    break
                    
                except Exception as e:
                    if "client id is already in use" in str(e):
                        # Try with a different client ID
                        unique_client_id = (int(time.time()) % 900) + 100 + random.randint(0, 99)
                        self.logger.warning(f"Client ID conflict, retrying with ID {unique_client_id}")
                        time.sleep(2)
                    else:
                        raise e
            else:
                raise Exception("Failed to connect after multiple attempts")
            
            # Keep reference to base client for processing requests
            self.base_ibkr_client = base_client
            
            # Wrap with thread-safe wrapper for other threads
            self.ibkr_client = ThreadSafeIBKRWrapper(base_client)
            
            # Wait for connection to stabilize
            time.sleep(2)  # Reduced from 10 seconds
            
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
            
            # Initialize portfolio monitor
            self.portfolio_monitor = PortfolioMonitor2026(
                risk_manager=self.risk_manager,
                ibkr_client=self.ibkr_client
            )
            
            # Initialize strategies
            self.strategies = [
                BullModule2026(self.ibkr_client, self.portfolio_provider),
                BearModule2026(self.ibkr_client, self.portfolio_provider),
                VolatileModule2026(self.ibkr_client, self.portfolio_provider)
            ]
            self.logger.info("Strategy modules initialized")
            
            # Initialize news analyzer
            self.news_analyzer = NewsHandler2026(self.ibkr_client)
            
            # Initialize stock screener
            self.stock_screener = StockScreener2026(
                ibkr_client=self.ibkr_client,
                portfolio_provider=self.portfolio_provider
            )
            self.logger.info("News handler and stock screener initialized")
            
            # Initialize execution engine
            engine_config = {
                **self.config,
                'ANALYSIS_INTERVAL': 60  # Run analysis every minute for more opportunities
            }
            self.execution_engine = SyncExecutionEngine2026(
                config=engine_config,
                ibkr_client=self.ibkr_client,
                strategies=self.strategies,
                news_analyzer=self.news_analyzer,
                stock_screener=self.stock_screener,
                web_monitor=None  # Will be set after web monitor is created
            )
            self.logger.info("Execution engine initialized")
            
            # Initialize web monitor (only takes bot_instance and port)
            self.web_monitor = BotMonitorServer(
                bot_instance=self,
                port=5001
            )
            
            # Now set the web monitor reference in execution engine
            self.execution_engine.web_monitor = self.web_monitor
            
            # Start web monitor in a separate thread
            self.web_thread = threading.Thread(target=self._run_web_monitor, daemon=True)
            self.web_thread.start()
            self.logger.info("Web monitor started at http://localhost:5001")
                
            self.running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing trading bot: {e}", exc_info=True)
            return False
            
    def _run_web_monitor(self):
        """Run web monitor in a separate thread"""
        try:
            self.web_monitor.start_server()
        except Exception as e:
            self.logger.error(f"Error in web monitor: {e}")
            # Don't let web monitor errors crash the bot
            return
            
    def run(self):
        """Main bot loop"""
        self.logger.info("Trading bot started")
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 Options Trading Bot 2026 is now LIVE!")
        self.logger.info("📊 Web Monitor: http://localhost:5001")
        self.logger.info("💰 Account Value: ${:,.2f}".format(
            self.ibkr_client.get_account_value()
        ))
        self.logger.info("⏰ Market Hours: 9:30 AM - 4:00 PM ET")
        self.logger.info("="*60 + "\n")
        
        # Start portfolio monitoring
        self.portfolio_monitor.start_monitoring()
        
        # Start execution engine
        self.execution_engine.start()
        
        try:
            while self.running:
                # Process any pending requests from other threads
                if self.ibkr_client:
                    self.ibkr_client._process_requests()
                
                # Main loop - the execution engine handles the trading logic
                time.sleep(0.1)  # Reduced from 1 second for better responsiveness
                
                # Update web monitor periodically
                if int(time.time()) % 10 == 0:  # Every 10 seconds
                    try:
                        self._update_web_monitor()
                    except Exception as e:
                        self.logger.error(f"Error updating web monitor: {e}")
                        # Don't let web monitor errors crash the bot
                        continue
                
                # Check if we're still connected
                if not self.ibkr_client.connected:
                    self.logger.error("Lost connection to IBKR")
                    # Try to reconnect instead of breaking
                    try:
                        self.base_ibkr_client.connect()
                        self.logger.info("Reconnected to IBKR")
                    except Exception as e:
                        self.logger.error(f"Failed to reconnect to IBKR: {e}")
                        time.sleep(30)  # Wait before retrying
                        continue
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            # Don't let errors crash the bot
            time.sleep(30)  # Wait before retrying
            return self.run()  # Restart the bot
        finally:
            self.shutdown()
            
    def _update_web_monitor(self):
        """Update web monitor with current data"""
        try:
            # Update portfolio value
            portfolio_value = self.ibkr_client.get_account_value()
            self.web_monitor.update_portfolio_value(portfolio_value)
            
            # Update bot status
            self.web_monitor.update_bot_status("Running")
            
            # Update health metrics
            health_data = {
                'ibkr_connection': self.ibkr_client.connected,
                'portfolio_monitor': self.portfolio_monitor.is_monitoring(),
                'execution_engine': self.execution_engine.running,
                'risk_manager': True,
                'news_handler': True,
                'stock_screener': True
            }
            self.web_monitor.update_health_status(health_data)
            
            # Update risk metrics
            risk_metrics = self.risk_manager.get_risk_summary() if self.risk_manager else {}
            self.web_monitor.update_risk_metrics(risk_metrics)
            
        except Exception as e:
            self.logger.error(f"Error updating web monitor: {e}")
            
    def shutdown(self):
        """Shutdown all bot components"""
        self.logger.info("Shutting down trading bot...")
        self.running = False
        
        # Update web monitor status
        if self.web_monitor:
            self.web_monitor.update_bot_status("Stopped")
        
        # Stop components in reverse order
        if self.portfolio_monitor:
            self.portfolio_monitor.stop_monitoring()
            
        if self.execution_engine:
            self.execution_engine.stop()
            
        if self.web_monitor:
            self.web_monitor.stop_server()
            
        if self.base_ibkr_client:
            # Disconnect using the base client
            if hasattr(self.base_ibkr_client, 'disconnect'):
                self.base_ibkr_client.disconnect()
            
        self.logger.info("Trading bot shutdown complete")
        
    # Methods required by web monitor
    async def get_portfolio_value(self):
        """Get portfolio value for web monitor"""
        return self.ibkr_client.get_account_value() if self.ibkr_client else 0
        
    async def get_active_trades(self):
        """Get active trades for web monitor"""
        if self.execution_engine:
            return list(self.execution_engine.active_positions.values())
        return []
        
    async def get_risk_metrics(self):
        """Get risk metrics for web monitor"""
        if self.risk_manager:
            return self.risk_manager.get_risk_summary()
        return {}
        
    async def get_health_status(self):
        """Get health status for web monitor"""
        return {
            'ibkr_connection': self.ibkr_client.connected if self.ibkr_client else False,
            'portfolio_monitor': self.portfolio_monitor.is_monitoring() if self.portfolio_monitor else False,
            'execution_engine': self.execution_engine.running if self.execution_engine else False,
            'risk_manager': True if self.risk_manager else False,
            'news_handler': True if self.news_analyzer else False,
            'stock_screener': True if self.stock_screener else False
        }


def setup_logging():
    """Configure logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
        format=log_format,
        handlers=[
            logging.FileHandler('options_bot_2026_live.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Reduce noise from some modules
    logging.getLogger('ib_insync').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)


def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🚀 OPTIONS TRADING BOT 2026 - LIVE MODE")
    print("="*60)
    print("Starting at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60 + "\n")
    
    bot = OptionsTradingBot2026()
    
    if bot.initialize():
        bot.run()
    else:
        logger.error("Bot initialization failed")
        bot.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main() 