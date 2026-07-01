"""
NSE Live Feed WebSocket Client Library

Professional-grade client for connecting to NSE live market data feed.
Supports both CM (equity) and FO (derivatives) segments.

Features:
   Real-time tick data (LTP)
   Instant depth data (5-level bid/ask)
   Automatic reconnection with exponential backoff
   Heartbeat & timeout detection
   Thread-safe queue-based data delivery
   Full OHLC + Greeks support

Author: Northeast Ltd
Version: 1.0
Last Updated: June 2026
"""

import json
import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple, Optional

import websocket


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DepthLevel:
    """Single bid/ask level in order book"""
    price: float
    qty: int
    orders: int = 0

    def __repr__(self):
        return f"{self.price:.2f}({self.qty})"


@dataclass
class MarketData:
    """Complete market data for a token"""
    # Identification
    ticker: str
    token: int
    segment: str  # "CM" or "FO"
    
    # Price data
    ltp: float = 0.0  # Last Traded Price
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    
    # Volume & Interest
    volume: int = 0
    oi: int = 0  # Open Interest (FO only)
    avg_price: float = 0.0
    
    # Changes
    net_change: float = 0.0
    net_change_pct: float = 0.0
    
    # Depth (Order Book)
    best_bid: float = 0.0
    best_bid_qty: int = 0
    best_ask: float = 0.0
    best_ask_qty: int = 0
    bid_levels: list = field(default_factory=list)  # List of DepthLevel
    ask_levels: list = field(default_factory=list)  # List of DepthLevel
    total_bid_qty: int = 0
    total_ask_qty: int = 0
    
    # Meta
    tick_type: str = "TL"  # "TL" (tick) or "B5" (depth)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        """Pretty print"""
        return (
            f"{self.ticker} LTP={self.ltp:.2f} "
            f"Bid={self.best_bid:.2f}x{self.best_bid_qty} "
            f"Ask={self.best_ask:.2f}x{self.best_ask_qty} "
            f"[{self.tick_type}] {self.timestamp.strftime('%H:%M:%S.%f')[:-3]}"
        )


# =============================================================================
# CLIENT
# =============================================================================

class NSEWebSocketClient:
    """
    Professional WebSocket client for NSE live feed.
    
    Usage:
        client = NSEWebSocketClient
        client.subscribe_cm({26000: "NIFTY50"})
        client.subscribe_fo({75663: "BANKNIFTY_FUT"})
        client.start()
        
        q = client.data_channel()
        while True:
            data = q.get(timeout=60)
            print(f"{data.ticker}: {data.ltp}")
    """

    def __init__(
        self,
        endpoint: str = "XXXXXXXXXXXXXXXX",
        logger: Optional[logging.Logger] = None,
        queue_size: int = 50000,
    ):
        """
        Initialize the client.
        
        Args:
            endpoint: WebSocket server URL
            logger: Python logger instance (optional)
            queue_size: Max items in data queue
        """
        self.endpoint = endpoint
        self.logger = logger or logging.getLogger(__name__)
        self._data_queue = queue.Queue(maxsize=queue_size)
        
        self._ws = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._worker = None
        self._subscriptions: Dict[int, Tuple[str, int]] = {}
        
        self.is_connected = False
        self.connection_count = 0
        self.last_data_time = None

    # ─────────────────────────────────────────────────────────────────────
    # Subscription Management
    # ─────────────────────────────────────────────────────────────────────

    def subscribe_cm(self, token_ticker_map: Dict[int, str]):
        """
        Subscribe to CM (equity) segment tokens.
        
        Args:
            token_ticker_map: Dict of {token: "ticker_name"}
            
        Example:
            client.subscribe_cm({26000: "NIFTY50", 26009: "BANKNIFTY"})
        """
        self.subscribe(token_ticker_map, segment=1)

    def subscribe_fo(self, token_ticker_map: Dict[int, str]):
        """
        Subscribe to FO (derivatives) segment tokens.
        
        Args:
            token_ticker_map: Dict of {token: "ticker_name"}
            
        Example:
            client.subscribe_fo({75663: "BANKNIFTY_FUT", 78774: "PE"})
        """
        self.subscribe(token_ticker_map, segment=2)

    def subscribe(self, token_ticker_map: Dict[int, str], segment: int = 2):
        """
        Subscribe to tokens.
        
        Args:
            token_ticker_map: Dict of {token: "ticker_name"}
            segment: 1 for CM, 2 for FO
        """
        for token, ticker in token_ticker_map.items():
            self._subscriptions[int(token)] = (str(ticker), int(segment))
        
        self.logger.info(
            " Subscribed: %d tokens (segment=%s)",
            len(self._subscriptions),
            "CM" if segment == 1 else "FO"
        )

    # ─────────────────────────────────────────────────────────────────────
    # Connection Management
    # ─────────────────────────────────────────────────────────────────────

    def start(self):
        """Start the WebSocket client (background thread)"""
        if self._worker and self._worker.is_alive():
            self.logger.warning(" Client already running")
            return
        
        self._stop.clear()
        self._worker = threading.Thread(
            target=self._run_forever,
            daemon=True,
            name="NSE-WebSocket-Client"
        )
        self._worker.start()
        self.logger.info("Client started -> %s", self.endpoint)

    def stop(self):
        """Stop the WebSocket client"""
        self.logger.info("Stopping client...")
        self._stop.set()
        
        with self._lock:
            if self._ws:
                try:
                    self._ws.close()
                except:
                    pass
        
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=5)
        
        self.logger.info(" Client stopped")

    # ─────────────────────────────────────────────────────────────────────
    # Data Access
    # ─────────────────────────────────────────────────────────────────────

    def data_channel(self) -> queue.Queue:
        """
        Get the data queue for reading market data.
        
        Returns:
            queue.Queue containing MarketData objects
            
        Example:
            q = client.data_channel()
            data = q.get(timeout=60)  # Block until data available
        """
        return self._data_queue

    def get_status(self) -> Dict:
        """Get client connection status"""
        return {
            "connected": self.is_connected,
            "connections": self.connection_count,
            "last_data": self.last_data_time,
            "data_flow_seconds": self.get_data_flow_status(),
        }

    def get_data_flow_status(self) -> float:
        """Get seconds since last data received"""
        if self.last_data_time is None:
            return 86400.0  # 1 day
        return (datetime.now() - self.last_data_time).total_seconds()

    # ─────────────────────────────────────────────────────────────────────
    # Internal Implementation
    # ─────────────────────────────────────────────────────────────────────

    def _run_forever(self):
        """Main event loop with auto-reconnect"""
        backoff = 1.0
        
        while not self._stop.is_set():
            try:
                self._connect_and_run()
                backoff = 1.0
            except Exception as e:
                self.logger.error("Connection lost: %s", e)
                self.is_connected = False
            
            if self._stop.is_set():
                break
            
            self.logger.info(" Reconnecting in %.1fs...", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 30.0)

    def _connect_and_run(self):
        """Connect and run message loop"""
        self.connection_count += 1
        self.logger.info(
            "Connecting (attempt=%d) -> %s",
            self.connection_count,
            self.endpoint
        )
        
        ws = websocket.create_connection(self.endpoint, timeout=30)
        with self._lock:
            self._ws = ws
        
        self.is_connected = True
        self.logger.info(" Connected")
        
        self._send_subscriptions(ws)
        ws.settimeout(60.0)
        state = {}

        while not self._stop.is_set():
            try:
                raw = ws.recv()
            except Exception as e:
                raise RuntimeError(f"recv error: {e}")
            
            if not raw:
                continue
            
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            
            # Handle server ping
            if msg.get("type") == "ping":
                try:
                    ws.send(json.dumps({"action": "pong"}))
                except:
                    pass
                continue
            
            # Handle cached depth on subscribe
            if msg.get("type") == "CACHED_DEPTH":
                token = msg.get("token")
                self.logger.debug(" Cached depth for token %s", token)
                msg = msg.get("data", {})
                msg["type"] = "B5"
            
            # Skip server messages
            if "status" in msg or "error" in msg:
                self.logger.debug("Server: %s", msg)
                continue
            
            # Parse and queue data
            data = self._parse_record(msg, state)
            if data is not None:
                self.last_data_time = datetime.now()
                try:
                    self._data_queue.put_nowait(data)
                except queue.Full:
                    self.logger.warning(" Queue full - dropping tick")

        ws.close()

    def _send_subscriptions(self, ws):
        """Send subscription requests to server"""
        if not self._subscriptions:
            self.logger.warning(" No subscriptions configured")
            return
        
        # Group by segment
        by_segment = {}
        for token, (ticker, seg) in self._subscriptions.items():
            by_segment.setdefault(seg, []).append(token)
        
        # Subscribe to each segment
        for segment, tokens in by_segment.items():
            ws.send(json.dumps({
                "action": "subscribe_tl",
                "seg": segment,
                "tokens": tokens
            }))
            ws.send(json.dumps({
                "action": "subscribe_b5",
                "seg": segment,
                "tokens": tokens
            }))
            
            seg_name = "CM" if segment == 1 else "FO"
            self.logger.info(" Subscribed to %d tokens (%s)", len(tokens), seg_name)

    def _parse_record(self, msg: Dict, state: Dict) -> Optional[MarketData]:
        """Parse message into MarketData object"""
        token = int(msg.get("token", 0))
        segment = int(msg.get("seg", 2))
        tick_type = msg.get("type", "TL")

        # Skip unknown tokens
        if token not in self._subscriptions and self._subscriptions:
            return None

        ticker, _ = self._subscriptions.get(token, (str(token), segment))

        if token not in state:
            state[token] = {}
        s = state[token]

        # Handle tick data
        if tick_type == "TL":
            s["ltp"] = msg.get("ltp", 0.0)
            s["oi"] = msg.get("oi", 0) or s.get("oi", 0)
            s["timestamp"] = datetime.now()
            
            # Handle index records
            if msg.get("index") == True:
                s["open"] = msg.get("open", 0.0)
                s["high"] = msg.get("high", 0.0)
                s["low"] = msg.get("low", 0.0)
                s["close"] = msg.get("close", 0.0)
                s["net_change_pct"] = msg.get("net_change_pct", 0.0)
                
                if s["close"] > 0:
                    s["net_change"] = round(
                        (s["net_change_pct"] / 100.0) * s["close"], 2
                    )
                else:
                    s["net_change"] = 0.0

        # Handle depth data
        else:
            fresh_ltp = s.get("ltp", 0.0)
            s.update(msg)
            if fresh_ltp > 0:
                s["ltp"] = fresh_ltp

        bids = s.get("bids", [])
        asks = s.get("asks", [])

        return MarketData(
            ticker=ticker,
            token=token,
            segment="CM" if segment == 1 else "FO",
            ltp=s.get("ltp", 0.0),
            open=s.get("open", 0.0),
            high=s.get("high", 0.0),
            low=s.get("low", 0.0),
            close=s.get("close", 0.0),
            volume=s.get("volume", 0),
            oi=s.get("oi", 0),
            avg_price=s.get("avg_price", 0.0),
            net_change=s.get("net_change", 0.0),
            net_change_pct=s.get("net_change_pct", 0.0),
            best_bid=bids[0]["price"] if bids else 0.0,
            best_bid_qty=bids[0]["qty"] if bids else 0,
            best_ask=asks[0]["price"] if asks else 0.0,
            best_ask_qty=asks[0]["qty"] if asks else 0,
            total_bid_qty=s.get("total_bid_qty", 0),
            total_ask_qty=s.get("total_ask_qty", 0),
            bid_levels=bids,
            ask_levels=asks,
            tick_type=tick_type,
            timestamp=s.get("timestamp", datetime.now()),
        )