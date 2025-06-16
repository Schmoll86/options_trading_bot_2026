#!/usr/bin/env python3
"""
Simplified bot runner with better error handling
"""

import sys
import os
import time
import signal
import logging
from datetime import datetime

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Setup logging with both file and console output
def setup_logging():
    """Configure logging with timestamp in filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"bot_run_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from some modules
    logging.getLogger('ib_insync').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return log_filename

def check_gateway():
    """Check if IBKR Gateway is running"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 4001))
    sock.close()
    return result == 0

def main():
    """Main runner"""
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🚀 OPTIONS TRADING BOT 2026 - SIMPLIFIED RUNNER")
    print("="*60)
    print(f"Log file: {log_file}")
    print("="*60 + "\n")
    
    # Check if Gateway is running
    if not check_gateway():
        print("❌ IBKR Gateway is not running on port 4001!")
        print("Please start IBKR Gateway/TWS first.")
        sys.exit(1)
    
    print("✓ IBKR Gateway detected on port 4001")
    
    # Import and run the main bot
    try:
        from main_sync_with_web import OptionsTradingBot2026
        
        bot = OptionsTradingBot2026()
        
        # Try to initialize with retries
        max_init_retries = 3
        for attempt in range(max_init_retries):
            try:
                logger.info(f"Initialization attempt {attempt + 1}/{max_init_retries}...")
                if bot.initialize():
                    logger.info("✓ Bot initialized successfully!")
                    break
                else:
                    raise Exception("Initialization returned False")
            except Exception as e:
                logger.error(f"Initialization attempt {attempt + 1} failed: {e}")
                if attempt < max_init_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("All initialization attempts failed!")
                    sys.exit(1)
        
        # Run the bot
        logger.info("Starting bot main loop...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    print("\n✓ Bot shutdown complete")

if __name__ == "__main__":
    main() 