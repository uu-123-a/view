"""岗位目录、收藏与简历匹配数据访问层。"""
from __future__ import annotations

import json
import sqlite3

from .user_repository import DATABASE_PATH


SEED_JOBS = [
    ("多模态算法工程师", "星云智能", "北京", "25K-45K", "3-5年", "硕士", ["Python", "PyTorch", "Transformer", "多模态", "计算机视觉"], "负责视觉语言模型训练、评测与业务落地，建设多模态数据和推理链路。"),
    ("大模型应用工程师", "启明科技", "上海", "22K-40K", "1-3年", "本科", ["Python", "RAG", "LangChain", "FastAPI", "向量数据库"], "建设企业知识库、智能问答与 Agent 应用，持续优化召回质量和响应性能。"),
    ("机器学习平台工程师", "云帆数据", "杭州", "24K-42K", "3-5年", "本科", ["Python", "Docker", "Kubernetes", "Linux", "MLOps"], "负责模型训练、部署、监控平台和工程效率体系建设。"),
    ("前端开发工程师", "极光互联", "深圳", "18K-32K", "1-3年", "本科", ["React", "TypeScript", "Vue", "Vite", "可视化"], "负责 AI 产品工作台与数据可视化页面，持续改善交互体验和前端性能。"),
    ("NLP算法工程师", "智言科技", "成都", "20K-36K", "1-3年", "硕士", ["Python", "NLP", "Transformer", "大模型", "模型微调"], "负责文本理解、信息抽取、模型微调与离线评测。"),
    ("后端开发工程师", "远航网络", "武汉", "16K-30K", "1-3年", "本科", ["Python", "Flask", "MySQL", "Redis", "Docker"], "开发高可用业务接口、异步任务与数据服务，保障系统稳定性。"),
]


class JobRepository:
    def __init__(self) -> None:
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,company TEXT NOT NULL,
                city TEXT NOT NULL,salary TEXT NOT NULL,experience TEXT NOT NULL,education TEXT NOT NULL,
                skills_json TEXT NOT NULL,description TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS saved_jobs(
                user_id INTEGER NOT NULL,job_id INTEGER NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id,job_id),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE)""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_city_title ON jobs(city,title)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_created ON saved_jobs(user_id,created_at DESC)")
            if connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
                connection.executemany("INSERT INTO jobs(title,company,city,salary,experience,education,skills_json,description) VALUES(?,?,?,?,?,?,?,?)", [(a,b,c,d,e,f,json.dumps(g,ensure_ascii=False),h) for a,b,c,d,e,f,g,h in SEED_JOBS])
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _item(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["skills"] = json.loads(item.pop("skills_json"))
        item["saved"] = bool(item.get("saved", 0))
        return item

    def list(self, user_id: int, keyword: str = "", city: str = "") -> list[dict]:
        sql = "SELECT j.*,EXISTS(SELECT 1 FROM saved_jobs s WHERE s.job_id=j.id AND s.user_id=?) saved FROM jobs j WHERE j.enabled=1"
        args: list[object] = [user_id]
        if keyword:
            sql += " AND (j.title LIKE ? OR j.company LIKE ? OR j.skills_json LIKE ?)"
            value = f"%{keyword}%"; args.extend([value, value, value])
        if city:
            sql += " AND j.city=?"; args.append(city)
        sql += " ORDER BY j.id"
        with self._connect() as connection:
            rows = connection.execute(sql, args).fetchall()
        return [self._item(row) for row in rows]

    def get(self, user_id: int, job_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT j.*,EXISTS(SELECT 1 FROM saved_jobs s WHERE s.job_id=j.id AND s.user_id=?) saved FROM jobs j WHERE j.id=? AND j.enabled=1", (user_id, job_id)).fetchone()
        return self._item(row) if row else None

    def save(self, user_id: int, job_id: int, value: bool) -> bool:
        with self._connect() as connection:
            if not connection.execute("SELECT 1 FROM jobs WHERE id=? AND enabled=1", (job_id,)).fetchone():
                return False
            if value:
                connection.execute("INSERT OR IGNORE INTO saved_jobs(user_id,job_id) VALUES(?,?)", (user_id, job_id))
            else:
                connection.execute("DELETE FROM saved_jobs WHERE user_id=? AND job_id=?", (user_id, job_id))
        return True

    def admin_list(self, search: str = "") -> list[dict]:
        sql = "SELECT j.*,(SELECT COUNT(*) FROM saved_jobs s WHERE s.job_id=j.id) saved_count FROM jobs j"
        args: list[object] = []
        if search:
            sql += " WHERE j.title LIKE ? OR j.company LIKE ? OR j.city LIKE ? OR j.skills_json LIKE ?"
            value = f"%{search}%"; args = [value, value, value, value]
        sql += " ORDER BY j.id DESC"
        with self._connect() as connection: rows = connection.execute(sql, args).fetchall()
        return [self._item(row) for row in rows]

    def create(self, data: dict) -> dict:
        with self._connect() as connection:
            cursor = connection.execute("INSERT INTO jobs(title,company,city,salary,experience,education,skills_json,description,enabled) VALUES(?,?,?,?,?,?,?,?,?)", (data["title"],data["company"],data["city"],data["salary"],data["experience"],data["education"],json.dumps(data["skills"],ensure_ascii=False),data["description"],data["enabled"]))
            row = connection.execute("SELECT j.*,0 saved_count FROM jobs j WHERE id=?", (cursor.lastrowid,)).fetchone()
        return self._item(row)

    def update(self, job_id: int, data: dict) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("UPDATE jobs SET title=?,company=?,city=?,salary=?,experience=?,education=?,skills_json=?,description=?,enabled=? WHERE id=?", (data["title"],data["company"],data["city"],data["salary"],data["experience"],data["education"],json.dumps(data["skills"],ensure_ascii=False),data["description"],data["enabled"],job_id))
        return cursor.rowcount > 0

    def delete(self, job_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        return cursor.rowcount > 0

