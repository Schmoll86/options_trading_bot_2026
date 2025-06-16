#!/usr/bin/env python3
"""
Safe startup script for the options trading bot
Provides additional checks and monitoring before starting real trading
"""

import asyncio
import logging
import sys
from datetime import datetime
from ibkr_client_2026.client import IBKRClient2026
from config_2026.config_loader import ConfigLoader2026

async def check_prerequisites():
    """Check all prerequisites before starting the bot"""
    print("\n" + "="*60)
    print("Options Trading Bot 2026 - Pre-flight Checks")
    print("="*60)
    
    # Load configuration
    config = ConfigLoader2026()
    
    # Create client
    client = IBKRClient2026(
        host=config.get('ibkr_host', '127.0.0.1'),
        port=config.get('ibkr_port', 4001),
        client_id=config.get('ibkr_client_id', 1)
    )
    
    try:
        # 1. Check IBKR connection
        print("\n1. Checking IBKR Gateway connection...")
        await client.connect()
        print("   ✓ Connected to IBKR Gateway")
        
        # 2. Check account status
        print("\n2. Checking account status...")
        account_value = await client.get_account_value()
        
        if account_value <= 0:
            print(f"   ⚠️  Account value is ${account_value:,.2f}")
            print("   Please ensure your account is funded and active")
            return False
        else:
            print(f"   ✓ Account value: ${account_value:,.2f}")
        
        # 3. Check trading hours
        print("\n3. Checking market hours...")
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        
        # Basic market hours check (M-F, 9:30 AM - 4:00 PM ET)
        # Note: This is simplified, doesn't account for holidays
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            print("   ⚠️  Market is closed (weekend)")
        elif hour < 9 or hour >= 16:
            print("   ⚠️  Market may be closed (outside regular hours)")
        else:
            print("   ✓ Market hours OK")
        
        # 4. Check risk parameters
        print("\n4. Checking risk parameters...")
        print(f"   - Max trade size: {config.get('max_trade_size_pct', 0.05) * 100}% of portfolio")
        print(f"   - Stop loss: {config.get('stop_loss_pct', 0.03) * 100}%")
        print(f"   - Daily loss limit: {config.get('daily_loss_limit', 0.10) * 100}%")
        print(f"   - Trading cycle interval: {config.get('trading_cycle_interval', 120)} seconds")
        
        # 5. Test market data
        print("\n5. Testing market data retrieval...")
        test_symbol = 'SPY'
        data = await client.get_market_data(test_symbol)
        if data and data.get('last'):
            print(f"   ✓ {test_symbol} market data: ${data['last']:.2f}")
        else:
            print(f"   ⚠️  Could not retrieve market data for {test_symbol}")
            print("      (This is normal if market is closed)")
        
        await client.disconnect()
        
        # Final confirmation
        print("\n" + "="*60)
        print("⚠️  IMPORTANT: This bot will trade with REAL MONEY!")
        print("="*60)
        print("\nPlease confirm you want to proceed:")
        print("1. All risk parameters are correctly set")
        print("2. You understand the risks involved")
        print("3. You are ready to start live trading")
        
        response = input("\nType 'YES' to start the bot, anything else to cancel: ")
        
        if response.strip().upper() == 'YES':
            return True
        else:
            print("\nBot startup cancelled.")
            return False
            
    except Exception as e:
        print(f"\n✗ Error during pre-flight checks: {e}")
        await client.disconnect()
        return False

async def start_bot_with_monitoring():
    """Start the bot with enhanced monitoring"""
    # Import main bot
    from main import OptionsTradingBot2026
    
    print("\n" + "="*60)
    print("Starting Options Trading Bot 2026...")
    print("="*60)
    
    # Set up enhanced logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('options_bot_2026.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    bot = OptionsTradingBot2026()
    
    try:
        # Initialize
        success = await bot.initialize()
        if not success:
            print("\n✗ Bot initialization failed!")
            return
        
        print("\n✓ Bot initialized successfully!")
        print("\nBot is now running. Press Ctrl+C to stop.")
        print("\nMonitor the bot at: http://localhost:5001")
        print("\nLogs are being written to: options_bot_2026.log")
        
        # Start trading
        await bot.start_trading()
        
    except KeyboardInterrupt:
        print("\n\nShutting down bot...")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.shutdown()
        print("\n✓ Bot shutdown complete.")

async def main():
    """Main function"""
    # Run pre-flight checks
    if await check_prerequisites():
        # Start the bot
        await start_bot_with_monitoring()
    else:
        print("\nBot not started due to failed checks or user cancellation.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.") 