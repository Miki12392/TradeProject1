import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from live.hyperliquid_client import HyperliquidClient
from live.notifier import send_telegram_msg


def run_live():
    client = HyperliquidClient()
    send_telegram_msg("🚀 System Quant uruchomiony. Paper Trading.")
    print("Naciśnij CTRL+C aby zatrzymać...")

    try:
        while True:
            price = client.get_price("BTC")
            if price > 0:
                print(f"[LIVE] BTC: {price:.2f}")
            time.sleep(5)
    except KeyboardInterrupt:
        send_telegram_msg("🛑 Zatrzymano bota (CTRL+C).")
        print("\nKoniec pracy.")


if __name__ == "__main__":
    run_live()