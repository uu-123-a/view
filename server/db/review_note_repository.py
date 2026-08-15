"""面试复盘笔记与行动项。"""
import json
import sqlite3
from .user_repository import DATABASE_PATH


class ReviewNoteRepository:
    def __init__(self):
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS interview_notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,session_id TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',actions_json TEXT NOT NULL DEFAULT '[]',tags_json TEXT NOT NULL DEFAULT '[]',
                starred INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,UNIQUE(user_id,session_id))""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_interview_notes_user_starred_updated ON interview_notes(user_id,starred,updated_at DESC)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect():
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row;connection.execute("PRAGMA foreign_keys=ON");return connection

    @staticmethod
    def _item(row):
        item=dict(row);item["actions"]=json.loads(item.pop("actions_json"));item["tags"]=json.loads(item.pop("tags_json"));item["starred"]=bool(item["starred"]);return item

    def list_notes(self,user_id:int,search:str="")->list[dict]:
        sql="""SELECT n.*,s.role,s.interview_type,s.completed_at,r.score FROM interview_notes n
            JOIN interview_sessions s ON s.id=n.session_id LEFT JOIN interview_reports r ON r.session_id=s.id WHERE n.user_id=?""";args=[user_id]
        if search:sql+=" AND (n.note LIKE ? OR n.tags_json LIKE ? OR s.role LIKE ?)";value=f"%{search}%";args.extend([value,value,value])
        sql+=" ORDER BY n.starred DESC,n.updated_at DESC"
        with self._connect() as connection:rows=connection.execute(sql,args).fetchall()
        return [self._item(row) for row in rows]

    def available(self,user_id:int)->list[dict]:
        with self._connect() as connection:rows=connection.execute("""SELECT s.id,s.role,s.interview_type,s.completed_at,s.created_at,COALESCE(r.score,0) score,
            EXISTS(SELECT 1 FROM interview_notes n WHERE n.session_id=s.id AND n.user_id=s.user_id) has_note
            FROM interview_sessions s LEFT JOIN interview_reports r ON r.session_id=s.id WHERE s.user_id=? AND s.status='complete'
            ORDER BY COALESCE(s.completed_at,s.created_at) DESC LIMIT 50""",(user_id,)).fetchall()
        return [dict(row) for row in rows]

    def save(self,user_id:int,session_id:str,note:str,actions:list[str],tags:list[str],starred:bool)->dict|None:
        with self._connect() as connection:
            if not connection.execute("SELECT 1 FROM interview_sessions WHERE id=? AND user_id=? AND status='complete'",(session_id,user_id)).fetchone():return None
            connection.execute("""INSERT INTO interview_notes(user_id,session_id,note,actions_json,tags_json,starred) VALUES(?,?,?,?,?,?)
                ON CONFLICT(user_id,session_id) DO UPDATE SET note=excluded.note,actions_json=excluded.actions_json,tags_json=excluded.tags_json,starred=excluded.starred,updated_at=CURRENT_TIMESTAMP""",(user_id,session_id,note,json.dumps(actions,ensure_ascii=False),json.dumps(tags,ensure_ascii=False),int(starred)))
            row=connection.execute("""SELECT n.*,s.role,s.interview_type,s.completed_at,r.score FROM interview_notes n JOIN interview_sessions s ON s.id=n.session_id LEFT JOIN interview_reports r ON r.session_id=s.id WHERE n.user_id=? AND n.session_id=?""",(user_id,session_id)).fetchone()
        return self._item(row)

    def delete(self,user_id:int,note_id:int)->bool:
        with self._connect() as connection:cursor=connection.execute("DELETE FROM interview_notes WHERE id=? AND user_id=?",(note_id,user_id))
        return cursor.rowcount>0
