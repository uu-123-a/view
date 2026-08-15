"""用户求职投递看板数据访问层。"""
import sqlite3
from .user_repository import DATABASE_PATH

STATUSES=("wishlist","applied","written","interview","offer","closed")


class ApplicationRepository:
    def __init__(self):
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS job_applications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,job_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'wishlist',interview_at TEXT,notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,UNIQUE(user_id,job_id))""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_user_status_updated ON job_applications(user_id,status,updated_at DESC)")
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect():
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row;connection.execute("PRAGMA foreign_keys=ON");return connection

    def list(self,user_id:int)->dict:
        with self._connect() as connection:
            rows=connection.execute("""SELECT a.*,j.title,j.company,j.city,j.salary,j.skills_json,j.enabled
                FROM job_applications a JOIN jobs j ON j.id=a.job_id WHERE a.user_id=? ORDER BY a.updated_at DESC""",(user_id,)).fetchall()
        items=[dict(row) for row in rows];counts={status:0 for status in STATUSES}
        for item in items:counts[item["status"]]+=1
        return {"items":items,"counts":counts,"total":len(items)}

    def create(self,user_id:int,job_id:int)->dict|None:
        with self._connect() as connection:
            if not connection.execute("SELECT 1 FROM jobs WHERE id=? AND enabled=1",(job_id,)).fetchone():return None
            connection.execute("INSERT OR IGNORE INTO job_applications(user_id,job_id) VALUES(?,?)",(user_id,job_id))
            row=connection.execute("SELECT * FROM job_applications WHERE user_id=? AND job_id=?",(user_id,job_id)).fetchone()
        return dict(row)

    def update(self,user_id:int,application_id:int,status:str,interview_at:str|None,notes:str)->bool:
        with self._connect() as connection:cursor=connection.execute("""UPDATE job_applications SET status=?,interview_at=?,notes=?,updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND user_id=?""",(status,interview_at or None,notes,application_id,user_id))
        return cursor.rowcount>0

    def delete(self,user_id:int,application_id:int)->bool:
        with self._connect() as connection:cursor=connection.execute("DELETE FROM job_applications WHERE id=? AND user_id=?",(application_id,user_id))
        return cursor.rowcount>0

