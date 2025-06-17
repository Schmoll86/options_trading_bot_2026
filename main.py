# main.py
import logging
import asyncio
from ibkr_client_2026.client import IBKRClient2026
from config_2026.config_loader import ConfigLoader2026
from risk_mgmt_2026.risk_manager import RiskManager2026
from risk_mgmt_2026.portfolio_monitor import PortfolioMonitor2026
from execution_engine_2026.engine import ExecutionEngine2026
from web_monitor_2026.monitor_server import BotMonitorServer
from risk_mgmt_2026.portfolio_provider import PortfolioProvider2026
from bull_module_2026.bull import BullModule2026
from bear_module_2026.bear import BearModule2026
from volatile_module_2026.volatile import VolatileModule2026
from news_handler_2026.news import NewsHandler2026
from stock_screener_2026.screener import StockScreener2026
import signal
import sys
from datetime import datetime

class OptionsTradingBot2026:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Initialize components
        self.config = None
        self.ibkr_client = None
        self.risk_manager = None
        self.portfolio_provider = None
        self.portfolio_monitor = None
        self.bull_module = None
        self.bear_module = None
        self.volatile_module = None
        self.news_handler = None
        self.stock_screener = None
        self.execution_engine = None
        
        # Initialize web monitor
        self.web_monitor = None
        
        # Initialize market sentiment tracking
        self.current_sentiment = {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'volatility_expected': 0.0,
            'bullish': False,
            'bearish': False,
            'volatile': False,
            'neutral': True,
            'sector_sentiment': {},
            'news_factors': {},
            'technical_sentiment': {},
            'timestamp': datetime.now().isoformat(),
            'data_sources': []
        }
        
        # Initialize error tracking
        self.error_counts = {
            'ibkr_connection': 0,
            'trading_cycle': 0,
            'monitor_update': 0
        }
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        
        # Set up signal handlers
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

    async def start_trading(self):
        """Start the trading bot"""
        try:
            self.logger.info("Starting trading bot...")
            self.running = True
            
            while self.running:
                try:
                    if not await self.check_component_health():
                        self.logger.error("Component health check failed")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    await self.execution_engine.run_trading_cycle()
                    await self.update_monitor()
                    
                    # Sleep for the configured interval
                    await asyncio.sleep(self.config.get('trading_cycle_interval', 300))
                    
                except Exception as e:
                    self.error_counts['trading_cycle'] += 1
                    self.logger.error(f"Error in trading cycle: {e}")
                    if self.error_counts['trading_cycle'] >= self.max_retries:
                        self.logger.error("Max retries exceeded, stopping bot")
                        await self.shutdown()
                        break
                    await asyncio.sleep(self.retry_delay)
                    
        except Exception as e:
            self.logger.error(f"Fatal error in trading bot: {e}")
            await self.shutdown()

    async def get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        try:
            return await self.ibkr_client.get_account_value()
        except Exception as e:
            self.logger.error(f"Error getting portfolio value: {e}")
            return 0.0

    async def get_active_trades(self) -> list:
        """Get list of active trades"""
        try:
            # TODO: Implement get_active_trades in portfolio monitor
            return []
        except Exception as e:
            self.logger.error(f"Error getting active trades: {e}")
            return []

    async def get_risk_metrics(self) -> dict:
        """Get current risk metrics"""
        try:
            portfolio_value = await self.get_portfolio_value()
            active_trades = await self.get_active_trades()
            
            return {
                'portfolio_value': portfolio_value,
                'daily_pnl': 0.0,  # TODO: Implement
                'total_pnl': 0.0,  # TODO: Implement
                'position_count': len(active_trades),
                'risk_exposure': 0.0,  # TODO: Implement
                'volatility_metrics': {},  # TODO: Implement
                'sector_exposure': {}  # TODO: Implement
            }
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {}

    async def get_health_status(self) -> dict:
        """Get health status of all components"""
        try:
            return {
                'ibkr_connection': self.ibkr_client.connected if self.ibkr_client else False,
                'portfolio_monitor': self.portfolio_monitor.is_monitoring() if self.portfolio_monitor else False,
                'execution_engine': self.execution_engine.is_running() if self.execution_engine else False,
                'risk_manager': True if self.risk_manager else False,
                'news_handler': True if self.news_handler else False,
                'stock_screener': True if self.stock_screener else False
            }
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'ibkr_connection': False,
                'portfolio_monitor': False,
                'execution_engine': False,
                'risk_manager': False,
                'news_handler': False,
                'stock_screener': False
            }

    async def update_monitor(self):
        """Update the web monitor with current status"""
        try:
            if not self.web_monitor:
                return
            
            # Get current portfolio value
            portfolio_value = await self.get_portfolio_value()
            
            # Get active trades
            active_trades = await self.get_active_trades()
            
            # Get risk metrics
            risk_metrics = await self.get_risk_metrics()
            
            # Get health status
            health_status = await self.get_health_status()
            
            # Update monitor
            self.web_monitor.update_portfolio_value(portfolio_value)
            self.web_monitor.update_active_trades(active_trades)
            self.web_monitor.update_risk_metrics(risk_metrics)
            self.web_monitor.update_health_status(health_status)
            self.web_monitor.update_market_sentiment(self.current_sentiment)
            
        except Exception as e:
            self.error_counts['monitor_update'] += 1
            self.logger.error(f"Error updating monitor: {e}")

    async def shutdown(self):
        """Shutdown the trading bot gracefully"""
        self.logger.info("Shutting down trading bot...")
        self.running = False
        
        try:
            # Stop portfolio monitoring
            if self.portfolio_monitor:
                self.portfolio_monitor.stop_monitoring()
            
            # Stop execution engine
            if self.execution_engine:
                self.execution_engine.stop()
            
            # Stop web monitor
            if self.web_monitor:
                self.web_monitor.stop_server()
            
            # Disconnect from IBKR
            if self.ibkr_client:
                await self.ibkr_client.disconnect()
            
            self.logger.info("Trading bot shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def initialize(self):
        """Initialize all components of the trading bot"""
        try:
            self.logger.info("Initializing trading bot...")
            
            # Load configuration
            self.config = ConfigLoader2026()
            self.logger.info("Configuration loaded")
            
            # Initialize IBKR client
            self.ibkr_client = IBKRClient2026(
                host=self.config.get('ibkr_host', '127.0.0.1'),
                port=self.config.get('ibkr_port', 4001),
                client_id=self.config.get('ibkr_client_id', 1)
            )
            await self.ibkr_client.connect()
            self.logger.info("Connected to IBKR Gateway")
            
            # Initialize risk management with real portfolio value (live account) and config
            portfolio_val = await self.ibkr_client.get_account_value()
            self.risk_manager = RiskManager2026(portfolio_val, config=self.config.get_all_config())
            self.portfolio_provider = PortfolioProvider2026(self.risk_manager)
            self.portfolio_monitor = PortfolioMonitor2026(self.risk_manager, self.ibkr_client)
            self.logger.info("Risk management initialized")
            
            # Initialize strategy modules
            self.bull_module = BullModule2026(self.ibkr_client, self.portfolio_provider)
            self.bear_module = BearModule2026(self.ibkr_client, self.portfolio_provider)
            self.volatile_module = VolatileModule2026(self.ibkr_client, self.portfolio_provider)
            self.logger.info("Strategy modules initialized")
            
            # Initialize news handler and stock screener
            self.news_handler = NewsHandler2026(self.ibkr_client)
            self.stock_screener = StockScreener2026(self.ibkr_client, self.portfolio_provider)
            self.logger.info("News handler and stock screener initialized")
            
            # Initialize execution engine
            self.execution_engine = ExecutionEngine2026(
                self.ibkr_client,
                self.risk_manager,
                self.bull_module,
                self.bear_module,
                self.volatile_module,
                self.news_handler,
                self.stock_screener
            )
            await self.execution_engine.start()
            self.logger.info("Execution engine initialized")
            
            # Start portfolio monitoring
            await self.portfolio_monitor.start_monitoring()
            self.logger.info("Portfolio monitoring started")
            
            # Initialize web monitor
            self.web_monitor = BotMonitorServer(
                bot_instance=self,
                port=self.config.get('web_monitor_port', 5001)
            )
            self.web_monitor.start_server()
            self.logger.info(f"Web monitor started on port {self.config.get('web_monitor_port', 5001)}")
            
            # Update initial health status
            health_status = await self.get_health_status()
            self.web_monitor.update_health_status(health_status)
            
            self.logger.info("Trading bot initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing trading bot: {e}")
            await self.shutdown()
            return False

async def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='options_bot_2026.log',
        filemode='a'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # Create the bot
    bot = OptionsTradingBot2026()
    
    try:
        # Initialize the bot
        success = await bot.initialize()
        if not success:
            logging.error("Bot initialization failed")
            return
        
        # Start trading
        await bot.start_trading()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        await bot.shutdown()

if __name__ == "__main__":
    # Use asyncio.run() which properly manages the event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
