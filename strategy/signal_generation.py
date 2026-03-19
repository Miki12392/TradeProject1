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
    rsi = rsi_gpu(close, period=rsi_period)
    vol = volatility_rolling_std_gpu(close, window=vol_window)
    signal = np.zeros_like(close, dtype=np.float64)
    signal[rsi < rsi_oversold] = 1.0
    signal[rsi > rsi_overbought] = -1.0
    return rsi, vol, signal