import numpy as np
from scipy import stats

def calculate_max_drawdown(equity_curve: np.ndarray) -> float:
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (running_max - equity_curve) / np.where(running_max > 0, running_max, 1)
    return float(np.max(drawdowns))

def probabilistic_sharpe_ratio(returns: np.ndarray, sr_ref: float = 0.0) -> float:
    n = len(returns)
    if n < 2: return 0.5
    std = np.std(returns)
    sr_est = np.mean(returns) / std if std > 1e-12 else 0.0
    skew = stats.skew(returns)
    kurt = stats.kurtosis(returns, fisher=True) + 3.0
    var_sr = (1.0 - skew * sr_est + (kurt - 1.0) / 4.0 * sr_est**2) / (n - 1.0)
    var_sr = max(var_sr, 1e-12)
    z = (sr_est - sr_ref) / np.sqrt(var_sr)
    return float(stats.norm.cdf(z))