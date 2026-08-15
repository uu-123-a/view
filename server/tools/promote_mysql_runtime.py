"""Promote validated `view_next` tables into `view`, preserving old tables."""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("必须添加 --confirm 才能提升 MySQL 运行库。")
    current = os.getenv("MYSQL_DATABASE", "view")
    candidate = os.getenv("MYSQL_MIGRATION_DATABASE", "view_next")
    legacy = f"view_legacy_{datetime.now():%Y%m%d_%H%M%S}"
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"), password=os.getenv("MYSQL_PASSWORD", ""), charset="utf8mb4", autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE `{legacy}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"SHOW TABLES FROM `{current}`")
            old_tables = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SHOW TABLES FROM `{candidate}`")
            new_tables = [row[0] for row in cursor.fetchall()]
            if not new_tables:
                raise RuntimeError("候选数据库没有数据表，已停止切换。")
            if old_tables:
                pairs = ",".join(f"`{current}`.`{name}` TO `{legacy}`.`{name}`" for name in old_tables)
                cursor.execute("RENAME TABLE " + pairs)
            pairs = ",".join(f"`{candidate}`.`{name}` TO `{current}`.`{name}`" for name in new_tables)
            cursor.execute("RENAME TABLE " + pairs)
        print(f"PROMOTED {candidate} -> {current}")
        print(f"LEGACY_DATABASE {legacy}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
