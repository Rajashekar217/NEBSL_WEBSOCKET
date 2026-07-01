"""
NSE WebSocket Client - Installation & Connection Test

This script verifies:
   Python environment is correct
   All dependencies installed
   Client can initialize
   Can connect to NSE servers
   Receiving market data
   Data parsing works correctly

Run with: python test_client.py
"""

import sys
import time
import logging
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN} {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}{text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW} {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 1: Python Version
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 1: Python Environment")

python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
print_info(f"Python Version: {python_version}")

if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
    print_success(f"Python {python_version} is supported")
else:
    print_error(f"Python {python_version} is too old (need 3.8+)")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# TEST 2: Dependencies
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 2: Required Dependencies")

dependencies = {
    'websocket': 'websocket-client',
    'json': 'json (built-in)',
    'threading': 'threading (built-in)',
    'queue': 'queue (built-in)',
    'logging': 'logging (built-in)',
}

missing = []
for module, display_name in dependencies.items():
    try:
        __import__(module)
        print_success(f"{display_name} installed")
    except ImportError:
        print_error(f"{module} not installed")
        missing.append(module)

if missing:
    print_error(f"\nMissing dependencies: {', '.join(missing)}")
    print_info("Install with: pip install -r requirements.txt")
    sys.exit(1)

# Optional dependency
print("\nOptional dependencies:")
try:
    import orjson
    print_success("orjson installed (faster JSON parsing)")
except ImportError:
    print_warning("orjson not installed (using standard json)")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 3: NSE Client Import
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 3: NSE WebSocket Client Import")

try:
    from nse_ws_client import NSEWebSocketClient, MarketData
    print_success("Successfully imported NSEWebSocketClient")
    print_success("Successfully imported MarketData")
except ImportError as e:
    print_error(f"Failed to import: {e}")
    print_info("Make sure nse_ws_client.py is in the same directory")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# TEST 4: Client Initialization
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 4: Client Initialization")

try:
    client = NSEWebSocketClient()
    print_success("NSEWebSocketClient instance created")
    print_info(f"Endpoint: {client.endpoint}")
    print_info(f"Queue size: {client._data_queue.maxsize}")
except Exception as e:
    print_error(f"Failed to initialize: {e}")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# TEST 5: Subscription
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 5: Token Subscription")

try:
    client.subscribe_cm({26000: "NIFTY50"})
    print_success("Subscribed to CM (equity) - NIFTY50")
    
    client.subscribe_fo({75663: "BANKNIFTY_FUT"})
    print_success("Subscribed to FO (derivatives) - BANKNIFTY_FUT")
    
    print_info(f"Total subscriptions: {len(client._subscriptions)}")
except Exception as e:
    print_error(f"Failed to subscribe: {e}")
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# TEST 6: Connection & Data Reception
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 6: Connection & Data Reception")

print_info("Starting WebSocket client...")
try:
    client.start()
    print_success("Client started")
except Exception as e:
    print_error(f"Failed to start: {e}")
    sys.exit(1)

# Wait for connection and first data
print_info("Waiting for connection (max 30 seconds)...")
start_time = time.time()
data_received = False
error_occurred = False

try:
    q = client.data_channel()
    
    # Try to receive data
    while time.time() - start_time < 30:
        try:
            data = q.get(timeout=2)
            data_received = True
            break
        except:
            elapsed = time.time() - start_time
            remaining = 30 - int(elapsed)
            status = client.get_status()
            
            sys.stdout.write(f"\r⏳ Waiting... {int(elapsed)}s ({remaining}s remaining) | "
                           f"Connected: {status['connected']}")
            sys.stdout.flush()
    
    print("\n")  # New line after progress
    
except Exception as e:
    print_error(f"Error during data reception: {e}")
    error_occurred = True

if data_received:
    print_success("Data received from NSE!")
    print(f"\n  Token: {data.token}")
    print(f"  Ticker: {data.ticker}")
    print(f"  Segment: {data.segment}")
    print(f"  LTP: {data.ltp:.2f}")
    print(f"  Bid: {data.best_bid:.2f} x {data.best_bid_qty}")
    print(f"  Ask: {data.best_ask:.2f} x {data.best_ask_qty}")
    print(f"  Type: {data.tick_type}")
    print(f"  Time: {data.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
elif not error_occurred:
    status = client.get_status()
    print_warning("No data received in 30 seconds")
    print_info(f"Connected: {status['connected']}")
    print_info(f"Connection attempts: {status['connections']}")
    
    if not status['connected']:
        print_warning("Connection failed - check network or endpoint")
    else:
        print_warning("Connected but no data - market may be closed")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 7: Data Processing
# ═════════════════════════════════════════════════════════════════════════════

if data_received:
    print_header("Test 7: Data Processing")
    
    try:
        # Test data attributes
        attributes = [
            ('token', int, data.token),
            ('ticker', str, data.ticker),
            ('ltp', float, data.ltp),
            ('best_bid', float, data.best_bid),
            ('best_ask', float, data.best_ask),
            ('volume', int, data.volume),
            ('tick_type', str, data.tick_type),
        ]
        
        for attr_name, expected_type, attr_value in attributes:
            if isinstance(attr_value, expected_type):
                print_success(f"data.{attr_name} = {attr_value} ({expected_type.__name__})")
            else:
                print_error(f"data.{attr_name} has wrong type: {type(attr_value)}")
        
    except Exception as e:
        print_error(f"Error processing data: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 8: Connection Health
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test 8: Connection Health")

status = client.get_status()
print_info(f"Connected: {status['connected']}")
print_info(f"Connection attempts: {status['connections']}")
print_info(f"Data flow (seconds): {status['data_flow_seconds']:.1f}s")
print_info(f"Last data: {status['last_data']}")

if status['connected']:
    print_success("Connection is active")
else:
    print_warning("Connection is not active (market hours?)")

if status['data_flow_seconds'] < 5:
    print_success("Data is flowing normally")
elif data_received:
    print_info("Data is flowing (may be slower market period)")
else:
    print_warning("No recent data - check connection")

# ═════════════════════════════════════════════════════════════════════════════
# Cleanup
# ═════════════════════════════════════════════════════════════════════════════

print_header("Cleanup")
print_info("Stopping client...")
client.stop()
print_success("Client stopped")

# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════

print_header("Test Summary")

if data_received:
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + " ALL TESTS PASSED - Installation Successful!".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    print(Colors.END)
    print("\nYou're ready to start using the NSE WebSocket client!")
    print("\nNext steps:")
    print("  1. Review the examples: python example.py [1-5]")
    print("  2. Read the documentation: README.md")
    print("  3. Build your trading bot using nse_ws_client.py")
else:
    print(f"{Colors.YELLOW}{Colors.BOLD}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + " PARTIAL SUCCESS - Check market hours & connection".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    print(Colors.END)
    print("\nClient is installed but couldn't receive data.")
    print("This could be because:")
    print("  • Market is closed (open 9:15 AM - 3:30 PM IST)")
    print("  • No internet connection to NSE servers")
    print("  • Firewall blocking port 7443")
    print("\nTroubleshooting:")
    print("  1. Check your internet connection")
    print("  2. Verify NSE servers are reachable")
    print("  3. Check if market is in trading hours")
    print("  4. Review README.md troubleshooting section")

print("\n" + "="*70)
print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70 + "\n")