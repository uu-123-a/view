"""Restore SQLite databases from a backup directory after explicit confirmation."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("恢复会覆盖当前数据库，请增加 --confirm。")
    for name in ("view.db", "admin.db"):
        source = args.backup / name
        if not source.exists():
            continue
        target = ROOT / "data" / name
        with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
            src.backup(dst)
        print(f"RESTORED {source} -> {target}")


if __name__ == "__main__":
    main()
