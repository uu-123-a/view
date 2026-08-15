"""Administrator identities stored separately from ordinary application users."""
import sqlite3
from pathlib import Path
from werkzeug.security import check_password_hash
from .user_repository import DATABASE_PATH as USER_DATABASE_PATH

ADMIN_DATABASE_PATH=Path(__file__).resolve().parents[1]/"data"/"admin.db"
# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class AdminRepository:
 def __init__(self):
  ADMIN_DATABASE_PATH.parent.mkdir(parents=True,exist_ok=True)
  with self._connect() as c:
   c.execute("CREATE TABLE IF NOT EXISTS administrators(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE COLLATE NOCASE,password_hash TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
   c.execute("CREATE INDEX IF NOT EXISTS idx_administrators_email_active ON administrators(email,active)")
  self._migrate_legacy()
 @staticmethod
 def _connect():c=sqlite3.connect(ADMIN_DATABASE_PATH,timeout=15);c.row_factory=sqlite3.Row;return c
 def _migrate_legacy(self):
  if not USER_DATABASE_PATH.exists():return
  with sqlite3.connect(USER_DATABASE_PATH) as u:
   cols={r[1] for r in u.execute("PRAGMA table_info(users)")}
   if "is_admin" not in cols:return
   rows=u.execute("SELECT name,email,password_hash,created_at FROM users WHERE is_admin=1").fetchall()
  with self._connect() as a:a.executemany("INSERT OR IGNORE INTO administrators(name,email,password_hash,created_at) VALUES(?,?,?,?)",rows)
 def authenticate(self,email,password):
  with self._connect() as c:r=c.execute("SELECT * FROM administrators WHERE email=? AND active=1",(email,)).fetchone()
  if not r or not check_password_hash(r['password_hash'],password):return None
  return {'id':r['id'],'name':r['name'],'email':r['email'],'role':'administrator'}
 def get(self,admin_id):
  with self._connect() as c:r=c.execute("SELECT id,name,email FROM administrators WHERE id=? AND active=1",(admin_id,)).fetchone()
  return {**dict(r),'role':'administrator'} if r else None
 def list_all(self):
  with self._connect() as c:rows=c.execute("SELECT id,name,email,active,created_at FROM administrators ORDER BY id").fetchall()
  return [{**dict(r),'active':bool(r['active'])} for r in rows]

repository=AdminRepository()
def current_admin(session):
 admin_id=session.get('admin_id');return repository.get(admin_id) if isinstance(admin_id,int) else None
