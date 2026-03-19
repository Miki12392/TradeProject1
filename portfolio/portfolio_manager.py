from dataclasses import dataclass

@dataclass
class Portfolio:
    initial_capital: float
    leverage: int
    current_capital: float = 0.0
    realized_pnl: float = 0.0
    total_fees_paid: float = 0.0
    max_drawdown_limit: float = 0.10  # 10% limit straty na sesję

    def __post_init__(self):
        if self.current_capital == 0.0:
            self.current_capital = self.initial_capital

    def add_realized_trade(self, gross_pnl: float, fee: float):
        net_pnl = gross_pnl - fee
        self.realized_pnl += gross_pnl
        self.total_fees_paid += fee
        self.current_capital += net_pnl

    def is_bankrupt(self) -> bool:
        """Sprawdza, czy przekroczyliśmy dopuszczalny limit straty."""
        current_loss = (self.initial_capital - self.current_capital) / self.initial_capital
        return current_loss >= self.max_drawdown_limit

    def get_equity(self, unrealized_pnl: float = 0.0) -> float:
        return self.current_capital + unrealized_pnl