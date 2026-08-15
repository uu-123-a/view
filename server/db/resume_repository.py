"""SQLite 简历文本与星火分析结果仓储。"""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from .user_repository import DATABASE_PATH


# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class ResumeRepository:
    def __init__(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS resumes (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_resumes_user_created ON resumes(user_id, created_at DESC)"
            )
            connection.execute("""CREATE TABLE IF NOT EXISTS resume_optimizations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,resume_id TEXT NOT NULL,
                job_id INTEGER NOT NULL,target_role TEXT NOT NULL,match_score INTEGER NOT NULL,
                result_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE)""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_resume_optimizations_user_created ON resume_optimizations(user_id,created_at DESC)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _item(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["analysis"] = json.loads(item.pop("analysis_json"))
        return item

    def save(self, user_id: int, filename: str, file_type: str, content: str, analysis: dict) -> dict:
        resume_id = uuid4().hex
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO resumes (id, user_id, filename, file_type, content, analysis_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (resume_id, user_id, filename, file_type, content, json.dumps(analysis, ensure_ascii=False)),
            )
            row = connection.execute(
                "SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
            ).fetchone()
        return self._item(row)

    def list_by_user(self, user_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM resumes WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
        return [self._item(row) for row in rows]

    def delete(self, resume_id: str, user_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
            )
        return cursor.rowcount > 0

    def get(self, resume_id: str, user_id: int) -> dict | None:
        with self._connect() as connection:
            row=connection.execute("SELECT * FROM resumes WHERE id=? AND user_id=?",(resume_id,user_id)).fetchone()
        return self._item(row) if row else None

    def rename(self,resume_id:str,user_id:int,filename:str)->bool:
        with self._connect() as connection:cursor=connection.execute("UPDATE resumes SET filename=? WHERE id=? AND user_id=?",(filename,resume_id,user_id))
        return cursor.rowcount>0

    def save_optimization(self,user_id:int,resume_id:str,job_id:int,target_role:str,result:dict)->dict:
        with self._connect() as connection:
            cursor=connection.execute("INSERT INTO resume_optimizations(user_id,resume_id,job_id,target_role,match_score,result_json) VALUES(?,?,?,?,?,?)",(user_id,resume_id,job_id,target_role,int(result["match_score"]),json.dumps(result,ensure_ascii=False)))
            row=connection.execute("SELECT * FROM resume_optimizations WHERE id=? AND user_id=?",(cursor.lastrowid,user_id)).fetchone()
        item=dict(row);item["result"]=json.loads(item.pop("result_json"));return item

    def optimizations(self,user_id:int)->list[dict]:
        with self._connect() as connection:rows=connection.execute("""SELECT o.id,o.resume_id,o.job_id,o.target_role,o.match_score,o.result_json,o.created_at,r.filename
            FROM resume_optimizations o JOIN resumes r ON r.id=o.resume_id WHERE o.user_id=? ORDER BY o.created_at DESC LIMIT 20""",(user_id,)).fetchall()
        result=[]
        for row in rows:item=dict(row);item["result"]=json.loads(item.pop("result_json"));result.append(item)
        return result
