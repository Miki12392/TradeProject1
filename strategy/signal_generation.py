import numpy as np
from features.gpu_indicators import rsi_gpu, volatility_rolling_std_gpu
from strategy.micro_margin_math import GridParams


def compute_signal_matrix(
        close: np.ndarray,
        grid_params: GridParams,
        rsi_period: int = 14,
        vol_window: int = 20,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generowanie sygnałów z filtrem trendu i zmienności.
    """
    rsi = rsi_gpu(close, period=rsi_period)
    vol = volatility_rolling_std_gpu(close, window=vol_window)

    # 1. BAZOWY SYGNAŁ (Mean Reversion)
    signal = np.zeros_like(close, dtype=np.float64)
    signal[rsi < rsi_oversold] = 1.0
    signal[rsi > rsi_overbought] = -1.0

    # 2. FILTR TRENDU (Ochrona przed Black Swan / silnym trendem)
    # SMA 200 jako prosty wyznacznik trendu długoterminowego
    sma_short = np.convolve(close, np.ones(20) / 20, mode='same')
    sma_long = np.convolve(close, np.ones(200) / 200, mode='same')

    # Jeśli cena jest w silnym trendzie spadkowym, blokujemy LONG (i odwrotnie)
    # Zapobiega to 'łapaniu spadających noży' w systemie Grid
    signal[(close < sma_long) & (signal > 0)] = 0
    signal[(close > sma_long) & (signal < -0)] = 0

    # 3. FILTR ZMIENNOŚCI (Triple Barrier Hint)
    # Jeśli zmienność jest ekstremalnie niska, Grid może nie zarobić na prowizje
    avg_vol = np.mean(vol)
    signal[vol < (avg_vol * 0.5)] = 0

    return rsi, vol, signal