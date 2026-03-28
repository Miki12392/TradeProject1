import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from config.settings import HL_WALLET_ADDRESS, HL_API_SECRET


class HyperliquidClient:
    def __init__(self):
        # API do odczytu danych (darmowe, publiczne)
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.exchange = None

        # API do egzekucji i czytania prywatnego portfela (wymaga kluczy)
        if HL_API_SECRET and HL_WALLET_ADDRESS:
            try:
                # Ładujemy klucz prywatny (API Secret)
                self.account: LocalAccount = eth_account.Account.from_key(HL_API_SECRET)
                # Inicjujemy klienta autoryzowanego
                self.exchange = Exchange(
                    wallet=self.account,
                    base_url=constants.MAINNET_API_URL,
                    account_address=HL_WALLET_ADDRESS
                )
            except Exception as e:
                print(f"[ERROR] Błąd ładowania kluczy API: {e}")

    def get_price(self, symbol: str) -> float:
        """Pobiera aktualną cenę danego aktywa."""
        mids = self.info.all_mids()
        return float(mids.get(symbol, 0.0))

    def get_balance(self) -> float:
        """Pobiera całkowitą wartość Twojego portfela w USD."""
        if not HL_WALLET_ADDRESS:
            return 0.0
        state = self.info.user_state(HL_WALLET_ADDRESS)
        # Margin Summary zawiera całkowitą wartość konta (margin + zysk)
        return float(state["marginSummary"]["accountValue"])