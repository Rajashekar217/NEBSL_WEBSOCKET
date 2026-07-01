import logging
from nse_ws_client import NSEWebSocketClient

logging.basicConfig(level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NSE")

client = NSEWebSocketClient()
client.subscribe_cm({26000: "NIFTY50", 26009: "BANKNIFTY"})
client.start()

q = client.data_channel()

try:
    while True:
        data = q.get(timeout=60)
        
        if data.tick_type == "B5":
            # Depth data (has bid/ask)
            logger.info(
                f"[DEPTH] {data.ticker} | LTP={data.ltp:.2f} | "
                f"Bid={data.best_bid:.2f}x{data.best_bid_qty} | "
                f"Ask={data.best_ask:.2f}x{data.best_ask_qty}"
            )
        else:
            # Tick data (TL)
            logger.info(
                f"[TICK] {data.ticker} | LTP={data.ltp:.2f}"
            )

except KeyboardInterrupt:
    client.stop()