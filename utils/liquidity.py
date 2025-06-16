from utils/liquidity.py
def is_liquid(option_data, min_volume=100, min_open_interest=100, max_bid_ask_spread_pct=0.1):
"""
Check if an option or stock is liquid based on volume, open interest, and bid-ask spread.
Args:
option_data (dict): Must contain 'volume', 'open_interest', 'bid', 'ask'
min_volume (int): Minimum volume (default: 100)
min_open_interest (int): Minimum open interest (default: 100)
max_bid_ask_spread_pct (float): Max bid-ask spread as a percent of mid price (default: 0.1 = 10%)
Returns:
bool: True if liquid, False otherwise
"""
volume = option_data.get('volume', 0)
open_interest = option_data.get('open_interest', 0)
bid = option_data.get('bid', 0)
ask = option_data.get('ask', 0)
mid = (bid + ask) / 2 if (bid and ask) else 0
spread_pct = (ask - bid) / mid if mid else 1
return (
volume >= min_volume and
open_interest >= min_open_interest and
spread_pct <= max_bid_ask_spread_pct
)
