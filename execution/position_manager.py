from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
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

    def process_signal(self, current_price: float, signal: float, current_vol: float) -> bool:
        """
        Zaktualizowana wersja: przyjmuje bieżącą zmienność (current_vol)
        do wyznaczenia Triple Barrier.
        """
        if signal == 0.0 or len(self.active_positions) >= self.params.effective_levels:
            return False

        side = 1 if signal > 0 else -1
        slippage = current_price * self.slippage_pct
        entry_price = current_price + slippage if side == 1 else current_price - slippage

        size_usd = self.params.position_size_usd_per_level()
        size_coin = size_usd / entry_price

        # DYNAMICZNE BARIERY (de Prado)
        # Używamy zmienności do określenia szerokości bariery
        # Mnożnik 2.0 dla TP i 3.0 dla SL (asymetria chroniąca kapitał)
        vol_distance = entry_price * current_vol * 2.0

        tp_price = entry_price + (vol_distance if side == 1 else -vol_distance)
        sl_price = entry_price - (vol_distance * 1.5 if side == 1 else -vol_distance * 1.5)

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