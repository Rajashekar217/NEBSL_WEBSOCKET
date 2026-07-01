"""
Example: NSE Live Feed Client Usage

This example shows how to:
1. Connect to NSE live feed
2. Subscribe to CM and FO tokens
3. Receive and process market data
4. Handle disconnections
"""

import logging
import sys
import queue
from datetime import datetime

from nse_ws_client import NSEWebSocketClient, MarketData


# Example 1: Basic Usage
EXAMPLE_1_CM = {26000: "nifty", 26009: ""}
EXAMPLE_1_FO = {61088: "BANKNIFTY28JUL2026FUT"}

# Example 2: Depth Analysis
EXAMPLE_2_FO = {61917: "BANKNIFTY28JUL2659000CE"}

# Example 3: OHLC Tracking
EXAMPLE_3_CM = {26009: "NIFTY"}

# Example 4: Multi-Segment Trading
EXAMPLE_4_CM = {26000: "NIFTY50"}
EXAMPLE_4_FO = {61889: "BANKNIFTY28JUL2658000CE"}

# Example 5: Connection Monitoring
EXAMPLE_5_CM = {26000: "NIFTY50"}


# =============================================================================
# SETUP LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("nse_client.log")
    ]
)
logger = logging.getLogger("NSE-Example")


# =============================================================================
# EXAMPLE 1: Basic Usage
# =============================================================================

def example_basic():
    """
    Basic example: Connect and receive data
    """
    logger.info("=" * 70)
    logger.info("EXAMPLE 1: Basic Usage")
    logger.info("=" * 70)
    
    # Create client (uses default endpoint from nse_ws_client.py)
    client = NSEWebSocketClient()
    
    # Subscribe to tokens (configured at top)
    client.subscribe_cm(EXAMPLE_1_CM)
    client.subscribe_fo(EXAMPLE_1_FO)
    
    # Start client
    client.start()
    
    # Get data queue
    q = client.data_channel()
    
    # Receive and print data
    logger.info("Receiving data (press Ctrl+C to stop)...")
    tick_count = 0
    
    try:
        while True:
            try:
                data: MarketData = q.get(timeout=60)
                tick_count += 1
                
                # Pretty print
                logger.info(
                    "[%s][%s] %s | LTP=%.2f | Bid=%.2f x %d | Ask=%.2f x %d",
                    data.segment,
                    data.tick_type,
                    data.ticker,
                    data.ltp,
                    data.best_bid,
                    data.best_bid_qty,
                    data.best_ask,
                    data.best_ask_qty,
                )
                
                # Every 100 ticks, show summary
                if tick_count % 100 == 0:
                    logger.info("[OK] Received %d ticks", tick_count)
                    
            except TimeoutError:
                logger.warning("[!]  No data for 60 seconds")
                
    except KeyboardInterrupt:
        logger.info("[STOP] Stopping...")
        client.stop()
        logger.info("[OK] Total ticks received: %d", tick_count)


# =============================================================================
# EXAMPLE 2: Depth Data Analysis
# =============================================================================

def example_depth_analysis():
    """
    Example: Analyze bid/ask levels
    """
    logger.info("=" * 70)
    logger.info("EXAMPLE 2: Depth Data Analysis")
    logger.info("=" * 70)
    
    client = NSEWebSocketClient()
    client.subscribe_fo(EXAMPLE_2_FO)  # Use config tokens
    client.start()
    
    q = client.data_channel()
    
    logger.info("Analyzing depth data (press Ctrl+C to stop)...")
    b5_count = 0
    
    try:
        while True:
            data: MarketData = q.get(timeout=60)
            
            # Only process B5 (depth) records
            if data.tick_type != "B5":
                continue
            
            b5_count += 1
            
            # Spread
            spread = data.best_ask - data.best_bid
            spread_pct = (spread / data.best_bid * 100) if data.best_bid > 0 else 0
            
            # Bid levels (all 5)
            bid_str = " | ".join(
                [f"{level['price']:.2f}({level['qty']})" 
                 for level in data.bid_levels[:5]]
            )
            
            # Ask levels (all 5)
            ask_str = " | ".join(
                [f"{level['price']:.2f}({level['qty']})" 
                 for level in data.ask_levels[:5]]
            )
            
            logger.info(
                "[%d B5] LTP=%.2f | Spread=%.2f (%.2f%%) | "
                "BIDS: %s | ASKS: %s",
                b5_count,
                data.ltp,
                spread,
                spread_pct,
                bid_str,
                ask_str,
            )
    
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()


# =============================================================================
# EXAMPLE 3: OHLC Tracking
# =============================================================================

def example_ohlc_tracking():
    """
    Example: Track OHLC for index
    """
    logger.info("=" * 70)
    logger.info("EXAMPLE 3: OHLC Tracking")
    logger.info("=" * 70)
    
    client = NSEWebSocketClient()
    client.subscribe_cm(EXAMPLE_3_CM)  # Use config tokens
    client.start()
    
    q = client.data_channel()
    
    logger.info("Tracking NIFTY50 OHLC (press Ctrl+C to stop)...")
    
    try:
        tick_count = 0
        while True:
            data: MarketData = q.get(timeout=60)
            tick_count += 1
            
            # Log every tick with OHLC
            logger.info(
                "[%d] %s | LTP=%.2f | OHLC=[O:%.2f H:%.2f L:%.2f C:%.2f] | "
                "Chg=%+.2f (%.2f%%)",
                tick_count,
                data.ticker,
                data.ltp,
                data.open,
                data.high,
                data.low,
                data.close,
                data.net_change,
                data.net_change_pct,
            )
    
    except KeyboardInterrupt:
        client.stop()


# =============================================================================
# EXAMPLE 4: Multi-Segment Trading
# =============================================================================

def example_multi_segment():
    """
    Example: Trade pairs (index + futures)
    """
    logger.info("=" * 70)
    logger.info("EXAMPLE 4: Multi-Segment Trading")
    logger.info("=" * 70)
    
    client = NSEWebSocketClient()
    
    # Subscribe to tokens (configured at top)
    client.subscribe_cm(EXAMPLE_4_CM)   # Cash market
    client.subscribe_fo(EXAMPLE_4_FO)   # Futures
    
    client.start()
    q = client.data_channel()
    
    # Store latest data
    latest = {}
    tick_count = 0
    
    logger.info("Monitoring cash vs futures (press Ctrl+C to stop)...")
    
    try:
        while True:
            data: MarketData = q.get(timeout=60)
            latest[data.token] = data
            tick_count += 1
            
            # Show progress every tick
            logger.info(
                "[%d] %s: LTP=%.2f | ",
                tick_count,
                data.ticker or f"Token_{data.token}",
                data.ltp,
            )
            
            # If we have both instruments, calculate basis
            if 26000 in latest and 75663 in latest:
                index = latest[26000]
                future = latest[75663]
                
                # Calculate basis
                basis = future.ltp - index.ltp
                basis_pct = (basis / index.ltp * 100) if index.ltp > 0 else 0
                
                logger.info(
                    "   └─ NIFTY50: %.2f | BANKNIFTY_FUT: %.2f | "
                    "Basis: %.2f (%.2f%%)",
                    index.ltp,
                    future.ltp,
                    basis,
                    basis_pct,
                )
    
    except KeyboardInterrupt:
        client.stop()


# =============================================================================
# EXAMPLE 5: Connection Status Monitoring
# =============================================================================

def example_connection_monitoring():
    """
    Example: Monitor connection health
    """
    logger.info("=" * 70)
    logger.info("EXAMPLE 5: Connection Monitoring")
    logger.info("=" * 70)
    
    client = NSEWebSocketClient()
    client.subscribe_cm(EXAMPLE_5_CM)  # Use config tokens
    client.start()
    
    q = client.data_channel()
    
    logger.info("Monitoring connection (press Ctrl+C to stop)...")
    tick_count = 0
    
    try:
        while True:
            try:
                data: MarketData = q.get(timeout=60)
                tick_count += 1
                
                # Log every 10 ticks with connection status
                if tick_count % 10 == 0:
                    status = client.get_status()
                    logger.info(
                        "[%d] Connected=%s | Attempts=%d | Flow=%.1fs | "
                        "LTP=%.2f",
                        tick_count,
                        status["connected"],
                        status["connections"],
                        status["data_flow_seconds"],
                        data.ltp,
                    )
            
            except queue.Empty:
                status = client.get_status()
                logger.warning(
                    "⚠️  No data! Connected=%s | Flow=%.1fs",
                    status["connected"],
                    status["data_flow_seconds"],
                )
    
    except KeyboardInterrupt:
        client.stop()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import queue
    
    print("\n" + "=" * 70)
    print("NSE LIVE FEED CLIENT - EXAMPLES")
    print("=" * 70)
    print("\nAvailable examples:")
    print("  1. Basic usage (connect & receive)")
    print("  2. Depth data analysis (bid/ask levels)")
    print("  3. OHLC tracking (candlestick data)")
    print("  4. Multi-segment trading (cash vs futures)")
    print("  5. Connection monitoring")
    print("\nUsage: python example.py [1-5]")
    print("=" * 70 + "\n")
    
    if len(sys.argv) < 2:
        print("[!] Please specify example number (1-5)")
        sys.exit(1)
    
    example = sys.argv[1]
    
    try:
        if example == "1":
            example_basic()
        elif example == "2":
            example_depth_analysis()
        elif example == "3":
            example_ohlc_tracking()
        elif example == "4":
            example_multi_segment()
        elif example == "5":
            example_connection_monitoring()
        else:
            print(f"[!] Unknown example: {example}")
            sys.exit(1)
    except Exception as e:
        logger.error("[!] Error: %s", e, exc_info=True)
        sys.exit(1)