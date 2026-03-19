import asyncio
import json
import websockets
import polars as pl
from datetime import datetime
from config.settings import HYPERLIQUID_WS_URL


class HyperliquidDataStream:
    """
    Klasa odpowiedzialna za strumieniowanie danych z Hyperliquid.
    Zgodnie z architekturą: TYLKO pobieranie i czyszczenie danych.
    """

    def __init__(self, symbol: str = "BTC"):
        self.symbol = symbol
        self.uri = HYPERLIQUID_WS_URL
        self.data_buffer = []

    async def subscribe(self):
        """Subskrypcja kanału L2 Book lub Trades dla wybranego symbolu."""
        subscribe_msg = {
            "method": "subscribe",
            "subscription": {
                "type": "l2Book",
                "coin": self.symbol
            }
        }

        async with websockets.connect(self.uri) as websocket:
            await websocket.send(json.dumps(subscribe_msg))
            print(f"[DATA] Subskrypcja aktywna: {self.symbol}")

            while True:
                response = await websocket.recv()
                data = json.loads(response)

                if "data" in data:
                    processed_entry = self._handle_l2_update(data["data"])
                    if processed_entry:
                        self.data_buffer.append(processed_entry)
                        # Logowanie minimalne dla wydajności
                        if len(self.data_buffer) % 10 == 0:
                            print(f"[DATA] {self.symbol} Mid: {processed_entry['mid_price']}")

    def _handle_l2_update(self, msg_data: dict) -> dict:
        """Transformacja surowego JSON do słownika gotowego dla Polars."""
        try:
            levels = msg_data.get("levels", [])
            if not levels:
                return None

            # Hyperliquid dostarcza poziomy bid/ask jako stringi
            best_bid = float(levels[0][0]["px"])
            best_ask = float(levels[1][0]["px"])
            mid_price = (best_bid + best_ask) / 2

            return {
                "timestamp": datetime.fromtimestamp(msg_data["time"] / 1000.0),
                "bid": best_bid,
                "ask": best_ask,
                "mid_price": mid_price,
                "symbol": self.symbol
            }
        except (KeyError, IndexError, ValueError):
            return None

    def get_as_polars(self) -> pl.DataFrame:
        """Konwersja bufora do formatu Polars dla modułów analitycznych."""
        if not self.data_buffer:
            return pl.DataFrame()
        return pl.DataFrame(self.data_buffer)


if __name__ == "__main__":
    stream = HyperliquidDataStream("BTC")
    try:
        asyncio.run(stream.subscribe())
    except KeyboardInterrupt:
        df = stream.get_as_polars()
        print("\n[DATA] Zebrane dane:")
        print(df.head())