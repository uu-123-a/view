"""面试日程与准备事项数据访问层。"""
import sqlite3
from .user_repository import DATABASE_PATH


class ScheduleRepository:
    def __init__(self):
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS schedule_tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,application_id INTEGER,
                title TEXT NOT NULL,due_at TEXT NOT NULL,task_type TEXT NOT NULL DEFAULT 'prepare',
                notes TEXT NOT NULL DEFAULT '',completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(application_id) REFERENCES job_applications(id) ON DELETE CASCADE)""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_schedule_tasks_user_due_completed ON schedule_tasks(user_id,completed,due_at)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect():
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row;connection.execute("PRAGMA foreign_keys=ON");return connection

    def sync_interviews(self,user_id:int)->None:
        with self._connect() as connection:
            rows=connection.execute("""SELECT a.id,a.interview_at,j.title,j.company FROM job_applications a JOIN jobs j ON j.id=a.job_id
                WHERE a.user_id=? AND a.interview_at IS NOT NULL AND a.interview_at!='' AND a.status IN ('written','interview')""",(user_id,)).fetchall()
            for row in rows:
                exists=connection.execute("SELECT 1 FROM schedule_tasks WHERE user_id=? AND application_id=? AND task_type='interview'",(user_id,row["id"])).fetchone()
                if exists:connection.execute("UPDATE schedule_tasks SET title=?,due_at=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND application_id=? AND task_type='interview'",(f"{row['company']} · {row['title']} 面试",row["interview_at"],user_id,row["id"]))
                else:connection.execute("INSERT INTO schedule_tasks(user_id,application_id,title,due_at,task_type,notes) VALUES(?,?,?,?,?,?)",(user_id,row["id"],f"{row['company']} · {row['title']} 面试",row["interview_at"],"interview","提前完成岗位知识、项目深挖和模拟面试准备。"))

    def list(self,user_id:int)->dict:
        self.sync_interviews(user_id)
        with self._connect() as connection:
            rows=connection.execute("""SELECT t.*,j.title job_title,j.company,j.salary FROM schedule_tasks t
                LEFT JOIN job_applications a ON a.id=t.application_id LEFT JOIN jobs j ON j.id=a.job_id
                WHERE t.user_id=? ORDER BY t.completed,t.due_at""",(user_id,)).fetchall()
        items=[{**dict(row),"completed":bool(row["completed"])} for row in rows]
        return {"items":items,"pending":sum(not x["completed"] for x in items),"completed":sum(x["completed"] for x in items)}

    def create(self,user_id:int,title:str,due_at:str,notes:str)->dict:
        with self._connect() as connection:
            cursor=connection.execute("INSERT INTO schedule_tasks(user_id,title,due_at,notes) VALUES(?,?,?,?)",(user_id,title,due_at,notes))
            row=connection.execute("SELECT * FROM schedule_tasks WHERE id=? AND user_id=?",(cursor.lastrowid,user_id)).fetchone()
        return dict(row)

    def complete(self,user_id:int,task_id:int,value:bool)->bool:
        with self._connect() as connection:cursor=connection.execute("UPDATE schedule_tasks SET completed=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(int(value),task_id,user_id))
        return cursor.rowcount>0

    def delete(self,user_id:int,task_id:int)->bool:
        with self._connect() as connection:cursor=connection.execute("DELETE FROM schedule_tasks WHERE id=? AND user_id=? AND task_type='prepare'",(task_id,user_id))
        return cursor.rowcount>0

