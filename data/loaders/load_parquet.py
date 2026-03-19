import polars as pl
from pathlib import Path

def load_and_clean_parquet(file_path: Path) -> pl.DataFrame:
    """
    Ładuje dane OHLC z formatu Parquet i wykonuje podstawowe czyszczenie.
    Zgodnie ze standardem Quant: Dane muszą być posortowane i bez braków.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Brak pliku danych: {file_path}")

    # Ładowanie danych za pomocą Polars (najszybsza metoda dla dużych zbiorów)
    df = pl.read_parquet(file_path)

    # Standardowe czyszczenie:
    # 1. Sortowanie po timestampie (krytyczne dla backtestu sekwencyjnego)
    # 2. Usunięcie duplikatów
    # 3. Wypełnienie brakujących wartości (forward fill)
    df = (
        df.sort("timestamp")
        .unique(subset=["timestamp"])
        .interpolate() # Wypełnia luki w cenie
    )

    # Upewnienie się, że mamy wymagane kolumny
    required_cols = ["timestamp", "open", "high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Brak wymaganej kolumny: {col} w pliku {file_path}")

    return df

if __name__ == "__main__":
    # Testowy odczyt
    from config.settings import STORAGE_DIR
    try:
        test_path = STORAGE_DIR / "BTC_1m_60d.parquet"
        data = load_and_clean_parquet(test_path)
        print(f"✅ Pomyślnie załadowano {len(data)} wierszy.")
        print(data.head())
    except Exception as e:
        print(f"❌ Błąd podczas testu ładowania: {e}")