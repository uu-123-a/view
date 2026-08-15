"""职业助手会话、消息和用户上下文。"""
import json
import sqlite3
from uuid import uuid4

from .user_repository import DATABASE_PATH


class CareerRepository:
    def __init__(self):
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS career_conversations(
                id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS career_messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,conversation_id TEXT NOT NULL,user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),content TEXT NOT NULL,source TEXT NOT NULL DEFAULT 'spark',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_id) REFERENCES career_conversations(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_career_conversations_user_updated ON career_conversations(user_id,updated_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_career_messages_conversation_id ON career_messages(conversation_id,id)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect():
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row;connection.execute("PRAGMA foreign_keys=ON");return connection

    def create(self,user_id:int,title:str)->dict:
        conversation_id=uuid4().hex
        with self._connect() as connection:
            connection.execute("INSERT INTO career_conversations(id,user_id,title) VALUES(?,?,?)",(conversation_id,user_id,title[:50]))
        return {"id":conversation_id,"title":title[:50],"messages":[]}

    def list(self,user_id:int)->list[dict]:
        with self._connect() as connection:rows=connection.execute("""SELECT c.id,c.title,c.created_at,c.updated_at,
            (SELECT COUNT(*) FROM career_messages m WHERE m.conversation_id=c.id) message_count
            FROM career_conversations c WHERE c.user_id=? ORDER BY c.updated_at DESC LIMIT 30""",(user_id,)).fetchall()
        return [dict(row) for row in rows]

    def get(self,user_id:int,conversation_id:str)->dict|None:
        with self._connect() as connection:
            row=connection.execute("SELECT * FROM career_conversations WHERE id=? AND user_id=?",(conversation_id,user_id)).fetchone()
            if not row:return None
            messages=connection.execute("SELECT id,role,content,source,created_at FROM career_messages WHERE conversation_id=? AND user_id=? ORDER BY id",(conversation_id,user_id)).fetchall()
        return {**dict(row),"messages":[dict(item) for item in messages]}

    def add(self,user_id:int,conversation_id:str,role:str,content:str,source:str="spark")->bool:
        with self._connect() as connection:
            if not connection.execute("SELECT 1 FROM career_conversations WHERE id=? AND user_id=?",(conversation_id,user_id)).fetchone():return False
            connection.execute("INSERT INTO career_messages(conversation_id,user_id,role,content,source) VALUES(?,?,?,?,?)",(conversation_id,user_id,role,content,source))
            connection.execute("UPDATE career_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(conversation_id,user_id))
        return True

    def delete(self,user_id:int,conversation_id:str)->bool:
        with self._connect() as connection:cursor=connection.execute("DELETE FROM career_conversations WHERE id=? AND user_id=?",(conversation_id,user_id))
        return cursor.rowcount>0

    def context(self,user_id:int)->dict:
        with self._connect() as connection:
            resume=connection.execute("SELECT filename,content,analysis_json FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1",(user_id,)).fetchone()
            reports=connection.execute("""SELECT s.role,r.score,r.report_json FROM interview_reports r JOIN interview_sessions s ON s.id=r.session_id
                WHERE s.user_id=? ORDER BY r.created_at DESC LIMIT 3""",(user_id,)).fetchall()
            mistakes=connection.execute("SELECT skill,COUNT(*) count,ROUND(AVG(best_score)) score FROM mistake_book WHERE user_id=? AND resolved=0 GROUP BY skill ORDER BY count DESC LIMIT 5",(user_id,)).fetchall()
            plan=connection.execute("SELECT target_role,focus_skill,weekly_target FROM training_plans WHERE user_id=?",(user_id,)).fetchone()
        return {"resume":{"filename":resume["filename"],"content":resume["content"][:5000],"analysis":json.loads(resume["analysis_json"])} if resume else None,"reports":[{"role":x["role"],"score":x["score"]} for x in reports],"mistakes":[dict(x) for x in mistakes],"plan":dict(plan) if plan else None}

