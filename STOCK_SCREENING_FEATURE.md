# Stock Screening Scroll Feature

## Overview
I've added a real-time stock screening display to the web monitor that shows which stocks are being analyzed and their sentiment scores.

## Features

### 1. Three Category Display
- **🐂 Bullish Stocks**: Shows stocks with positive sentiment and upward momentum
- **🐻 Bearish Stocks**: Shows stocks with negative sentiment and downward momentum  
- **⚡ Volatile Stocks**: Shows stocks with high volatility scores

### 2. Visual Elements
- **Stock Symbol**: Bold display of ticker symbol
- **Rank**: Shows ranking within category (#1, #2, etc.)
- **Score**: Color-coded percentage score
  - Green: Positive sentiment
  - Red: Negative sentiment
  - Gray: Neutral

### 3. Animations
- Smooth fade-in animation for new stocks
- Hover effect that shifts items slightly
- Cascading entry animation when lists update

### 4. Auto-Scrolling
- Each category scrolls independently
- Maximum height of 200px per section
- Clean scrollbar styling

## How It Works

1. **Stock Screener** runs every 5 minutes during market hours
2. **Execution Engine** receives screening results
3. **Web Monitor** updates the display in real-time
4. **Browser** shows animated updates via WebSocket

## Testing

Run the test script to see it in action:
```bash
python test_screening_display.py
```

Then open http://localhost:5002 in your browser.

## Integration with Live Bot

When you run the bot with web UI:
```bash
python main_sync_with_web.py
```

The stock screening results will automatically appear at:
- http://localhost:5001
- Bottom section of the dashboard
- Updates every time the screener runs

## What You'll See

Example display:
```
🐂 Bullish Stocks        🐻 Bearish Stocks       ⚡ Volatile Stocks
AAPL #1  +75.0%         META #1  -60.0%         NVDA #1  +80.0%
MSFT #2  +65.0%         NFLX #2  -50.0%         AMD  #2  +70.0%
GOOGL #3 +55.0%         PYPL #3  -45.0%         COIN #3  +65.0%
```

## Customization

You can adjust:
- Scroll area height in CSS (`.stock-scroll`)
- Animation speed in JavaScript
- Number of stocks shown per category
- Update frequency in execution engine

The feature provides real-time visibility into what stocks the bot is analyzing and their relative sentiment scores! 