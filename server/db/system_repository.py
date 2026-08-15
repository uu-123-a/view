"""Persistent system switches and sanitized failure events."""
import sqlite3
from .user_repository import DATABASE_PATH

# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class SystemRepository:
    def __init__(self):
        with self._connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS system_events(id INTEGER PRIMARY KEY AUTOINCREMENT,service TEXT NOT NULL,level TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            c.executemany("INSERT OR IGNORE INTO system_settings(key,value) VALUES(?,?)",[("spark_enabled","1"),("whisper_enabled","1")])
            c.execute("CREATE INDEX IF NOT EXISTS idx_system_events_created ON system_events(created_at DESC)")
    @staticmethod
    def _connect():
        c=sqlite3.connect(DATABASE_PATH,timeout=15);c.row_factory=sqlite3.Row;return c
    def enabled(self,key):
        with self._connect() as c:r=c.execute("SELECT value FROM system_settings WHERE key=?",(key,)).fetchone()
        return r is None or r["value"]=="1"
    def settings(self):
        with self._connect() as c: rows=c.execute("SELECT key,value,updated_at FROM system_settings").fetchall()
        return {r["key"]:{"enabled":r["value"]=="1","updated_at":r["updated_at"]} for r in rows}
    def set(self,key,enabled):
        with self._connect() as c:c.execute("INSERT INTO system_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP",(key,"1" if enabled else "0"))
    def log(self,service,message):
        with self._connect() as c:
            c.execute("INSERT INTO system_events(service,level,message) VALUES(?,'error',?)",(service,str(message)[:500]))
            c.execute("DELETE FROM system_events WHERE id NOT IN (SELECT id FROM system_events ORDER BY id DESC LIMIT 200)")
    def events(self):
        with self._connect() as c:rows=c.execute("SELECT id,service,level,message,created_at FROM system_events ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]
