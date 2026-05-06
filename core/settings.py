"""
Global application settings.
Keep it minimal and explicit.
"""

# Simulation speed multiplier (1 real second = N market seconds)
SIMULATION_SPEED: int = 60

# Default timezone for market display
MARKET_TIMEZONE: str = "America/New_York"

# Data folder path
DATA_PATH: str = "data/"

# Storage (DB)
DB_PATH: str = "storage/ipo_drocher.db"