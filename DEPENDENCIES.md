# Options Trading Bot 2026 - Dependencies

## Python Version
- **Python 3.11+** (Required for latest async features and performance)

## Core Dependencies

### Trading & Market Data
- **ib_insync (0.9.86)**: Interactive Brokers API wrapper
  - Async/await support for IBKR API
  - Market data streaming
  - Order management
  - Account information

- **ibapi (9.81.1.post1)**: Official IBKR Python API
  - Low-level API implementation
  - Required by ib_insync

### Data Processing & Analysis
- **pandas (2.1.4)**: Data manipulation and analysis
  - Market data processing
  - Technical indicator calculations
  - Time series analysis

- **numpy (1.24.3)**: Numerical computing
  - Mathematical operations
  - Array processing
  - Statistical calculations

- **scipy (1.11.4)**: Scientific computing
  - Statistical functions
  - Optimization algorithms
  - Black-Scholes calculations

### Web & Networking
- **flask (2.3.3)**: Web framework
  - Web monitoring interface
  - REST API endpoints
  - Dashboard hosting

- **flask-socketio (5.3.6)**: WebSocket support
  - Real-time data updates
  - Bi-directional communication
  - Live dashboard updates

- **python-socketio (5.9.0)**: Socket.IO server
  - WebSocket protocol handling
  - Event-based communication

- **aiohttp (3.9.1)**: Async HTTP client/server
  - Async web requests
  - News API integration
  - Market data fetching

- **requests (2.31.0)**: HTTP library
  - Synchronous API calls
  - News source integration
  - Web scraping

### Async & Concurrency
- **asyncio** (built-in): Async I/O support
  - Concurrent operations
  - Event loop management
  - Coroutine execution

- **nest-asyncio (1.6.0)**: Nested event loops
  - Jupyter notebook compatibility
  - Event loop patching

- **eventlet (0.33.3)**: Concurrent networking
  - Green thread support
  - Non-blocking I/O

### Data Parsing & Processing
- **beautifulsoup4 (4.12.2)**: HTML/XML parsing
  - Web scraping
  - News content extraction
  - HTML parsing

- **python-dateutil (2.9.0)**: Date/time utilities
  - Time zone handling
  - Date parsing
  - Market hours calculation

### Configuration & Environment
- **python-dotenv (1.0.0)**: Environment variable management
  - Configuration loading
  - Secret management
  - Environment isolation

### Testing & Development
- **pytest (7.4.3)**: Testing framework
  - Unit testing
  - Integration testing
  - Test automation

- **pytest-asyncio (0.21.1)**: Async test support
  - Async function testing
  - Coroutine testing

### Utilities
- **click (8.2.1)**: Command-line interface
  - CLI argument parsing
  - Command creation

- **pytz (2025.2)**: Timezone support
  - Market timezone handling
  - Time conversions

## Installation

### Using pip
```bash
pip install -r requirements.txt
```

### Using conda
```bash
conda create -n trading_bot python=3.11
conda activate trading_bot
pip install -r requirements.txt
```

## requirements.txt Content
```
# Core Trading
ib_insync==0.9.86
ibapi==9.81.1.post1

# Data Processing
pandas==2.1.4
numpy==1.24.3
scipy==1.11.4

# Web & API
flask==2.3.3
flask-socketio==5.3.6
python-socketio==5.9.0
aiohttp==3.9.1
requests==2.31.0
beautifulsoup4==4.12.2

# Async Support
nest-asyncio==1.6.0
eventlet==0.33.3

# Utilities
python-dotenv==1.0.0
python-dateutil==2.9.0.post0
pytz==2025.2
click==8.2.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
```

## System Dependencies

### Ubuntu/Debian
```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev
```

### macOS
```bash
# Using Homebrew
brew install python@3.11
```

### IBKR Gateway Requirements
- Java Runtime Environment (JRE) 8 or higher
- IBKR Gateway application
- Valid IBKR account (paper or live)
- API permissions enabled in IBKR account

## Optional Dependencies

### Performance Monitoring
- **prometheus-client**: Metrics export
- **grafana**: Metrics visualization

### Database Storage
- **sqlalchemy**: ORM for database access
- **psycopg2**: PostgreSQL adapter
- **redis**: In-memory data store

### Enhanced Analysis
- **ta-lib**: Technical analysis library
- **scikit-learn**: Machine learning
- **tensorflow**: Deep learning

### Notifications
- **twilio**: SMS alerts
- **sendgrid**: Email notifications
- **slack-sdk**: Slack integration

## Version Compatibility

| Component | Minimum Version | Recommended Version | Notes |
|-----------|----------------|-------------------|-------|
| Python | 3.9 | 3.11+ | Async improvements in 3.11 |
| IBKR Gateway | 10.19 | Latest stable | API compatibility |
| Java | 8 | 11 | For IBKR Gateway |
| Ubuntu | 20.04 | 22.04 | LTS versions |
| macOS | 11.0 | 13.0+ | ARM64 support |

## Dependency Management

### Virtual Environment Setup
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Updating Dependencies
```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package_name
```

### Dependency Conflicts
Common conflicts and resolutions:
1. **eventlet vs asyncio**: Use nest-asyncio for compatibility
2. **numpy version**: Some packages require specific numpy versions
3. **Flask vs async**: Use synchronous Flask with threading

## Security Considerations

1. **Keep dependencies updated**: Regular security patches
2. **Use virtual environments**: Isolate project dependencies
3. **Pin versions**: Ensure reproducible builds
4. **Audit dependencies**: Check for known vulnerabilities
```bash
pip audit
``` 