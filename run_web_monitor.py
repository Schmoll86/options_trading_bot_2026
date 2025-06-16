#!/usr/bin/env python3
"""
Run the web monitor interface
"""

import logging
import sys
from web_monitor_2026.monitor_server import BotMonitorServer
from async_handler_2026 import create_sync_ibkr_client
from config_2026.config_loader import ConfigLoader2026
from risk_mgmt_2026.portfolio_provider import PortfolioProvider2026

logging.basicConfig(level=logging.INFO)

def main():
    try:
        # Load config
        config_loader = ConfigLoader2026()
        config = config_loader.get_all_config()
        
        # Create IBKR client
        client = create_sync_ibkr_client(
            host=config['IBKR_HOST'],
            port=config['IBKR_PORT'], 
            client_id=config['IBKR_CLIENT_ID']
        )
        
        # Connect
        client.connect()
        print(f"Connected to IBKR Gateway")
        
        # Create portfolio provider
        portfolio_provider = PortfolioProvider2026(client)
        
        # Create and start monitor server
        monitor = BotMonitorServer(
            bot_instance=None,  # No bot instance for now
            portfolio_provider=portfolio_provider,
            port=5001
        )
        
        print(f"\n✅ Web Monitor started at http://localhost:5001")
        print("Press Ctrl+C to stop\n")
        
        monitor.start()
        
    except KeyboardInterrupt:
        print("\nStopping web monitor...")
        if 'client' in locals() and client:
            client.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        if 'client' in locals() and client:
            client.disconnect()
        sys.exit(1)

if __name__ == "__main__":
    main() 