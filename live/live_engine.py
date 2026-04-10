import asyncio
import sys
from pathlib import Path
import numpy as np

# Dodajemy główny folder projektu do ścieżki, żeby importy działały
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from live.hyperliquid_client import HyperliquidClient
from live.notifier import send_telegram_msg
from live.db_logger import DatabaseLogger
from execution.position_manager import PositionManager


# Opcjonalnie: import Twojego mózgu (odkomentuj, gdy będziemy podpinać GPU)
# from strategy.signal_generation import compute_signal_matrix

async def run_production_engine():
    print("🚀 Inicjalizacja Produkcyjnego Silnika Quant...")

    # 1. Inicjalizacja komponentów
    client = HyperliquidClient()
    db = DatabaseLogger()

    try:
        # KROK 1: Synchroniczne, bezpieczne pobranie salda na start
        initial_balance = client.get_balance()
        db.log_system("INFO", f"System uruchomiony. Startowy kapitał: {initial_balance}")
        send_telegram_msg(f"🟢 PRODUKCJA ZAINICJOWANA\n💰 Kapitał: {initial_balance:.2f} USD")
    except Exception as e:
        # Wyłapujemy błąd i DUKUJEMY go na ekran, żeby nie było "cichej awarii"
        print(f"\n[SYSTEM WYKRYŁ BŁĄD KRYTYCZNY STARTU]: {e}\n")
        db.log_system("CRITICAL", f"Błąd inicjalizacji: {e}")
        send_telegram_msg("🔴 BŁĄD KRYTYCZNY: Nie udało się pobrać salda.")
        return

    # Inicjalizacja Menedżera Ryzyka (Kill Switch przy 5% straty)
    risk_manager = PositionManager(initial_capital=initial_balance, max_daily_drawdown=0.05)

    symbol = "BTC"

    try:
        while True:
            # 2. Sprawdzenie stanu konta i Kill Switcha (co np. 10 sekund)
            current_balance = await asyncio.to_thread(client.get_balance)

            if risk_manager.check_kill_switch(current_balance):
                msg = f"🛑 KILL SWITCH AKTYWOWANY! Kapitał spadł do {current_balance}. System zablokowany."
                print(msg)
                db.log_system("CRITICAL", msg)
                send_telegram_msg(msg)
                break  # Całkowicie wyłącza pętlę i kończy pracę bota!

            # 3. Pobranie najnowszej ceny
            price = await asyncio.to_thread(client.get_price, symbol)

            # ---------------------------------------------------------
            # MIEJSCE NA TWÓJ MÓZG (Podłączenie GPU i strategii)
            # ---------------------------------------------------------
            # Tutaj za chwilę pobierzesz listę ostatnich cen (np. 200 świec z WebSocket)
            # historyczne_ceny = np.array([60000, 60100, 60050...])
            # sygnaly = compute_signal_matrix(historyczne_ceny)
            # signal = sygnaly[-1] # Wyciągamy ostatnią decyzję (z tej sekundy)

            signal = 0  # Tymczasowy Placeholder: 0=Czekaj, 1=Long, -1=Short
            # ---------------------------------------------------------

            if signal == 1:
                # 4. Egzekucja z Fail-Safes (zarządzanie pozycją)
                size_usd = risk_manager.calculate_position_size(current_balance)
                size_coin = round(size_usd / price, 4)  # Przeliczenie USD na BTC

                # Zabezpieczenie na minimalną wielkość Hyperliquid (np. 0.001 dla BTC)
                size_coin = max(size_coin, 0.001)

                db.log_system("INFO", f"Wysyłam zlecenie KUPNA {size_coin} {symbol}")
                order_result = await asyncio.to_thread(
                    client.place_market_order_with_retry, symbol, True, size_coin
                )

                # 5. Logowanie wyniku transakcji
                if order_result["status"] == "ok":
                    exec_price = order_result["price"]
                    db.log_trade(symbol, "LONG", size_coin, exec_price, "SUCCESS")
                    send_telegram_msg(f"✅ OTWARTO: LONG {size_coin} {symbol} @ {exec_price}")
                else:
                    db.log_trade(symbol, "LONG", size_coin, 0.0, "FAILED")
                    send_telegram_msg(f"❌ ODRZUCONO ZLECENIE: {order_result['response']}")

            # Pętla zasypia asynchronicznie na 10 sekund (nie blokując komputera)
            await asyncio.sleep(10)

    except asyncio.CancelledError:
        send_telegram_msg("🛑 Zatrzymano silnik asynchroniczny.")
    except Exception as e:
        # Kolejne zabezpieczenie przed cichą awarią w trakcie działania
        print(f"\n[SYSTEM WYKRYŁ BŁĄD W PĘTLI]: {e}\n")
        db.log_system("CRITICAL", f"Błąd Runtime: {e}")
        send_telegram_msg(f"🔥 KRYTYCZNY BŁĄD PĘTLI: {e}")


if __name__ == "__main__":
    try:
        # Uruchomienie profesjonalnej pętli zdarzeń
        asyncio.run(run_production_engine())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Bezpieczne wyłączanie...")