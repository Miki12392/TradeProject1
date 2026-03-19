import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import CAPITAL_USD, LEVERAGE, MARGIN_PER_GRID_LEVEL_USD, MAX_GRID_LEVELS, FEE_BPS, SLIPPAGE_PCT, \
    STORAGE_DIR
from strategy.micro_margin_math import GridParams
from strategy.signal_generation import compute_signal_matrix
from execution.position_manager import GridPositionManager
from backtest.sequential_engine import run_sequential_backtest
from analytics.metrics import probabilistic_sharpe_ratio, calculate_max_drawdown
from data.loaders.load_parquet import load_and_clean_parquet


def main():
    # Zmień nazwę pliku na właściwą!
    data_path = STORAGE_DIR / "BTC_1m_60d.parquet"

    print("[1/5] Ładowanie OHLC...")
    try:
        df = load_and_clean_parquet(data_path)
    except FileNotFoundError:
        print(f"Brak pliku w: {data_path}. Wgraj Parquet do folderu data/storage/!")
        return

    print("[2/5] Generowanie cech i sygnałów na GPU...")
    params = GridParams(CAPITAL_USD, LEVERAGE, MARGIN_PER_GRID_LEVEL_USD, MAX_GRID_LEVELS, 0.2, 0.5, 1.0)
    _, _, signals = compute_signal_matrix(df["close"].to_numpy(), params)

    print("[3/5] Uruchamianie silnika sekwencyjnego (Realizm Mode)...")
    equity_curve, portfolio, manager = run_sequential_backtest(
        df["open"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(),
        signals, params, FEE_BPS, SLIPPAGE_PCT
    )

    print("[4/5] Analityka...")
    equity_arr = np.array(equity_curve)
    returns = np.diff(equity_arr) / equity_arr[:-1]
    sr = (np.mean(returns) / np.std(returns)) * np.sqrt(365 * 24 * 60) if np.std(returns) > 0 else 0
    psr = probabilistic_sharpe_ratio(returns)
    max_dd = calculate_max_drawdown(equity_arr)

    print("\n" + "=" * 50)
    print("🏆 RAPORT Z EGZEKUCJI")
    print("=" * 50)
    print(f"PnL:       ${equity_arr[-1] - portfolio.initial_capital:.2f}")
    print(f"Opłaty:    ${portfolio.total_fees_paid:.2f}")
    print(f"Transakcje: {manager.trade_counter}")
    print(f"Max DD:    {max_dd * 100:.2f}%")
    print(f"Sharpe:    {sr:.2f} (PSR: {psr:.2f})")
    print("=" * 50)


if __name__ == "__main__":
    main()