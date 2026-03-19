from dataclasses import dataclass

@dataclass
class GridParams:
    capital_usd: float
    leverage: int
    margin_per_level_usd: float
    max_levels: int
    grid_spacing_pct: float
    take_profit_pct: float
    stop_loss_pct: float

    @property
    def effective_levels(self) -> int:
        by_margin = int(self.capital_usd / self.margin_per_level_usd)
        return min(max(1, by_margin), self.max_levels)

    def position_size_usd_per_level(self) -> float:
        return self.margin_per_level_usd * self.leverage

    def price_step_at(self, mid_price: float) -> float:
        return mid_price * (self.grid_spacing_pct / 100.0) if self.grid_spacing_pct else 0.0

    def tp_distance_at(self, entry_price: float) -> float:
        return entry_price * (self.take_profit_pct / 100.0)

    def sl_distance_at(self, entry_price: float) -> float:
        return entry_price * (self.stop_loss_pct / 100.0)