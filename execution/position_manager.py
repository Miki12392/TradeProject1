class PositionManager:
    def __init__(self, initial_capital: float, max_daily_drawdown: float = 0.05):
        """
        initial_capital: Kapitał startowy (np. 8.5 USD)
        max_daily_drawdown: Maksymalna strata w ciągu dnia (np. 0.05 = 5%)
        """
        self.initial_capital = initial_capital
        self.max_daily_drawdown = max_daily_drawdown
        self.is_kill_switch_active = False

    def check_kill_switch(self, current_balance: float) -> bool:
        if self.is_kill_switch_active:
            return True

        # ZABEZPIECZENIE: Jeśli kapitał to 0, odcinamy handel, ale bez błędu matematycznego
        if self.initial_capital <= 0:
            print("[WARNING] Kapitał to 0! Zatrzymuję handel (Kill Switch).")
            self.is_kill_switch_active = True
            return True

        drawdown = (self.initial_capital - current_balance) / self.initial_capital

        if drawdown >= self.max_daily_drawdown:
            self.is_kill_switch_active = True
            return True

        return False

    def calculate_position_size(self, current_balance: float, risk_per_trade: float = 0.02) -> float:
        if self.is_kill_switch_active:
            return 0.0

        position_value_usd = current_balance * risk_per_trade
        return position_value_usd