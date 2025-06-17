#!/usr/bin/env python3
"""
Options Trading Bot 2026 - Clean Production Main Entry Point
NO TESTING CODE - Production ready implementation

Architecture: Main entry point that orchestrates all components following proper dependency injection
"""

import sys
import os
import signal
import logging
import time
from typing import Dict, List, Any
import random
import threading

# Add the project directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('options_bot_2026_live.log'),
        logging.StreamHandler()
    ]
)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

class TradingBotMain:
    """
    Main Trading Bot Application - Production Implementation
    
    Architecture: Orchestrates all components with proper dependency injection
    
    Dependency Flow:
    1. Configuration → All components
    2. IBKR Client → Thread-safe wrapper → Async adapter  
    3. Risk Manager → Portfolio Provider
    4. Portfolio Provider → Strategy modules
    5. All components → Execution Engine
    6. Web Monitor → Dashboard
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.ibkr_client = None
        self.thread_safe_client = None
        self.risk_manager = None
        self.portfolio_provider = None
        self.strategies = []
        self.execution_engine = None
        self.web_monitor = None
        
    def initialize(self):
        """Initialize all components with proper dependency injection"""
        try:
            self.logger.info("Initializing trading bot with web monitor...")
            
            # Step 1: Load configuration
            self._load_configuration()
            self.logger.info("Configuration loaded")
            
            # Step 2: Connect to IBKR
            self._connect_to_ibkr()
            self.logger.info("Connected to IBKR Gateway")
            
            # Step 3: Initialize risk management (BEFORE portfolio provider)
            self._initialize_risk_management()
            self.logger.info("Risk management initialized")
            
            # Step 4: Initialize strategy modules (requires portfolio provider)
            self._initialize_strategies()
            self.logger.info("Strategy modules initialized")
            
            # Step 5: Initialize supporting components
            self._initialize_support_components()
            self.logger.info("News handler and stock screener initialized")
            
            # Step 6: Initialize execution engine
            self._initialize_execution_engine()
            self.logger.info("Execution engine initialized")
            
            # Step 7: Initialize web monitor
            self._initialize_web_monitor()
            self.logger.info(f"Web monitor started at http://localhost:5001")
            
            self.logger.info("Trading bot started")
            return True
            
        except Exception as e:
            self.logger.error(f"Bot initialization failed: {e}", exc_info=True)
            return False
    
    def _load_configuration(self):
        """Load configuration from environment and defaults"""
        from config_2026.config_loader import ConfigLoader2026
        
        config_loader = ConfigLoader2026()
        self.config = config_loader.get_all_config()
    
    def _connect_to_ibkr(self):
        """Establish IBKR connection with proper client hierarchy"""
        from async_handler_2026 import create_sync_ibkr_client
        from thread_safe_ibkr_wrapper import ThreadSafeIBKRWrapper
        from async_sync_adapter import AsyncSyncAdapter
        
        # Create unique client ID for this session
        client_id = random.randint(100, 999)
        self.logger.info(f"Using dynamic client ID: {client_id}")
        
        # Layer 1: Core IBKR sync client (NO TESTING CODE)
        self.ibkr_client = create_sync_ibkr_client(
            host=self.config.get('IBKR_HOST', '127.0.0.1'),
            port=self.config.get('IBKR_PORT', 4001),
            client_id=client_id
        )
        self.ibkr_client.connect()
        
        # Wait for connection to stabilize
        time.sleep(2)
        
        # Get account value for risk management
        account_value = self.ibkr_client.get_account_value()
        self.logger.info(f"Account value: ${account_value:,.2f}")
        
        # Layer 2: Thread-safe wrapper (provides calculate_max_trade_size, is_trading_halted)
        self.thread_safe_client = ThreadSafeIBKRWrapper(self.ibkr_client)
        
        # Layer 3: Async-sync adapter (bridges to strategy modules)
        self.async_adapter = AsyncSyncAdapter(self.thread_safe_client)
        
        return account_value
    
    def _initialize_risk_management(self):
        """Initialize risk management BEFORE portfolio provider"""
        from risk_mgmt_2026.risk_manager import RiskManager2026
        from risk_mgmt_2026.portfolio_provider import PortfolioProvider2026
        
        # Get current account value
        account_value = self.ibkr_client.get_account_value()
        
        # Initialize risk manager FIRST (with account value and config)
        self.risk_manager = RiskManager2026(
            account_value if account_value > 0 else self.config.get('INITIAL_PORTFOLIO_VALUE', 10000),
            config=self.config
        )
        
        # Initialize portfolio provider SECOND (with risk manager)
        self.portfolio_provider = PortfolioProvider2026(self.risk_manager)
    
    def _initialize_strategies(self):
        """Initialize strategy modules with proper dependencies"""
        from bull_module_2026.bull import BullModule2026
        from bear_module_2026.bear import BearModule2026
        from volatile_module_2026.volatile import VolatileModule2026
        
        # All strategies use async_adapter (which includes thread-safe wrapper)
        # This ensures they have access to all required methods:
        # - calculate_max_trade_size (from thread-safe wrapper)
        # - is_trading_halted(symbol) (from thread-safe wrapper)
        # - All market data methods (from async adapter)
        
        self.strategies = [
            BullModule2026(self.async_adapter, self.portfolio_provider),      # Index 0: Bull
            BearModule2026(self.async_adapter, self.portfolio_provider),      # Index 1: Bear  
            VolatileModule2026(self.async_adapter, self.portfolio_provider)   # Index 2: Volatile
        ]
    
    def _initialize_support_components(self):
        """Initialize news handler and stock screener"""
        from news_handler_2026.news import NewsHandler2026
        from stock_screener_2026.screener import StockScreener2026
        
        # News handler for sentiment analysis (expects ibkr_client, not config)
        self.news_handler = NewsHandler2026(self.async_adapter)
        
        # Stock screener for candidate selection (expects ibkr_client and portfolio_provider, not config)
        self.stock_screener = StockScreener2026(
            self.async_adapter, 
            self.portfolio_provider
        )
    
    def _initialize_execution_engine(self):
        """Initialize execution engine that orchestrates everything"""
        from execution_engine_2026.sync_engine import SyncExecutionEngine2026
        
        # Execution engine coordinates all components
        self.execution_engine = SyncExecutionEngine2026(
            config=self.config,
            ibkr_client=self.thread_safe_client,  # Use thread-safe client
            strategies=self.strategies,
            news_analyzer=self.news_handler,
            stock_screener=self.stock_screener,
            web_monitor=None  # Will be set after web monitor is created
        )
    
    def _initialize_web_monitor(self):
        """Initialize web monitoring dashboard"""
        from web_monitor_2026.monitor_server import BotMonitorServer
        
        # Create web monitor with the correct arguments
        self.web_monitor = BotMonitorServer(
            bot_instance=self,
            port=self.config.get('WEB_MONITOR_PORT', 5001)
        )
        
        # Link web monitor to execution engine
        self.execution_engine.web_monitor = self.web_monitor
        
        # Start web server in a background thread
        def start_web_server():
            self.web_monitor.start_server()
        
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        
        self.logger.info(f"🖥️ Web monitor starting at http://localhost:{self.config.get('WEB_MONITOR_PORT', 5001)}")
    
    def run(self):
        """Start all components and run the bot"""
        try:
            self.logger.info("")
            self.logger.info("============================================================")
            self.logger.info("🚀 Options Trading Bot 2026 is now LIVE!")
            self.logger.info("📊 Web Monitor: http://localhost:5001")
            self.logger.info(f"💰 Account Value: ${self.ibkr_client.get_account_value():,.2f}")
            self.logger.info("⏰ Market Hours: 9:30 AM - 4:00 PM ET")
            self.logger.info("============================================================")
            
            # Update web monitor that bot is running
            if self.web_monitor:
                self.web_monitor.update_bot_status("Running")
            
            # Start execution engine
            self.execution_engine.start()
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            if self.web_monitor:
                self.web_monitor.update_bot_status("Stopped")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            if self.web_monitor:
                self.web_monitor.update_bot_status("Error")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all components"""
        self.logger.info("Shutting down trading bot...")
        
        # Update web monitor that bot is shutting down
        if self.web_monitor:
            self.web_monitor.update_bot_status("Stopping")
        
        try:
            # Stop execution engine
            if self.execution_engine:
                self.execution_engine.stop()
                
            # Stop web monitor
            if self.web_monitor:
                self.web_monitor.stop_server()
                
            # Disconnect from IBKR
            if self.ibkr_client:
                self.ibkr_client.disconnect()
                
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        # Final status update
        if self.web_monitor:
            self.web_monitor.update_bot_status("Stopped")
        
        self.logger.info("Trading bot shutdown complete")

    # Web monitor interface methods
    async def get_portfolio_value(self) -> float:
        """Get current portfolio value for web monitor"""
        try:
            if self.ibkr_client:
                return self.ibkr_client.get_account_value()
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting portfolio value: {e}")
            return 0.0

    async def get_active_trades(self) -> list:
        """Get active trades for web monitor"""
        try:
            if not self.ibkr_client:
                return []
                
            positions = self.ibkr_client.get_positions()
            formatted_trades = []
            
            for pos in positions:
                try:
                    # Get basic position info
                    symbol = pos.contract.symbol if hasattr(pos, 'contract') else 'Unknown'
                    position_size = getattr(pos, 'position', 0)
                    current_value = getattr(pos, 'marketValue', 0)
                    avg_cost = getattr(pos, 'avgCost', 0)
                    unrealized_pnl = getattr(pos, 'unrealizedPNL', 0)
                    
                    # Calculate entry price and current price estimates
                    if position_size != 0:
                        entry_price = abs(avg_cost)
                        current_price = entry_price + (unrealized_pnl / abs(position_size) / 100)
                        pnl_pct = (unrealized_pnl / (abs(avg_cost * position_size * 100))) * 100 if avg_cost != 0 else 0
                    else:
                        entry_price = current_price = pnl_pct = 0
                    
                    # Determine strategy type from contract
                    strategy = 'unknown'
                    if hasattr(pos, 'contract'):
                        if getattr(pos.contract, 'secType', '') == 'BAG':
                            # Options spread
                            if position_size > 0:
                                strategy = 'bull_spread'  
                            else:
                                strategy = 'bear_spread'
                        elif getattr(pos.contract, 'secType', '') == 'OPT':
                            # Single option
                            right = getattr(pos.contract, 'right', '')
                            if right == 'C':
                                strategy = 'call_option'
                            elif right == 'P':
                                strategy = 'put_option'
                            else:
                                strategy = 'option'
                        else:
                            strategy = 'stock'
                    
                    formatted_trades.append({
                        'symbol': symbol,
                        'strategy': strategy,
                        'position_size': position_size,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'pnl': unrealized_pnl,
                        'pnl_pct': f"{pnl_pct:.2f}%",
                        'avg_cost': avg_cost
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error formatting position {symbol}: {e}")
                    continue
                    
            return formatted_trades
            
        except Exception as e:
            self.logger.error(f"Error getting active trades: {e}")
            return []

    async def get_risk_metrics(self) -> dict:
        """Get risk metrics for web monitor"""
        try:
            if self.risk_manager:
                metrics = self.risk_manager.get_risk_metrics()
                # Add additional fields expected by web monitor
                metrics['active_trailing_stops'] = len(getattr(self.risk_manager, 'trailing_stops', {}))
                return metrics
            return {
                'max_trade_size': 0,
                'daily_loss': 0,
                'active_trailing_stops': 0
            }
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {
                'max_trade_size': 0,
                'daily_loss': 0,
                'active_trailing_stops': 0
            }

    async def get_health_status(self) -> dict:
        """Get health status for web monitor"""
        try:
            return {
                'ibkr_connection': getattr(self.ibkr_client, 'connected', False) if self.ibkr_client else False,
                'execution_engine': self.execution_engine.running if self.execution_engine else False,
                'risk_manager': True if self.risk_manager else False,
                'portfolio_provider': True if self.portfolio_provider else False,
                'news_handler': True if hasattr(self, 'news_handler') else False,
                'stock_screener': True if hasattr(self, 'stock_screener') else False
            }
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'ibkr_connection': False,
                'execution_engine': False,
                'risk_manager': False,
                'portfolio_provider': False,
                'news_handler': False,
                'stock_screener': False
            }

    # Additional web monitor helper methods
    def log_trade_action(self, action_type: str, symbol: str, strategy: str, details: dict):
        """Log a trade action to the web monitor"""
        if self.web_monitor:
            self.web_monitor.add_trade_action(action_type, symbol, strategy, details)

    def log_error(self, error_type: str, message: str, details: dict = None):
        """Log an error to the web monitor"""
        if self.web_monitor:
            self.web_monitor.add_error(error_type, message, details or {})

    def update_market_sentiment(self, sentiment_data: dict):
        """Update market sentiment in web monitor"""
        if self.web_monitor:
            self.web_monitor.update_market_sentiment(sentiment_data)


def main():
    """Main entry point"""
    # Print startup banner
    print("============================================================")
    print("🚀 OPTIONS TRADING BOT 2026 - LIVE MODE")
    print("============================================================")
    print(f"Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("============================================================")
    
    # Create and run the bot
    bot = TradingBotMain()
    
    if bot.initialize():
        bot.run()
    else:
        print("❌ Bot initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 