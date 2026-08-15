"""SQLite 用户账户仓储。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "view.db"


# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class UserRepository:
    def __init__(self) -> None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
            if "is_admin" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
            connection.execute(
                "UPDATE users SET is_admin = 1 WHERE id = (SELECT id FROM users ORDER BY id LIMIT 1) AND NOT EXISTS (SELECT 1 FROM users WHERE is_admin = 1)"
            )

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _public_user(row: sqlite3.Row) -> dict[str, object]:
        return {"id": row["id"], "name": row["name"], "email": row["email"], "is_admin": bool(row["is_admin"])}

    def create(self, name: str, email: str, password: str) -> dict[str, object]:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                row = connection.execute(
                    "SELECT id, name, email, is_admin FROM users WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError("该邮箱已经注册，请直接登录。") from exc
        return self._public_user(row)

    def authenticate(self, email: str, password: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, email, password_hash, is_admin FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return None
        return self._public_user(row)

    def get(self, user_id: int) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return self._public_user(row) if row else None

    def profile(self, user_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT id,name,email,is_admin,created_at FROM users WHERE id=?", (user_id,)).fetchone()
            if row is None:
                return None
            stats = connection.execute("""SELECT COUNT(*) interviews,
                COALESCE(ROUND(AVG(r.score)),0) average_score,COALESCE(MAX(r.score),0) best_score,
                COALESCE(SUM(s.duration_seconds),0) duration_seconds
                FROM interview_sessions s LEFT JOIN interview_reports r ON r.session_id=s.id
                WHERE s.user_id=? AND s.status='complete' AND s.mode='interview'""", (user_id,)).fetchone()
            extras = connection.execute("""SELECT
                (SELECT COUNT(*) FROM resumes WHERE user_id=?) resumes,
                (SELECT COUNT(*) FROM saved_jobs WHERE user_id=?) saved_jobs,
                (SELECT COUNT(*) FROM mistake_book WHERE user_id=? AND resolved=0) open_mistakes""", (user_id,user_id,user_id)).fetchone()
            jobs = connection.execute("""SELECT j.id,j.title,j.company,j.city,j.salary
                FROM saved_jobs s JOIN jobs j ON j.id=s.job_id WHERE s.user_id=?
                ORDER BY s.created_at DESC LIMIT 5""", (user_id,)).fetchall()
            resumes = connection.execute("SELECT id,filename,file_type,created_at FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (user_id,)).fetchall()
        return {"user": dict(row), "stats": {**dict(stats), **dict(extras)}, "saved_jobs": [dict(item) for item in jobs], "resumes": [dict(item) for item in resumes]}

    def update_name(self, user_id: int, name: str) -> dict | None:
        with self._connect() as connection:
            connection.execute("UPDATE users SET name=? WHERE id=?", (name, user_id))
        return self.get(user_id)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
            if row is None or not check_password_hash(row["password_hash"], current_password):
                return False
            connection.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_password), user_id))
        return True

    def list_all(self):
        with self._connect() as c: rows=c.execute("SELECT id,name,email,is_admin,created_at FROM users ORDER BY id").fetchall()
        return [{**dict(r),"is_admin":bool(r["is_admin"])} for r in rows]

    def set_admin(self,user_id:int,value:bool)->bool:
        with self._connect() as c:
            if not value:
                admins=c.execute("SELECT COUNT(*) FROM users WHERE is_admin=1").fetchone()[0]
                current=c.execute("SELECT is_admin FROM users WHERE id=?",(user_id,)).fetchone()
                if current and current[0] and admins<=1: raise ValueError("系统至少需要保留一名管理员。")
            cur=c.execute("UPDATE users SET is_admin=? WHERE id=?",(int(value),user_id))
        return cur.rowcount>0
