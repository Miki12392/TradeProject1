import numpy as np
from typing import List, Tuple
from strategy.micro_margin_math import GridParams
from execution.position_manager import GridPositionManager
from portfolio.portfolio_manager import Portfolio


def run_sequential_backtest(
        open_p: np.ndarray, high_p: np.ndarray, low_p: np.ndarray, close_p: np.ndarray,
        signals: np.ndarray, params: GridParams, fee_bps: float, slippage_pct: float
) -> Tuple[List[float], Portfolio, GridPositionManager]:
    """Silnik sekwencyjny ODPORNY na look-ahead bias."""

    portfolio = Portfolio(initial_capital=params.capital_usd, leverage=params.leverage)
    manager = GridPositionManager(params, fee_bps=fee_bps, slippage_pct=slippage_pct)
    equity_curve = [portfolio.initial_capital]

    # ZACZYNAMY OD INDEXU 1, aby móc pobrać signals[t-1]
    for t in range(1, len(close_p)):
        c_high = high_p[t]
        c_low = low_p[t]
        c_close = close_p[t]
        prev_signal = signals[t - 1]

        # 1. Rozlicz pozycje z knotów
        closed_events = manager.update_market_price(c_high, c_low)
        for event in closed_events:
            portfolio.add_realized_trade(event["gross_pnl"], event["fee"])

        # 2. Przetwórz nowy sygnał
        manager.process_signal(c_close, prev_signal)

        # 3. Zapisz kapitał
        unrealized = manager.get_unrealized_pnl(c_close)
        equity_curve.append(portfolio.get_equity(unrealized))

    return equity_curve, portfolio, manager