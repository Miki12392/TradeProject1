import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Środowisko i Klucze ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Hyperliquid API Keys ---
HL_WALLET_ADDRESS = os.getenv("HL_WALLET_ADDRESS")
HL_API_SECRET = os.getenv("HL_API_SECRET")

# --- Hyperliquid API ---
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
HYPERLIQUID_WS_URL = "wss://api.hyperliquid.xyz/ws"

# --- Kapitał i Parametry Strategii ---
CAPITAL_USD = 400.0
LEVERAGE = 50
MARGIN_PER_GRID_LEVEL_USD = 4.0
MAX_GRID_LEVELS = 150

# --- Koszty transakcyjne ---
FEE_BPS = 2.0
SLIPPAGE_PCT = 0.0005

# --- Ścieżki danych ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)