"""SQLite 面试会话、逐轮回答与报告仓储。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from .user_repository import DATABASE_PATH


# PyCharm may inject SQL into the strings below. The project uses sqlite3
# directly, so a configured IDE data source is not required for execution.
# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class InterviewRepository:
    def __init__(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    level TEXT NOT NULL,
                    interview_type TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'interview',
                    focus_skill TEXT NOT NULL DEFAULT '',
                    difficulty TEXT NOT NULL DEFAULT '中等',
                    question_strategy TEXT NOT NULL DEFAULT 'spark_first',
                    resume TEXT NOT NULL,
                    current_question TEXT NOT NULL DEFAULT '',
                    current_source TEXT NOT NULL DEFAULT 'fallback',
                    max_questions INTEGER NOT NULL DEFAULT 5,
                    status TEXT NOT NULL DEFAULT 'active',
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            session_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(interview_sessions)").fetchall()
            }
            if "mode" not in session_columns:
                connection.execute("ALTER TABLE interview_sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'interview'")
            if "focus_skill" not in session_columns:
                connection.execute("ALTER TABLE interview_sessions ADD COLUMN focus_skill TEXT NOT NULL DEFAULT ''")
            if "difficulty" not in session_columns:
                connection.execute("ALTER TABLE interview_sessions ADD COLUMN difficulty TEXT NOT NULL DEFAULT '中等'")
            if "question_strategy" not in session_columns:
                connection.execute("ALTER TABLE interview_sessions ADD COLUMN question_strategy TEXT NOT NULL DEFAULT 'spark_first'")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'fallback',
                    evaluation_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
                    UNIQUE (session_id, turn_number)
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(interview_turns)").fetchall()
            }
            if "evaluation_json" not in columns:
                connection.execute(
                    "ALTER TABLE interview_turns ADD COLUMN evaluation_json TEXT NOT NULL DEFAULT '{}'"
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_reports (
                    session_id TEXT PRIMARY KEY,
                    score INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_created ON interview_sessions(user_id, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_mode_completed ON interview_sessions(user_id, mode, completed_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_turns_session_number ON interview_turns(session_id, turn_number)"
            )
            connection.execute("PRAGMA optimize")

    @staticmethod
    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_session(self, session: dict, user_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interview_sessions
                    (id, user_id, role, level, interview_type, mode, focus_skill, difficulty, question_strategy,
                     resume, current_question, current_source, max_questions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["session_id"], user_id, session["role"], session["level"],
                    session["interview_type"], session.get("mode", "interview"),
                    session.get("focus_skill", ""), session.get("difficulty", "中等"),
                    session.get("question_strategy", "spark_first"), session["resume"], session["current_question"],
                    session["current_source"], session["max_questions"],
                ),
            )

    def add_turn(self, session_id: str, turn: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interview_turns
                    (session_id, turn_number, question, answer, source, evaluation_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, turn["turn_number"], turn["question"],
                    turn["answer"], turn.get("source", "fallback"),
                    json.dumps(turn.get("evaluation", {}), ensure_ascii=False),
                ),
            )

    def update_question(self, session_id: str, question: str, source: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE interview_sessions SET current_question = ?, current_source = ? WHERE id = ?",
                (question, source, session_id),
            )

    def complete(self, session_id: str, duration_seconds: int) -> None:
        completed_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE interview_sessions
                SET status = 'complete', duration_seconds = ?, completed_at = ?
                WHERE id = ?
                """,
                (max(0, duration_seconds), completed_at, session_id),
            )

    def get_session(self, session_id: str, user_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            if row is None:
                return None
            turns = connection.execute(
                """
                SELECT turn_number, question, answer, source, evaluation_json
                FROM interview_turns WHERE session_id = ? ORDER BY turn_number
                """,
                (session_id,),
            ).fetchall()
        session = dict(row)
        session["session_id"] = session.pop("id")
        session["turns"] = []
        for row in turns:
            turn = dict(row)
            raw_evaluation = turn.pop("evaluation_json", "{}")
            try:
                turn["evaluation"] = json.loads(raw_evaluation or "{}")
            except json.JSONDecodeError:
                turn["evaluation"] = {}
            session["turns"].append(turn)
        return session

    def save_report(self, session_id: str, report: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interview_reports (session_id, score, report_json)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    score = excluded.score,
                    report_json = excluded.report_json,
                    created_at = CURRENT_TIMESTAMP
                """,
                (session_id, int(report["score"]), json.dumps(report, ensure_ascii=False)),
            )

    def get_report(self, session_id: str, user_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT r.report_json
                FROM interview_reports r
                JOIN interview_sessions s ON s.id = r.session_id
                WHERE r.session_id = ? AND s.user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()
        return json.loads(row["report_json"]) if row else None

    def list_by_user(self, user_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT s.id, s.role, s.interview_type, s.duration_seconds,
                       s.completed_at, s.created_at, COALESCE(r.score, 0) AS score
                FROM interview_sessions s
                LEFT JOIN interview_reports r ON r.session_id = s.id
                WHERE s.user_id = ? AND s.status = 'complete' AND s.mode = 'interview'
                ORDER BY COALESCE(s.completed_at, s.created_at) DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            {
                "id": row["id"], "role": row["role"], "type": row["interview_type"],
                "score": row["score"], "duration_seconds": row["duration_seconds"],
                "date": (row["completed_at"] or row["created_at"])[:10],
            }
            for row in rows
        ]

    def practice_progress(self, user_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT s.id, s.focus_skill, s.completed_at, s.created_at,
                       COALESCE(r.score, 0) AS score
                FROM interview_sessions s
                LEFT JOIN interview_reports r ON r.session_id = s.id
                WHERE s.user_id = ? AND s.mode = 'practice' AND s.status = 'complete'
                ORDER BY COALESCE(s.completed_at, s.created_at)
                """,
                (user_id,),
            ).fetchall()
        return [
            {"id": row["id"], "skill": row["focus_skill"] or "专项能力",
             "score": row["score"], "date": (row["completed_at"] or row["created_at"])[:10]}
            for row in rows
        ]

    def delete(self, session_id: str, user_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM interview_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            )
        return cursor.rowcount > 0
