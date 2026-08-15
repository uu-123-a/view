"""Small DB-API compatibility layer used while repositories move to MySQL.

Repository queries keep sqlite-style ``?`` placeholders; this module translates
the small, audited SQLite dialect subset used by the application.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pymysql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
_sqlite_connect = sqlite3.connect


class Row(dict):
    def __init__(self, value=()):
        super().__init__(value)
        for key, item in list(self.items()):
            if isinstance(item, datetime):
                self[key] = item.isoformat(sep=" ")
            elif isinstance(item, date):
                self[key] = item.isoformat()

    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cursor=None, rows: list[Row] | None = None):
        self._cursor = cursor
        self._rows = rows
        self.rowcount = 0 if cursor is None else cursor.rowcount
        self.lastrowid = None if cursor is None else cursor.lastrowid

    def fetchone(self):
        if self._rows is not None:
            return self._rows[0] if self._rows else None
        value = self._cursor.fetchone()
        return Row(value) if value is not None else None

    def fetchall(self):
        if self._rows is not None:
            return self._rows
        return [Row(value) for value in self._cursor.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


def _translate(sql: str) -> str | None:
    stripped = sql.strip()
    upper = stripped.upper()
    if upper.startswith(("CREATE TABLE", "CREATE INDEX", "CREATE UNIQUE INDEX", "ALTER TABLE")):
        return None
    if upper.startswith("PRAGMA"):
        return None
    value = sql
    if re.search(r"UPDATE\s+users\s+SET\s+is_admin\s*=\s*1\s+WHERE", value, flags=re.I):
        value = """UPDATE users SET is_admin=1
            WHERE id=(SELECT id FROM (SELECT id FROM users ORDER BY id LIMIT 1) AS first_user)
            AND NOT EXISTS (SELECT 1 FROM (SELECT is_admin FROM users) AS admins WHERE is_admin=1)"""
    value = re.sub(r"\bINSERT\s+OR\s+IGNORE\b", "INSERT IGNORE", value, flags=re.I)
    value = re.sub(r"datetime\('now','localtime','3 days'\)", "DATE_ADD(NOW(), INTERVAL 3 DAY)", value, flags=re.I)
    value = re.sub(r"datetime\('now','localtime'\)", "NOW()", value, flags=re.I)
    value = re.sub(r"\s+AND\s+a\.interview_at\s*!=\s*''", "", value, flags=re.I)
    value = re.sub(r"\bMAX\(best_score\s*,\s*\?\)", "GREATEST(best_score, ?)", value, flags=re.I)
    if re.search(r"\bsystem_settings\b", value, flags=re.I):
        value = re.sub(r"(?<![`\w])key(?![`\w])", "`key`", value, flags=re.I)
    conflict = re.search(r"\s+ON\s+CONFLICT\s*\([^)]*\)\s+DO\s+UPDATE\s+SET\s+(.+)$", value, flags=re.I | re.S)
    if conflict:
        assignments = re.sub(r"excluded\.([A-Za-z_][A-Za-z0-9_]*)", r"VALUES(\1)", conflict.group(1), flags=re.I)
        value = value[:conflict.start()] + " ON DUPLICATE KEY UPDATE " + assignments
    value = value.replace("?", "%s")
    return value


class Connection:
    def __init__(self, database: str):
        self._connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        self.row_factory = Row

    def execute(self, sql: str, params: Iterable[Any] = ()) -> Cursor:
        translated = _translate(sql)
        if translated is None:
            return Cursor(rows=[])
        cursor = self._connection.cursor()
        try:
            cursor.execute(translated, tuple(params))
        except pymysql.err.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        return Cursor(cursor)

    def executemany(self, sql: str, params: Iterable[Iterable[Any]]) -> Cursor:
        translated = _translate(sql)
        if translated is None:
            return Cursor(rows=[])
        cursor = self._connection.cursor()
        try:
            cursor.executemany(translated, [tuple(item) for item in params])
        except pymysql.err.IntegrityError as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc
        return Cursor(cursor)

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self._connection.rollback() if exc_type else self._connection.commit()
        finally:
            self._connection.close()
        return False


def connect_compat(database_path=None, *_args, **_kwargs):
    path = str(database_path or "").lower()
    database = os.getenv("MYSQL_ADMIN_DATABASE", "view_admin") if path.endswith("admin.db") else os.getenv("MYSQL_DATABASE", "view")
    return Connection(database)


def enable_mysql_compat() -> bool:
    if os.getenv("DATABASE_ENGINE", "sqlite").strip().lower() != "mysql":
        return False
    sqlite3.connect = connect_compat
    return True
