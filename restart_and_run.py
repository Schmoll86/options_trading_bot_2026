#!/usr/bin/env python3
"""
Restart and Run Script
Helps coordinate IBKR Gateway restart with bot startup
"""

import os
import time
import subprocess

print("\n" + "="*60)
print("🔄 IBKR GATEWAY RESTART HELPER")
print("="*60 + "\n")

# Step 1: Stop any running bot instances
print("1️⃣ Stopping any running bot instances...")
subprocess.run(["pkill", "-f", "python main_sync_with_web.py"], capture_output=True)
time.sleep(2)

# Step 2: Prompt user to restart Gateway
print("\n2️⃣ Please restart your IBKR Gateway now:")
print("   - Close IBKR Gateway completely")
print("   - Wait a few seconds")
print("   - Start IBKR Gateway again")
print("   - Make sure it's fully loaded (green connection status)")
print("")
input("Press ENTER when IBKR Gateway is ready and connected...")

# Step 3: Wait a bit more
print("\n3️⃣ Waiting 10 seconds for Gateway to stabilize...")
time.sleep(10)

# Step 4: Start the bot
print("\n4️⃣ Starting the trading bot with conservative timeouts...")
print("   - Market data timeout: 60 seconds")
print("   - Connection stabilization: 10 seconds")
print("   - Data request delays: 2 seconds between stocks")
print("")

# Run the bot
subprocess.run(["python", "main_sync_with_web.py"]) 