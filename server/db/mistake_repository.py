"""Owned low-score answers and retry history."""
import sqlite3
from .user_repository import DATABASE_PATH

# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class MistakeRepository:
 def __init__(self):
  with self._connect() as c:
   c.execute("CREATE TABLE IF NOT EXISTS mistake_book(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,session_id TEXT NOT NULL,turn_number INTEGER NOT NULL,skill TEXT NOT NULL,question TEXT NOT NULL,original_answer TEXT NOT NULL,original_score INTEGER NOT NULL,feedback TEXT NOT NULL,improvement TEXT NOT NULL,best_score INTEGER NOT NULL,resolved INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,UNIQUE(user_id,session_id,turn_number))")
   c.execute("CREATE TABLE IF NOT EXISTS mistake_retries(id INTEGER PRIMARY KEY AUTOINCREMENT,mistake_id INTEGER NOT NULL,user_id INTEGER NOT NULL,answer TEXT NOT NULL,score INTEGER NOT NULL,feedback TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(mistake_id) REFERENCES mistake_book(id) ON DELETE CASCADE,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
   c.execute("CREATE INDEX IF NOT EXISTS idx_mistakes_user_resolved_score ON mistake_book(user_id,resolved,original_score,created_at DESC)");c.execute("PRAGMA optimize")
 @staticmethod
 def _connect():c=sqlite3.connect(DATABASE_PATH,timeout=15);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
 def add(self,user_id,session_id,turn,skill='综合能力'):
  e=turn.get('evaluation') or {};score=int(e.get('score',0))
  if score>=75:return
  with self._connect() as c:c.execute("INSERT OR IGNORE INTO mistake_book(user_id,session_id,turn_number,skill,question,original_answer,original_score,feedback,improvement,best_score) VALUES(?,?,?,?,?,?,?,?,?,?)",(user_id,session_id,turn['turn_number'],skill,turn['question'],turn['answer'],score,str(e.get('feedback','')),str(e.get('improvement','')),score))
 def list(self,user_id,skill=''):
  sql="SELECT * FROM mistake_book WHERE user_id=?";args=[user_id]
  if skill:sql+=" AND skill=?";args.append(skill)
  sql+=" ORDER BY resolved,created_at DESC"
  with self._connect() as c:rows=c.execute(sql,args).fetchall()
  return [{**dict(r),'resolved':bool(r['resolved'])} for r in rows]
 def get(self,user_id,mistake_id):
  with self._connect() as c:r=c.execute("SELECT * FROM mistake_book WHERE id=? AND user_id=?",(mistake_id,user_id)).fetchone()
  return dict(r) if r else None
 def retry(self,user_id,mistake_id,answer,evaluation):
  score=int(evaluation['score'])
  with self._connect() as c:
   if not c.execute("SELECT 1 FROM mistake_book WHERE id=? AND user_id=?",(mistake_id,user_id)).fetchone():return False
   c.execute("INSERT INTO mistake_retries(mistake_id,user_id,answer,score,feedback) VALUES(?,?,?,?,?)",(mistake_id,user_id,answer,score,evaluation.get('feedback','')))
   c.execute("UPDATE mistake_book SET best_score=MAX(best_score,?),resolved=CASE WHEN ?>=80 THEN 1 ELSE resolved END,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(score,score,mistake_id,user_id))
  return True
