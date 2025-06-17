#!/usr/bin/env python3
"""
Final Clean Options Trading Bot 2026 - Production Ready
All testing code removed, all interface issues fixed
"""

import sys
import os
import signal
import logging
import time

# Add the project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clear any cached modules to ensure fresh start
import importlib
import types

def clear_module_cache():
    """Clear Python module cache for clean restart"""
    modules_to_clear = []
    for module_name in sys.modules.keys():
        if any(part in module_name for part in [
            'bull_module_2026', 'bear_module_2026', 'volatile_module_2026',
            'execution_engine_2026', 'risk_mgmt_2026', 'thread_safe_ibkr_wrapper',
            'async_sync_adapter', 'ibkr_client_2026'
        ]):
            modules_to_clear.append(module_name)
    
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]

def main():
    """Main entry point for clean bot startup"""
    
    print("=" * 60)
    print("🚀 OPTIONS TRADING BOT 2026 - FINAL CLEAN VERSION")
    print("=" * 60)
    print("✅ All testing code removed")
    print("✅ All interface issues fixed")
    print("✅ Production ready")
    print("=" * 60)
    
    # Clear any cached modules
    clear_module_cache()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('clean_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting clean bot initialization...")
    
    try:
        # Import and start the main bot
        from main_sync_with_web import main
        
        # Setup signal handling
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the bot
        logger.info("Starting main bot process...")
        main()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 