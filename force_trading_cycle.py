#!/usr/bin/env python3
"""
Force a trading cycle by temporarily bypassing time checks
"""

import requests
import json
import time

# Find the execution engine and force analysis
print("🔧 Attempting to trigger a trading cycle...")

# Check if bot is running
try:
    response = requests.get('http://localhost:5001/api/status')
    data = response.json()
    print(f"✅ Bot status: {data['bot_status']}")
    print(f"💰 Portfolio value: ${data['portfolio_value']:,.2f}")
    
    # The bot's execution engine should have a force_analysis method
    # But since we can't directly call it via API, we'll need to wait for the fix
    
    print("\n⚠️  The bot has a timezone bug!")
    print("📍 Current situation:")
    print("   - Arizona time: 7:49 AM")
    print("   - Eastern time: 10:49 AM")
    print("   - Market opened at: 6:30 AM Arizona time")
    print("   - Bot thinks market is closed because it's comparing local time to ET hours")
    
    print("\n🔧 To fix this, the bot needs to either:")
    print("   1. Convert local time to ET before checking")
    print("   2. Adjust market hours to local timezone")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📊 The screening feature is ready, but won't activate until:")
print("   - The timezone bug is fixed")
print("   - OR it reaches 9:30 AM Arizona time (when the bot thinks market opens)")
print("   - That would be 12:30 PM ET (3 hours into trading!)") 