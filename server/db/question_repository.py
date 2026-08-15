"""SQLite-backed local interview question bank."""

from __future__ import annotations

import sqlite3

from .user_repository import DATABASE_PATH

SEED_QUESTIONS = [
    ("通用", "技术面", "基础", "请介绍一个最能体现你岗位能力的项目，并说明你的具体职责。"),
    ("通用", "技术面", "中等", "遇到线上故障时，你会如何确定排查顺序并控制影响范围？"),
    ("通用", "技术面", "困难", "请设计一个高可用服务，并说明容量规划、降级和容灾策略。"),
    ("后端", "技术面", "基础", "HTTP 常见状态码分别适用于哪些场景？"),
    ("后端", "技术面", "中等", "如何定位并优化一个响应缓慢的数据库接口？"),
    ("后端", "技术面", "困难", "高并发写入场景下，如何保证一致性并避免热点问题？"),
    ("前端", "技术面", "基础", "请解释组件状态与属性的区别。"),
    ("前端", "技术面", "中等", "如何分析和优化首屏加载速度？"),
    ("前端", "技术面", "困难", "请设计大型前端应用的状态管理和微前端边界。"),
    ("人工智能", "技术面", "基础", "训练集、验证集和测试集分别有什么作用？"),
    ("人工智能", "技术面", "中等", "模型上线后效果下降，你会如何定位数据漂移和服务问题？"),
    ("人工智能", "技术面", "困难", "请设计一个可评估、可追踪且支持回退的 RAG 系统。"),
    ("通用", "HR 面", "基础", "为什么选择这个岗位？"),
    ("通用", "HR 面", "中等", "请讲述一次团队意见冲突以及你的处理方式。"),
    ("通用", "HR 面", "困难", "当业务目标与技术质量冲突时，你会如何推动决策？"),
]


# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class QuestionRepository:
    def __init__(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    interview_type TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    question TEXT NOT NULL UNIQUE,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO question_bank (category, interview_type, difficulty, question) VALUES (?, ?, ?, ?)",
                SEED_QUESTIONS,
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_question_bank_lookup ON question_bank(enabled, interview_type, difficulty, category)"
            )
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH, timeout=15)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def category_for_role(role: str) -> str:
        lowered = role.lower()
        if any(term in lowered for term in ("python", "java", "后端", "服务端", "数据库")):
            return "后端"
        if any(term in lowered for term in ("前端", "react", "vue", "web")):
            return "前端"
        if any(term in lowered for term in ("算法", "模型", "ai", "人工智能", "nlp", "多模态")):
            return "人工智能"
        return "通用"

    def select(self, role: str, interview_type: str, difficulty: str, used: list[str]) -> str | None:
        category = self.category_for_role(role)
        placeholders = ",".join("?" for _ in used)
        exclusion = f"AND question NOT IN ({placeholders})" if used else ""
        query = f"""
            SELECT question FROM question_bank
            WHERE enabled = 1 AND difficulty = ?
              AND interview_type IN (?, '技术面')
              AND category IN (?, '通用') {exclusion}
            ORDER BY CASE WHEN category = ? THEN 0 ELSE 1 END, id
            LIMIT 1
        """
        params = [difficulty, interview_type, category, *used, category]
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return str(row["question"]) if row else None

    def list(self, search: str = "") -> list[dict]:
        pattern = f"%{search.strip()}%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM question_bank WHERE question LIKE ? OR category LIKE ? ORDER BY id DESC LIMIT 500",
                (pattern, pattern),
            ).fetchall()
        return [dict(row) for row in rows]

    def create(self, data: dict) -> dict:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO question_bank(category, interview_type, difficulty, question, enabled) VALUES(?,?,?,?,?)",
                (data["category"], data["interview_type"], data["difficulty"], data["question"], int(data.get("enabled", 1))),
            )
            return dict(connection.execute("SELECT * FROM question_bank WHERE id=?", (cursor.lastrowid,)).fetchone())

    def update(self, question_id: int, data: dict) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE question_bank SET category=?, interview_type=?, difficulty=?, question=?, enabled=? WHERE id=?",
                (data["category"], data["interview_type"], data["difficulty"], data["question"], int(data.get("enabled", 1)), question_id),
            )
        return cursor.rowcount > 0

    def delete(self, question_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM question_bank WHERE id=?", (question_id,))
        return cursor.rowcount > 0
