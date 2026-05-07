# conftest.py
import sys
import os

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ipo_drocher")
)
sys.path.insert(0, ROOT)