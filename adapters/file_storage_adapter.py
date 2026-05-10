"""
File Storage Adapter.

Responsible for:
- scanning data directory
- returning available CSV files
"""

import os
from typing import List


class FileStorageAdapter:
    def __init__(self, data_path: str):
        self.data_path = data_path

    def list_csv_files(self) -> List[str]:
        """
        Returns list of CSV filenames.
        """
        return [
            f for f in os.listdir(self.data_path)
            if f.endswith(".csv")
        ]

    def list_tickers(self) -> List[str]:
        """
        Extracts tickers from filenames like CRCL_ipo_...
        """
        files = self.list_csv_files()
        tickers = []

        for f in files:
            ticker = f.split("_")[0]
            tickers.append(ticker)

        return sorted(list(set(tickers)))

    def get_file_path(self, filename: str) -> str:
        return os.path.join(self.data_path, filename)