"""
CSV Data Loader.

Responsible for:
- reading CSV file
- converting to MarketData
"""

import pandas as pd
import numpy as np

from domain.models import MarketData


class CsvDataLoader:
    def load(self, file_path: str) -> MarketData:
        """
        Loads CSV and converts to MarketData (numpy arrays).
        """

        df = pd.read_csv(file_path)

        # --- normalize column names ---
        df.columns = [c.strip().lower() for c in df.columns]

        # --- parse timestamp ---
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # --- sort just in case ---
        df = df.sort_values("timestamp")

        # --- convert to numpy arrays ---
        return MarketData(
            opens=df["open"].to_numpy(dtype=np.float64),
            highs=df["high"].to_numpy(dtype=np.float64),
            lows=df["low"].to_numpy(dtype=np.float64),
            closes=df["close"].to_numpy(dtype=np.float64),
            volumes=df["volume"].to_numpy(dtype=np.float64),
            timestamps=df["timestamp"].to_numpy(),
        )