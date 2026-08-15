"""Create a consistent backup of the local SQLite databases."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = args.output or ROOT / "backups" / stamp
    for name in ("view.db", "admin.db"):
        source = ROOT / "data" / name
        if source.exists():
            backup(source, output / name)
            print(f"BACKED_UP {source} -> {output / name}")


if __name__ == "__main__":
    main()
