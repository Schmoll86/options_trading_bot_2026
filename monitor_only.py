#!/usr/bin/env python3
"""
Monitor-only mode for the options trading bot
Shows what the bot would do without executing any trades
"""

import asyncio
import logging
from datetime import datetime
from ibkr_client_2026.client import IBKRClient2026
from config_2026.config_loader import ConfigLoader2026
from stock_screener_2026.screener import StockScreener2026
from news_handler_2026.news import NewsHandler2026
from risk_mgmt_2026.risk_manager import RiskManager2026
from risk_mgmt_2026.portfolio_provider import PortfolioProvider2026

async def monitor_market():
    """Monitor market without trading"""
    print("\n" + "="*60)
    print("Options Trading Bot 2026 - Monitor Mode")
    print("="*60)
    print("This mode shows market analysis without executing trades\n")
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = ConfigLoader2026()
    
    # Create components
    client = IBKRClient2026(
        host=config.get('ibkr_host', '127.0.0.1'),
        port=config.get('ibkr_port', 4001),
        client_id=config.get('ibkr_client_id', 1)
    )
    
    try:
        # Connect to IBKR
        print("Connecting to IBKR Gateway...")
        await client.connect()
        print("✓ Connected\n")
        
        # Get initial account value
        account_value = await client.get_account_value()
        
        # Initialize risk manager with portfolio value and config
        risk_manager = RiskManager2026(
            account_value if account_value > 0 else config.get('initial_portfolio_value', 10000),
            config=config.get_all_config()
        )
        
        # Initialize portfolio provider
        portfolio_provider = PortfolioProvider2026(risk_manager)
        
        # Create analysis components
        news_handler = NewsHandler2026(client)
        stock_screener = StockScreener2026(client, portfolio_provider)
        
        print("Starting market monitoring... (Press Ctrl+C to stop)\n")
        
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"Monitoring Cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            try:
                # Get account info
                account_value = await client.get_account_value()
                print(f"\nAccount Value: ${account_value:,.2f}")
                
                # Get market sentiment
                print("\nAnalyzing market sentiment...")
                sentiment = await news_handler.get_market_sentiment()
                print(f"Market Sentiment: {sentiment.get('overall_sentiment', 'unknown')}")
                print(f"Confidence: {sentiment.get('confidence', 0):.1%}")
                
                # Get stock universe
                print("\nGetting stock universe...")
                universe = await stock_screener.get_dynamic_universe()
                print(f"Tracking {len(universe)} stocks")
                
                # Screen stocks
                candidates = await stock_screener.screen_stocks(sentiment)
                if candidates:
                    print(f"\nFound {len(candidates)} candidate stocks:")
                    for i, symbol in enumerate(candidates[:5], 1):
                        market_data = await client.get_market_data(symbol)
                        if market_data and market_data.get('last'):
                            print(f"  {i}. {symbol}: ${market_data['last']:.2f}")
                        else:
                            print(f"  {i}. {symbol}: (no data)")
                else:
                    print("\nNo candidate stocks found")
                
                # Show what strategies would be active
                print("\nActive strategies based on sentiment:")
                if sentiment.get('bullish'):
                    print("  ✓ Bull Call Spreads - ACTIVE")
                else:
                    print("  ✗ Bull Call Spreads - inactive")
                    
                if sentiment.get('bearish'):
                    print("  ✓ Bear Put Spreads - ACTIVE")
                else:
                    print("  ✗ Bear Put Spreads - inactive")
                    
                if sentiment.get('volatile'):
                    print("  ✓ Volatility Strategies - ACTIVE")
                else:
                    print("  ✗ Volatility Strategies - inactive")
                
                print(f"\nNext cycle in {config.get('trading_cycle_interval', 120)} seconds...")
                
            except Exception as e:
                logging.error(f"Error in monitoring cycle: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(config.get('trading_cycle_interval', 120))
            
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        await client.disconnect()
        print("\n✓ Disconnected from IBKR")

async def main():
    """Main function"""
    await monitor_market()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped.") 