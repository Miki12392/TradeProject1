import pandas as pd
import requests
import time
from pathlib import Path
from datetime import datetime, timedelta


def download_ohlc_hyperliquid(symbol="BTC", interval="1m", days=60):
    print(f"--- POBIERANIE DANYCH {symbol} ({interval}) ---")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    url = "https://api.hyperliquid.xyz/info"
    all_candles = []

    current_end = int(end_time.timestamp() * 1000)
    start_ts = int(start_time.timestamp() * 1000)

    while current_end > start_ts:
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": interval,
                "startTime": start_ts,
                "endTime": current_end
            }
        }
        response = requests.post(url, json=payload)
        data = response.json()

        if not data:
            break

        all_candles.extend(data)
        # Przesuwamy koniec na najstarszą pobraną świecę
        current_end = data[0]['t'] - 1
        print(f"Pobrano {len(all_candles)} świec... (Data: {datetime.fromtimestamp(data[0]['t'] / 1000)})")
        time.sleep(0.5)  # Anti-rate limit

    df = pd.DataFrame(all_candles)
    df = df.rename(columns={
        't': 'timestamp', 'o': 'open', 'h': 'high',
        'l': 'low', 'c': 'close', 'v': 'volume'
    })

    # Konwersja typów
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Zapis do Parquet (Zgodnie z wymaganiami load_parquet.py)
    output_dir = Path("data/storage")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{symbol}_{interval}_{days}d.parquet"
    df.to_parquet(file_path)
    print(f"✅ Plik zapisany: {file_path}")


if __name__ == "__main__":
    download_ohlc_hyperliquid()