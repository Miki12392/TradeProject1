from dataclasses import dataclass
from typing import List, Dict, Optional
from strategy.micro_margin_math import GridParams


@dataclass
class Position:
    id: int
    side: int
    size_coin: float
    entry_price: float
    tp_price: float
    sl_price: float
    is_open: bool = True

    def check_exit(self, high_price: float, low_price: float) -> Optional[float]:
        """Zwraca Gross PnL sprawdzając uderzenia po knotach (OHLC)."""
        if not self.is_open:
            return None

        if self.side == 1:  # LONG
            if high_price >= self.tp_price:
                self.is_open = False
                return (self.tp_price - self.entry_price) * self.size_coin
            elif low_price <= self.sl_price:
                self.is_open = False
                return (self.sl_price - self.entry_price) * self.size_coin

        elif self.side == -1:  # SHORT
            if low_price <= self.tp_price:
                self.is_open = False
                return (self.entry_price - self.tp_price) * self.size_coin
            elif high_price >= self.sl_price:
                self.is_open = False
                return (self.entry_price - self.sl_price) * self.size_coin

        return None


class GridPositionManager:
    def __init__(self, grid_params: GridParams, fee_bps: float, slippage_pct: float):
        self.params = grid_params
        self.fee_bps = fee_bps
        self.slippage_pct = slippage_pct
        self.active_positions: List[Position] = []
        self.trade_counter = 0

    def update_market_price(self, high_price: float, low_price: float) -> List[Dict[str, float]]:
        closed_events = []
        for pos in self.active_positions:
            gross_pnl = pos.check_exit(high_price, low_price)
            if gross_pnl is not None:
                # Rozliczamy obrót (Wejście + Wyjście po cenie docelowej)
                exit_price = pos.tp_price if gross_pnl > 0 else pos.sl_price
                turnover = (pos.size_coin * pos.entry_price) + (pos.size_coin * exit_price)
                fee_cost = turnover * (self.fee_bps / 10_000.0)
                closed_events.append({
                    "gross_pnl": gross_pnl,
                    "fee": fee_cost,
                    "net_pnl": gross_pnl - fee_cost
                })
        self.active_positions = [p for p in self.active_positions if p.is_open]
        return closed_events

    def process_signal(self, current_price: float, signal: float) -> bool:
        if signal == 0.0:
            return False
        if len(self.active_positions) >= self.params.effective_levels:
            return False

        side = 1 if signal > 0 else -1
        # Uwzględnienie slippage (Kupujemy drożej, sprzedajemy taniej)
        slippage = current_price * self.slippage_pct
        entry_price = current_price + slippage if side == 1 else current_price - slippage

        size_usd = self.params.position_size_usd_per_level()
        size_coin = size_usd / entry_price

        tp_dist = self.params.tp_distance_at(entry_price)
        sl_dist = self.params.sl_distance_at(entry_price)

        tp_price = entry_price + (tp_dist if side == 1 else -tp_dist)
        sl_price = entry_price - (sl_dist if side == 1 else -sl_dist)

        self.trade_counter += 1
        self.active_positions.append(
            Position(self.trade_counter, side, size_coin, entry_price, tp_price, sl_price)
        )
        return True

    def get_unrealized_pnl(self, current_price: float) -> float:
        return sum(
            (current_price - p.entry_price) * p.size_coin if p.side == 1 else
            (p.entry_price - current_price) * p.size_coin
            for p in self.active_positions
        )