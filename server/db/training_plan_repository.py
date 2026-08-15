"""Weekly training plan and owned task persistence."""
import sqlite3
from datetime import date,timedelta
from .user_repository import DATABASE_PATH

def week_start():
 today=date.today();return (today-timedelta(days=today.weekday())).isoformat()
# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class TrainingPlanRepository:
 def __init__(self):
  with self._connect() as c:
   c.execute("CREATE TABLE IF NOT EXISTS training_plans(user_id INTEGER PRIMARY KEY,target_role TEXT NOT NULL,weekly_target INTEGER NOT NULL,focus_skill TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
   c.execute("CREATE TABLE IF NOT EXISTS training_tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,week_start TEXT NOT NULL,task_number INTEGER NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,completed INTEGER NOT NULL DEFAULT 0,completed_at TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,UNIQUE(user_id,week_start,task_number))")
   c.execute("CREATE INDEX IF NOT EXISTS idx_training_tasks_user_week ON training_tasks(user_id,week_start,task_number)");c.execute("PRAGMA optimize")
 @staticmethod
 def _connect():c=sqlite3.connect(DATABASE_PATH,timeout=15);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
 def save(self,user_id,role,target,skill):
  target=max(1,min(7,int(target)));week=week_start()
  with self._connect() as c:
   c.execute("INSERT INTO training_plans(user_id,target_role,weekly_target,focus_skill) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET target_role=excluded.target_role,weekly_target=excluded.weekly_target,focus_skill=excluded.focus_skill,updated_at=CURRENT_TIMESTAMP",(user_id,role,target,skill))
   c.execute("DELETE FROM training_tasks WHERE user_id=? AND week_start=?",(user_id,week))
   tasks=[]
   for n in range(1,target+1):
    kind='完整模拟面试' if n%3==1 else f'{skill}专项训练' if n%3==2 else '错题复盘与重答'
    tasks.append((user_id,week,n,kind,f'围绕{role}完成第 {n} 次训练，重点提升{skill}。'))
   c.executemany("INSERT INTO training_tasks(user_id,week_start,task_number,title,description) VALUES(?,?,?,?,?)",tasks)
  return self.get(user_id)
 def get(self,user_id):
  week=week_start()
  with self._connect() as c:
   plan=c.execute("SELECT target_role,weekly_target,focus_skill,updated_at FROM training_plans WHERE user_id=?",(user_id,)).fetchone()
   tasks=c.execute("SELECT id,task_number,title,description,completed FROM training_tasks WHERE user_id=? AND week_start=? ORDER BY task_number",(user_id,week)).fetchall()
  return {'plan':dict(plan) if plan else None,'week_start':week,'tasks':[{**dict(t),'completed':bool(t['completed'])} for t in tasks]}
 def complete(self,user_id,task_id,value):
  with self._connect() as c:cur=c.execute("UPDATE training_tasks SET completed=?,completed_at=CASE WHEN ?=1 THEN CURRENT_TIMESTAMP ELSE NULL END WHERE id=? AND user_id=?",(int(value),int(value),task_id,user_id))
  return cur.rowcount>0
