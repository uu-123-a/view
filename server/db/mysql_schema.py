"""Create the empty MySQL runtime schema without importing local user data."""

from __future__ import annotations

import os
from pathlib import Path

import pymysql


def _setting(primary: str, railway: str, default: str = "") -> str:
    return os.getenv(primary) or os.getenv(railway) or default


def ensure_mysql_schema() -> None:
    if os.getenv("DATABASE_ENGINE", "sqlite").strip().lower() != "mysql":
        return
    if os.getenv("MYSQL_AUTO_INIT", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        return

    schema_path = Path(__file__).with_name("schema_mysql.sql")
    statements = [item.strip() for item in schema_path.read_text(encoding="utf-8").split(";") if item.strip()]
    connection = pymysql.connect(
        host=_setting("MYSQL_HOST", "MYSQLHOST", "127.0.0.1"),
        port=int(_setting("MYSQL_PORT", "MYSQLPORT", "3306")),
        user=_setting("MYSQL_USER", "MYSQLUSER", "root"),
        password=_setting("MYSQL_PASSWORD", "MYSQLPASSWORD"),
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                try:
                    cursor.execute(statement)
                except pymysql.err.OperationalError as exc:
                    if exc.args[0] != 1050:  # table already exists
                        raise
    finally:
        connection.close()
