"""Run unit tests against isolated SQLite files, never the production MySQL database."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ["DATABASE_ENGINE"] = "sqlite"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
suite = unittest.defaultTestLoader.discover(str(ROOT / "server" / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
