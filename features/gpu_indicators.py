from typing import Literal
import numpy as np

try:
    import cupy as cp
    _XP = cp
    _BACKEND: Literal["cupy", "numpy"] = "cupy"
except ImportError:
    _XP = np
    _BACKEND = "numpy"

def _to_xp(a: np.ndarray):
    return cp.asarray(a) if _BACKEND == "cupy" else a

def _to_numpy(a) -> np.ndarray:
    return cp.asarray(a).get() if _BACKEND == "cupy" else np.asarray(a)

def _ewm_vectorized(xp, arr, alpha: float):
    out = xp.empty_like(arr)
    out[0] = arr[0]
    for i in range(1, len(arr)):
        out[i] = alpha * arr[i] + (1 - alpha) * out[i - 1]
    return out

def rsi_gpu(close: np.ndarray, period: int = 14) -> np.ndarray:
    x = _to_xp(close.astype(np.float64))
    delta = _XP.zeros_like(x)
    delta[1:] = x[1:] - x[:-1]
    gain = _XP.where(delta > 0, delta, 0.0)
    loss = _XP.where(delta < 0, -delta, 0.0)
    alpha = 1.0 / period
    avg_g = _ewm_vectorized(_XP, gain, alpha)
    avg_l = _ewm_vectorized(_XP, loss, alpha)
    rs = _XP.where(avg_l != 0, avg_g / avg_l, _XP.inf)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = _XP.where(_XP.isfinite(rsi), rsi, 50.0)
    return _to_numpy(rsi)

def volatility_rolling_std_gpu(close: np.ndarray, window: int = 20) -> np.ndarray:
    x = _to_xp(close.astype(np.float64))
    ret = _XP.zeros_like(x)
    ret[1:] = (x[1:] - x[:-1]) / _XP.where(x[:-1] != 0, x[:-1], 1e-12)
    vol = _XP.zeros_like(x)
    for i in range(window, len(x)):
        vol[i] = _XP.std(ret[i - window : i])
    return _to_numpy(vol)