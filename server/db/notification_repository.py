"""用户通知持久化与业务提醒同步。"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from .user_repository import DATABASE_PATH


class NotificationRepository:
    def __init__(self) -> None:
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS notifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,source_key TEXT NOT NULL,
                kind TEXT NOT NULL,title TEXT NOT NULL,content TEXT NOT NULL,target TEXT NOT NULL DEFAULT 'home',
                is_read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,UNIQUE(user_id,source_key))""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created ON notifications(user_id,is_read,created_at DESC)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON");return connection

    @staticmethod
    def _week_start() -> str:
        today=date.today();return (today-timedelta(days=today.weekday())).isoformat()

    @staticmethod
    def _upsert(connection: sqlite3.Connection,user_id: int,key: str,kind: str,title: str,content: str,target: str) -> None:
        connection.execute("""INSERT INTO notifications(user_id,source_key,kind,title,content,target)
            VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,source_key) DO UPDATE SET
            title=excluded.title,content=excluded.content,target=excluded.target,updated_at=CURRENT_TIMESTAMP""",
            (user_id,key,kind,title,content,target))

    def sync(self,user_id: int) -> None:
        with self._connect() as connection:
            week=self._week_start()
            plan=connection.execute("""SELECT COUNT(*) total,SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) done
                FROM training_tasks WHERE user_id=? AND week_start=?""",(user_id,week)).fetchone()
            if plan and plan["total"]:
                remaining=int(plan["total"])-int(plan["done"] or 0)
                if remaining>0:self._upsert(connection,user_id,f"training:{week}","training","本周训练计划待完成",f"本周还有 {remaining} 项训练任务，完成后会更新你的成长轨迹。","home")
            mistakes=connection.execute("SELECT COUNT(*) count FROM mistake_book WHERE user_id=? AND resolved=0",(user_id,)).fetchone()["count"]
            if mistakes:self._upsert(connection,user_id,"mistakes:open","mistake","错题等待复盘",f"你有 {mistakes} 道低分题尚未掌握，建议完成一次重新作答。","mistakes")
            report=connection.execute("""SELECT s.id,s.role,r.score,r.created_at FROM interview_reports r
                JOIN interview_sessions s ON s.id=r.session_id WHERE s.user_id=? ORDER BY r.created_at DESC LIMIT 1""",(user_id,)).fetchone()
            if report:self._upsert(connection,user_id,f"report:{report['id']}","report","新的面试报告已生成",f"{report['role']} 面试得分 {report['score']}，查看报告并安排下一步训练。","history")
            upcoming=connection.execute("""SELECT t.id,t.title,t.due_at FROM schedule_tasks t
                WHERE t.user_id=? AND t.completed=0 AND t.due_at>=datetime('now','localtime')
                AND t.due_at<=datetime('now','localtime','3 days') ORDER BY t.due_at LIMIT 1""",(user_id,)).fetchone()
            if upcoming:self._upsert(connection,user_id,f"schedule:{upcoming['id']}","schedule","近期面试日程提醒",f"{upcoming['title']} 将在 {upcoming['due_at'].replace('T',' ')} 进行，请及时完成准备。","schedule")

    def list(self,user_id: int) -> dict:
        self.sync(user_id)
        with self._connect() as connection:
            rows=connection.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY is_read,created_at DESC,id DESC LIMIT 50",(user_id,)).fetchall()
        items=[{**dict(row),"is_read":bool(row["is_read"])} for row in rows]
        return {"items":items,"unread":sum(not item["is_read"] for item in items)}

    def mark(self,user_id: int,notification_id: int) -> bool:
        with self._connect() as connection:cursor=connection.execute("UPDATE notifications SET is_read=1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(notification_id,user_id))
        return cursor.rowcount>0

    def mark_all(self,user_id: int) -> int:
        with self._connect() as connection:cursor=connection.execute("UPDATE notifications SET is_read=1,updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND is_read=0",(user_id,))
        return cursor.rowcount
