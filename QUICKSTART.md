# NSE WebSocket Client - Quick Start (5 minutes)

Get the NSE client running in 5 minutes! 🚀

---

## 1️⃣ Install (2 minutes)

```bash
# Install dependencies
pip install websocket-client

# Optional (faster JSON parsing):
pip install orjson
```

---

## 2️⃣ Copy Files (1 minute)

Copy these files to your project:
- `nse_ws_client.py` (main library)
- `example.py` (examples)

---

## 3️⃣ Test Installation (1 minute)

```bash
python test_client.py
```

Expected output:
```
 Test 1: Python Environment
 Test 2: Required Dependencies
 Test 3: NSE WebSocket Client Import
 Test 4: Client Initialization
 Test 5: Token Subscription
 Test 6: Connection & Data Reception
  Token: 26000
  Ticker: NIFTY50
  LTP: 23865.75
  ...
 ALL TESTS PASSED
```

---

## 4️⃣ Run Examples (1 minute)

```bash
# Example 1: Basic real-time feed
python example.py 1

# Example 2: Depth analysis
python example.py 2

# Example 3: OHLC tracking
python example.py 3
```

---

## 5️⃣ Create Your Bot (This is on you! 😄)

```python
from nse_ws_client import NSEWebSocketClient

# Create client
client = NSEWebSocketClient()

# Subscribe to tokens
client.subscribe_cm({26000: "NIFTY50"})      # Equity
client.subscribe_fo({75663: "BANKNIFTY_FUT"}) # Futures

# Start
client.start()

# Receive data
q = client.data_channel()
while True:
    data = q.get()
    print(f"{data.ticker}: LTP={data.ltp}, Bid={data.best_bid}, Ask={data.best_ask}")
```

Save as `my_bot.py` and run:
```bash
python my_bot.py
```

---

## 📚 Common Tokens

```python
# Equity (CM) - Segment 1
client.subscribe_cm({
    26000: "NIFTY50",
    26009: "BANKNIFTY",
    26008: "NIFTY_IT",
    26017: "VIX",
})

# Futures (FO) - Segment 2
client.subscribe_fo({
    75663: "BANKNIFTY_FUT",
    75697: "NIFTY_FUT",
    78774: "BANKNIFTY_PE",
    78775: "BANKNIFTY_CE",
})
```

---

## 💡 Common Recipes

### Recipe 1: Get Latest Price

```python
from nse_ws_client import NSEWebSocketClient

client = NSEWebSocketClient()
client.subscribe_cm({26000: "NIFTY50"})
client.start()

q = client.data_channel()
data = q.get()  # Wait for first data
print(f"NIFTY50: {data.ltp}")

client.stop()
```

### Recipe 2: Track Bid-Ask Spread

```python
from nse_ws_client import NSEWebSocketClient

client = NSEWebSocketClient()
client.subscribe_fo({75663: "BANKNIFTY_FUT"})
client.start()

q = client.data_channel()
for _ in range(10):
    data = q.get()
    spread = data.best_ask - data.best_bid
    print(f"Spread: {spread:.2f}")

client.stop()
```

### Recipe 3: Print All 5 Depth Levels

```python
from nse_ws_client import NSEWebSocketClient

client = NSEWebSocketClient()
client.subscribe_fo({75663: "BANKNIFTY_FUT"})
client.start()

q = client.data_channel()
for _ in range(5):
    data = q.get()
    if data.tick_type == "B5":
        print(f"\n{data.ticker} - LTP: {data.ltp}")
        print("Bids:")
        for i, level in enumerate(data.bid_levels, 1):
            print(f"  L{i}: {level['price']:.2f} x {level['qty']}")
        print("Asks:")
        for i, level in enumerate(data.ask_levels, 1):
            print(f"  L{i}: {level['price']:.2f} x {level['qty']}")

client.stop()
```

### Recipe 4: Monitor Connection Health

```python
from nse_ws_client import NSEWebSocketClient
import time

client = NSEWebSocketClient()
client.subscribe_cm({26000: "NIFTY50"})
client.start()

# Check status every 5 seconds
for _ in range(10):
    status = client.get_status()
    print(f"Connected: {status['connected']}, Data flow: {status['data_flow_seconds']:.1f}s")
    time.sleep(5)

client.stop()
```

### Recipe 5: Calculate Basis (Spot vs Futures)

```python
from nse_ws_client import NSEWebSocketClient

client = NSEWebSocketClient()
client.subscribe_cm({26000: "NIFTY50"})
client.subscribe_fo({75697: "NIFTY_FUT"})
client.start()

q = client.data_channel()
latest = {}

while True:
    data = q.get()
    latest[data.token] = data
    
    if 26000 in latest and 75697 in latest:
        spot = latest[26000].ltp
        future = latest[75697].ltp
        basis = future - spot
        
        print(f"Spot: {spot:.2f} | Future: {future:.2f} | Basis: {basis:.2f}")
```

---

## 🔧 Basic Configuration

### Custom Logging

```python
import logging

# Setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MyBot")
logger.info("Bot started")

# Pass to client
client = NSEWebSocketClient(logger=logger)
```

### Larger Queue (for high-frequency trading)

```python
# Default: 50,000 items
# For high frequency, use 100,000+

client = NSEWebSocketClient(queue_size=100000)
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: websocket` | `pip install websocket-client` |
| No data received | Market is closed (9:15 AM - 3:30 PM IST) |
| "Connection refused" | Check internet connection |
| Queue full warnings | Use `queue_size=100000` |

---

## 🚀 Next Steps

1. **Explore Examples:**
   ```bash
   python example.py 1  # Basic
   python example.py 2  # Depth
   python example.py 3  # OHLC
   ```

2. **Read Full Docs:**
   - `README.md` - Complete API reference
   - `SETUP.md` - Detailed setup guide

3. **Build Your Strategy:**
   - Use recipes above as templates
   - Implement your trading logic
   - Test thoroughly with paper trading

4. **Deploy:**
   - Run in production environment
   - Monitor logs
   - Watch for edge cases

---

## 📞 Quick Help

```python
# List all available methods
from nse_ws_client import NSEWebSocketClient
client = NSEWebSocketClient()
print([m for m in dir(client) if not m.startswith('_')])
```

---

##  You're Ready!

You have everything to start trading! 🎉

**Good luck! 🚀**