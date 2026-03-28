import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from live.hyperliquid_client import HyperliquidClient
from live.notifier import send_telegram_msg

def run_live():
    print("🚀 Inicjalizacja połączenia API z Hyperliquid...")
    client = HyperliquidClient()

    # TEST API 1: Sprawdzenie stanu konta
    try:
        balance = client.get_balance()
        success_msg = f"🟢 SYSTEM QUANT ZAINICJOWANY\n💰 Podpięto kapitał: {balance:.2f} USD\n🤖 Tryb: Oczekuję na sygnały."
        print(success_msg)
        send_telegram_msg(success_msg)  # Telegram budzi się do życia!
    except Exception as e:
        error_msg = f"🔴 BŁĄD API KRYTYCZNY: Nie udało się pobrać salda. Sprawdź klucze w .env!\n{e}"
        print(error_msg)
        send_telegram_msg(error_msg)
        return

    print("Naciśnij CTRL+C aby zatrzymać...\n")

    # TEST API 2: Nasłuch rynku
    try:
        while True:
            price = client.get_price("BTC")
            if price > 0:
                print(f"[LIVE] BTC/USD Mid-Price: {price:.2f}")
            time.sleep(5)  # Sprawdzamy co 5 sekund
    except KeyboardInterrupt:
        send_telegram_msg("🛑 Zatrzymano bota (CTRL+C).")
        print("\n[SYSTEM] Koniec pracy. Rozłączono bezpiecznie.")

if __name__ == "__main__":
    run_live()