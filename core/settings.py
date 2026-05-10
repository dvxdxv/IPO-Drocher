"""
Global application settings.
Keep it minimal and explicit.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Data folder path
DATA_PATH: str = BASE_DIR / "data"

# Storage (DB)
DB_PATH = BASE_DIR / "storage" / "ipo_drocher.db"

# Simulation speed multiplier (1 real second = N market seconds)
SIMULATION_SPEED: int = 60

# Time interval for each simulation tick in real seconds
AUTO_TICK_INTERVAL_SECONDS: float = 1.0

# Default timezone for market display
MARKET_TIMEZONE: str = "America/New_York"