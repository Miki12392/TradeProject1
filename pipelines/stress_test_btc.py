import sys
from pathlib import Path
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategy.micro_margin_math import GridParams
from strategy.signal_generation import compute_signal_matrix
from backtest.sequential_engine import run_sequential_backtest
from data.loaders.load_parquet import load_and_clean_parquet


def run_test():
    # 1. Ładowanie danych
    data_path = Path("data/storage/BTC_1m_60d.parquet")
    if not data_path.exists():
        print("Błąd: Brak danych BTC! Pobierz plik Parquet.")
        return

    df = load_and_clean_parquet(data_path)

    # 2. Parametry pod Twój budżet 500 USD (Realistyczne)
    params = GridParams(
        capital_usd=500.0,
        leverage=10,  # Zmniejszamy dźwignię dla testu stabilności
        margin_per_level_usd=5.0,
        max_levels=20,
        grid_spacing_pct=0.3,
        take_profit_pct=0.6,
        stop_loss_pct=1.2
    )

    print(f"--- URUCHAMIAM STRESS TEST BTC (60 dni) ---")

    # 3. Generowanie sygnałów
    rsi, vol, signals = compute_signal_matrix(df["close"].to_numpy(), params)

    # 4. Backtest
    equity_curve, portfolio, manager = run_sequential_backtest(
        df["open"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(),
        signals, vol, params, fee_bps=2.0, slippage_pct=0.0005
    )

    # 5. Wynik
    final_equity = equity_curve[-1]
    profit = final_equity - 500.0
    print(f"Wynik końcowy: ${final_equity:.2f}")
    print(f"Zysk/Strata: ${profit:.2f}")
    print(f"Liczba transakcji: {manager.trade_counter}")

    if final_equity < 450:
        print("WERDYKT: Strategia zbyt agresywna. Ryzyko wyzerowania konta.")
    else:
        print("WERDYKT: System stabilny. Można przejść do Paper Trading.")


if __name__ == "__main__":
    run_test()