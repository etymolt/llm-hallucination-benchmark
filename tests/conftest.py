"""
conftest.py — pytest config: add the benchmark dir to sys.path so tests can
import scoring/prompts/etc. without an editable install.
"""

import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
if str(BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(BENCH_DIR))
