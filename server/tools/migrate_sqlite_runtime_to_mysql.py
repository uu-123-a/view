"""Build and verify MySQL runtime databases from the current SQLite data."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
SAFE = re.compile(r"^[A-Za-z0-9_]+$")
LONG_TEXT_HINTS = ("json", "content", "resume", "question", "answer", "description", "feedback", "improvement", "message", "notes", "note", "summary")


def safe(value: str) -> str:
    if not SAFE.fullmatch(value):
        raise ValueError(f"不安全的数据库标识符: {value}")
    return value


def mysql_connection(database: str | None = None):
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=database,
        charset="utf8mb4",
        autocommit=False,
    )


def indexed_columns(source: sqlite3.Connection, table: str) -> set[str]:
    result: set[str] = set()
    for index in source.execute(f"PRAGMA index_list(`{safe(table)}`)").fetchall():
        if index[2]:
            result.update(row[2] for row in source.execute(f"PRAGMA index_info(`{safe(index[1])}`)").fetchall())
    return result


def column_type(name: str, declared: str, primary: bool, indexed: bool) -> str:
    value = (declared or "TEXT").upper()
    lower = name.lower()
    if lower.endswith("_at"):
        return "DATETIME"
    if lower in {"date", "week_start"}:
        return "DATE"
    if "INT" in value:
        return "BIGINT"
    if any(token in value for token in ("REAL", "FLOA", "DOUB")):
        return "DOUBLE"
    if "BLOB" in value:
        return "LONGBLOB"
    if primary or indexed:
        return "VARCHAR(191)"
    if any(hint in lower for hint in LONG_TEXT_HINTS):
        return "LONGTEXT"
    return "VARCHAR(500)"


def normalize_value(value, mysql_type: str):
    if value is None or not isinstance(value, str):
        return value
    if mysql_type == "DATETIME":
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return value
    return value


def default_clause(raw, mysql_type: str) -> str:
    if raw is None:
        return ""
    if mysql_type in {"LONGTEXT", "LONGBLOB"}:
        return ""
    value = str(raw).strip()
    if value.upper() == "CURRENT_TIMESTAMP":
        return " DEFAULT CURRENT_TIMESTAMP"
    if value.upper() == "NULL":
        return " DEFAULT NULL"
    if re.fullmatch(r"-?\d+(\.\d+)?", value):
        return f" DEFAULT {value}"
    if value.startswith("'") and value.endswith("'"):
        return " DEFAULT " + value
    return ""


def migrate_file(sqlite_path: Path, target_database: str) -> dict[str, int]:
    target_database = safe(target_database)
    server = mysql_connection()
    with server.cursor() as cursor:
        cursor.execute(f"DROP DATABASE IF EXISTS `{target_database}`")
        cursor.execute(f"CREATE DATABASE `{target_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    server.commit()
    server.close()

    counts: dict[str, int] = {}
    with sqlite3.connect(sqlite_path) as source, mysql_connection(target_database) as target:
        tables = [row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            table = safe(table)
            columns = source.execute(f"PRAGMA table_info(`{table}`)").fetchall()
            indexed = indexed_columns(source, table)
            definitions = []
            mysql_types = []
            primary_columns = []
            for column in columns:
                name, declared, not_null, raw_default, primary_order = column[1], column[2], column[3], column[4], column[5]
                mysql_type = column_type(name, declared, bool(primary_order), name in indexed)
                mysql_types.append(mysql_type)
                definition = f"`{safe(name)}` {mysql_type}"
                if primary_order and len([item for item in columns if item[5]]) == 1 and mysql_type == "BIGINT":
                    definition += " AUTO_INCREMENT"
                if not_null or primary_order:
                    definition += " NOT NULL"
                definition += default_clause(raw_default, mysql_type)
                definitions.append(definition)
                if primary_order:
                    primary_columns.append((primary_order, name))
            if primary_columns:
                ordered = [name for _, name in sorted(primary_columns)]
                definitions.append("PRIMARY KEY (" + ",".join(f"`{safe(name)}`" for name in ordered) + ")")
            for index in source.execute(f"PRAGMA index_list(`{table}`)").fetchall():
                if not index[2] or index[3] == "pk":
                    continue
                names = [row[2] for row in source.execute(f"PRAGMA index_info(`{safe(index[1])}`)").fetchall()]
                if names:
                    definitions.append("UNIQUE KEY `" + safe(index[1]) + "` (" + ",".join(f"`{safe(name)}`" for name in names) + ")")
            with target.cursor() as cursor:
                cursor.execute(f"CREATE TABLE `{table}` ({','.join(definitions)}) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                rows = source.execute(f"SELECT * FROM `{table}`").fetchall()
                if rows:
                    fields = ",".join(f"`{safe(column[1])}`" for column in columns)
                    placeholders = ",".join(["%s"] * len(columns))
                    normalized_rows = [tuple(normalize_value(value, mysql_types[index]) for index, value in enumerate(row)) for row in rows]
                    cursor.executemany(f"INSERT INTO `{table}` ({fields}) VALUES ({placeholders})", normalized_rows)
                counts[table] = len(rows)
        target.commit()
    return counts


def main() -> None:
    business = safe(os.getenv("MYSQL_MIGRATION_DATABASE", "view_next"))
    admin = safe(os.getenv("MYSQL_ADMIN_DATABASE", "view_admin"))
    business_counts = migrate_file(ROOT / "data" / "view.db", business)
    admin_counts = migrate_file(ROOT / "data" / "admin.db", admin)
    print("BUSINESS", business, business_counts)
    print("ADMIN", admin, admin_counts)


if __name__ == "__main__":
    main()
