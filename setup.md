# NSE WebSocket Client - Setup Guide

Complete step-by-step guide to get the NSE live feed client running on your system.

---

## 📋 Pre-requisites

- **Python:** 3.8 or higher
- **OS:** Linux, macOS, or Windows
- **Internet:** Stable connection to NSE servers
- **Terminal:** Command line access

---

##  Step 1: Check Python Installation

```bash
# Check Python version
python --version
# Expected: Python 3.8.0 or higher

# Check pip
pip --version
# Expected: pip 20.0 or higher
```

**If Python not installed:**
- Linux: `sudo apt-get install python3-pip`
- macOS: `brew install python@3.10`
- Windows: Download from https://www.python.org/

---

## 📥 Step 2: Create Project Directory

```bash
# Create folder for your trading project
mkdir NEBSL_WEBSOCKET
cd NEBSL_WEBSOCKET

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

---

## 📦 Step 3: Install Dependencies

```bash
# Copy requirements.txt to your directory
# Then install:
pip install -r requirements.txt

# Verify installation
pip list | grep websocket
# Should show: websocket-client  X.X.X
```

---

## 📂 Step 4: Organize Files

```
NEBSL_WEBSOCKET/
├── venv/                    # Virtual environment
├── nse_ws_client.py        # Main library
├── example.py       # Examples
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── SETUP.md              # This file
├── test_client.py        # Your test script
└── trading_bot.py        # Your trading strategy
```

---

## 🧪 Step 5: Test Installation

Create `test_client.py`:

```python
"""
Simple test to verify NSE client installation
"""
import logging
from nse_ws_client import NSEWebSocketClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

print("=" * 70)
print("NSE WebSocket Client - Installation Test")
print("=" * 70)

# Test 1: Can we import?
print("\n Test 1: Import Check")
print("   ✓ nse_ws_client imported successfully")

# Test 2: Can we create client?
print("\n Test 2: Client Creation")
client = NSEWebSocketClient()
print("   ✓ NSEWebSocketClient instance created")

# Test 3: Can we subscribe?
print("\n Test 3: Subscription")
client.subscribe_cm({26000: "NIFTY50"})
print("   ✓ Subscribed to NIFTY50")

# Test 4: Can we start?
print("\n Test 4: Client Start")
client.start()
print("   ✓ Client started (background thread)")

# Test 5: Wait for data
print("\n⏳ Test 5: Receiving Data")
print("   Waiting for first data point (max 30 seconds)...")

q = client.data_channel()
try:
    data = q.get(timeout=30)
    print(f"   ✓ Data received!")
    print(f"   Token: {data.token}")
    print(f"   Ticker: {data.ticker}")
    print(f"   LTP: {data.ltp}")
    print(f"   Timestamp: {data.timestamp}")
except:
    print("   ✗ No data received (check connection)")

# Cleanup
client.stop()

print("\n" + "=" * 70)
print(" All tests passed! Installation successful!")
print("=" * 70)
```

**Run test:**
```bash
python test_client.py

# Expected output:
#  Test 1: Import Check
#  Test 2: Client Creation
#  Test 3: Subscription
#  Test 4: Client Start
#  Test 5: Receiving Data
#    Data received!
#    Token: 26000
#    Ticker: NIFTY50
#    LTP: 23865.75
#    Timestamp: ...
#  All tests passed!
```

---

## 🔐 Step 6: Network Configuration (if behind proxy)

### For Proxy Users:

```python
import websocket

# Set proxy
websocket.create_connection(
    endpoint,
    http_proxy_host="proxy.company.com",
    http_proxy_port=8080,
    http_proxy_auth=("username", "password")
)
```


---

## 🚀 Step 7: Run Examples

```bash
# Example 1: Basic usage
python example.py 1
# Ctrl+C to stop

# Example 2: Depth analysis
python example.py 2

# Example 3: OHLC tracking
python example.py 3

# Example 4: Multi-segment trading
python example.py 4

# Example 5: Connection monitoring
python example.py 5
```

---

## 💻 Step 8: Create Your Trading Bot

Create `trading_bot.py`:

```python
"""
Your custom trading bot
"""
import logging
from datetime import datetime
from nse_ws_client import NSEWebSocketClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("trading_bot.log")
    ]
)
logger = logging.getLogger("TradingBot")

def main():
    logger.info("=" * 70)
    logger.info("Trading Bot Started")
    logger.info("=" * 70)
    
    # Create client
    client = NSEWebSocketClient()
    
    # Subscribe to tokens
    logger.info("Subscribing to tokens...")
    client.subscribe_cm({
        26000: "NIFTY50",
        26009: "BANKNIFTY",
    })
    
    client.subscribe_fo({
        75663: "BANKNIFTY_FUT",
    })
    
    # Start client
    logger.info("Starting WebSocket client...")
    client.start()
    
    # Get data queue
    q = client.data_channel()
    
    # Trading loop
    logger.info("Trading loop started")
    tick_count = 0
    
    try:
        while True:
            try:
                # Receive data
                data = q.get(timeout=60)
                tick_count += 1
                
                # Your trading logic here
                if data.tick_type == "B5":  # Depth data
                    spread = data.best_ask - data.best_bid
                    logger.info(
                        f"[{tick_count}] {data.ticker:15} | "
                        f"LTP: {data.ltp:8.2f} | "
                        f"Spread: {spread:6.2f} | "
                        f"Bid Vol: {data.best_bid_qty:6d} | "
                        f"Ask Vol: {data.best_ask_qty:6d}"
                    )
                
                # Example: Buy when spread is tight
                if spread < 5 and data.ltp > 75600:
                    logger.warning(f"🔥 BUY Signal: {data.ticker} at {data.ltp}")
                
            except TimeoutError:
                logger.warning("No data received for 60 seconds")
                break
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    
    finally:
        client.stop()
        logger.info(f"Processed {tick_count} ticks")
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    main()
```

**Run your bot:**
```bash
python trading_bot.py

# Ctrl+C to stop
```

---

## 🔧 Configuration Files

### config.ini (Optional)

```ini

[TOKENS_CM]
26000 = NIFTY50
26009 = BANKNIFTY
26017 = VIX

[TOKENS_FO]
75663 = BANKNIFTY_FUT
75697 = NIFTY_FUT

[LOGGING]
level = INFO
file = trading.log
```

**Use in code:**
```python
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

endpoint = config.get('NSE', 'endpoint')
queue_size = config.getint('NSE', 'queue_size')

cm_tokens = dict(config.items('TOKENS_CM'))
fo_tokens = dict(config.items('TOKENS_FO'))

client = NSEWebSocketClient(endpoint=endpoint, queue_size=queue_size)
client.subscribe_cm({int(k): v for k, v in cm_tokens.items()})
```

---

## 📊 Monitoring Setup

### Real-time Dashboard (Optional)

```python
"""
Monitor bot health in real-time
"""
import time
from nse_ws_client import NSEWebSocketClient

def monitor_bot(client, interval=5):
    """Print status every N seconds"""
    while True:
        status = client.get_status()
        
        print(f"\n{'='*60}")
        print(f"Time: {time.strftime('%H:%M:%S')}")
        print(f"Connected: {'' if status['connected'] else '❌'}")
        print(f"Connections: {status['connections']}")
        print(f"Data Flow: {status['data_flow_seconds']:.1f}s ago")
        print(f"{'='*60}")
        
        time.sleep(interval)

# In your main code:
import threading
monitor_thread = threading.Thread(
    target=monitor_bot,
    args=(client, 10),
    daemon=True
)
monitor_thread.start()
```

---

## 🆘 Troubleshooting Installation

### Issue: "ModuleNotFoundError: No module named 'websocket'"

```bash
# Solution:
pip install websocket-client --upgrade

# Verify:
python -c "import websocket; print(websocket.__version__)"
```

---


### Issue: "No data after startup"

```bash
# Debug steps:
client = NSEWebSocketClient()
client.subscribe_cm({26000: "NIFTY50"})
client.start()

# Wait a moment
import time
time.sleep(5)

# Check status
status = client.get_status()
print(f"Connected: {status['connected']}")
print(f"Data flow: {status['data_flow_seconds']}")

# If data_flow > 10, connection issue
# If not connected, check logs
```

---

## 🎯 Performance Optimization

### For High-Frequency Trading:

```python
# 1. Use larger queue
client = NSEWebSocketClient(queue_size=100000)

# 2. Process in separate thread
import threading
def process_data(q):
    while True:
        data = q.get()
        # Fast processing, no blocking

threading.Thread(target=process_data, args=(q,), daemon=True).start()

# 3. Monitor performance
import sys
q = client.data_channel()
size_mb = sys.getsizeof(q) / 1024 / 1024
print(f"Queue size: {size_mb:.2f} MB")
```

---

## 📝 Logging Setup

```python
import logging

# File + Console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s][%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Get logger
logger = logging.getLogger("MyBot")

# Usage
logger.info("Bot started")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug info")
```

---

##  Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] requirements.txt installed
- [ ] test_client.py runs successfully
- [ ] Receives data from NSE
- [ ] Connection is stable (no timeouts)
- [ ] Logs are being written
- [ ] Trading bot runs without errors

---

## 🚀 Next Steps

1. **Run examples:** `python example.py 1`
2. **Customize tokens:** Edit TOKENS_CM/FO in your code
3. **Implement strategy:** Add your trading logic
4. **Test thoroughly:** Use paper trading first
5. **Monitor live:** Set up dashboard and alerts
6. **Deploy:** Move to production when confident

---

## 📞 Need Help?

1. **Check logs:** `tail -f bot.log`
2. **Enable debug:** Set logging to DEBUG level
3. **Run test:** `python test_client.py`
4. **Check examples:** `python example.py [1-5]`
5. **Read README:** Comprehensive API docs in README.md

---

**Ready to start trading! 🚀**