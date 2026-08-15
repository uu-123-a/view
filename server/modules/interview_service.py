"""由讯飞星火驱动、SQLite 持久化的模拟面试会话。"""

from __future__ import annotations

import json
import re
from threading import Lock
from uuid import uuid4

from ..db.interview_repository import InterviewRepository
from ..db.question_repository import QuestionRepository
from ..db.mistake_repository import MistakeRepository
from .spark_service import SparkService
from .emotion_service import EmotionService

FALLBACK_QUESTIONS = [
    "请用两分钟介绍一下你自己，并重点说明与目标岗位最相关的经历。",
    "你在项目中遇到过最棘手的技术问题是什么？你是如何定位并解决的？",
    "如果线上模型的准确率突然下降，你会按照什么顺序排查？",
    "请讲一个你与团队成员意见不一致的例子，你最终是如何推进事情的？",
    "为什么选择这个岗位？你希望未来三年在哪些方面获得成长？",
]


class InterviewService:
    def __init__(self) -> None:
        self.spark = SparkService()
        self.repository = InterviewRepository()
        self.questions = QuestionRepository()
        self.mistakes = MistakeRepository()
        self.sessions: dict[str, dict] = {}
        self.lock = Lock()

    @staticmethod
    def _question_prompt(session: dict, first: bool = False) -> str:
        transcript = "\n".join(
            f"面试官：{item['question']}\n候选人：{item['answer']}"
            for item in session["turns"][-4:]
        )
        stage = "第一题" if first else "下一道追问"
        focus = f"专项训练能力：{session.get('focus_skill')}" if session.get("mode") == "practice" else ""
        return f"""你是专业、克制的中文技术面试官 MOSS。请为候选人生成{stage}。
目标岗位：{session['role']}
候选级别：{session['level']}
面试类型：{session['interview_type']}
题目难度：{session.get('difficulty', '中等')}
{focus}
简历重点：{session['resume'][:2500]}
已完成对话：
{transcript or '暂无'}

要求：结合简历与上一轮回答，只输出一个清晰具体的问题；不要评价，不要给答案，不要编号；避免重复，长度不超过100字。"""

    def _generate_question(self, session: dict, index: int) -> tuple[str, str]:
        strategy = session.get("question_strategy", "spark_first")
        used = [turn["question"] for turn in session.get("turns", [])]
        if session.get("current_question"):
            used.append(session["current_question"])
        if strategy in {"local_first", "local_only"}:
            local = self.questions.select(
                session["role"], session["interview_type"], session.get("difficulty", "中等"), used
            )
            if local:
                return local, "question_bank"
            if strategy == "local_only":
                return FALLBACK_QUESTIONS[min(index, len(FALLBACK_QUESTIONS) - 1)], "fallback"
        try:
            question = self.spark.chat(
                [{"role": "user", "content": self._question_prompt(session, index == 0)}],
                temperature=0.55, max_tokens=256, uid=session["session_id"],
            )
            return question.strip().strip('"“”'), "spark"
        except RuntimeError:
            local = self.questions.select(
                session["role"], session["interview_type"], session.get("difficulty", "中等"), used
            )
            return (local, "question_bank") if local else (FALLBACK_QUESTIONS[min(index, len(FALLBACK_QUESTIONS) - 1)], "fallback")

    @staticmethod
    def _fallback_evaluation(answer: str) -> dict:
        length_score = min(24, len(answer) // 12)
        structure_terms = ("首先", "其次", "最后", "第一", "第二", "因此", "总结")
        evidence_terms = ("例如", "比如", "%", "提升", "降低", "耗时", "用户", "数据")
        structure_score = min(10, sum(term in answer for term in structure_terms) * 3)
        evidence_score = min(12, sum(term in answer for term in evidence_terms) * 3)
        score = max(45, min(88, 48 + length_score + structure_score + evidence_score))
        if len(answer) < 60:
            improvement = "回答偏短，建议补充具体场景、你的行动和量化结果。"
        elif not any(term in answer for term in evidence_terms):
            improvement = "思路已经较完整，建议加入数据或项目结果增强说服力。"
        else:
            improvement = "可以进一步说明关键取舍，以及为什么选择这一方案。"
        return {
            "score": score,
            "level": "优秀" if score >= 85 else "良好" if score >= 70 else "待提升",
            "feedback": "回答与问题相关，能够表达主要思路。",
            "strength": "内容聚焦，没有明显偏离问题。",
            "improvement": improvement,
            "source": "fallback",
        }

    @classmethod
    def _normalize_evaluation(cls, raw: dict, answer: str) -> dict:
        fallback = cls._fallback_evaluation(answer)
        try:
            score = max(0, min(100, int(float(raw.get("score", fallback["score"])))))
        except (TypeError, ValueError):
            score = fallback["score"]

        def text(key: str, default: str, limit: int = 180) -> str:
            value = str(raw.get(key) or default).strip()
            return value[:limit]

        return {
            "score": score,
            "level": "优秀" if score >= 85 else "良好" if score >= 70 else "待提升",
            "feedback": text("feedback", fallback["feedback"]),
            "strength": text("strength", fallback["strength"]),
            "improvement": text("improvement", fallback["improvement"]),
            "source": "spark",
        }

    def _evaluate_answer(self, session: dict, question: str, answer: str) -> dict:
        prompt = f"""你是严格但友好的中文面试官。请评价候选人的单题回答，只输出合法 JSON，不要 Markdown。
岗位：{session['role']}
级别：{session['level']}
面试类型：{session['interview_type']}
问题：{question}
回答：{answer[:4000]}

评分维度：问题相关性、技术准确性、结构表达、事实与量化依据。
JSON 格式：{{"score":0到100整数,"feedback":"一句总体评价","strength":"最明显的优点","improvement":"最重要且可执行的改进建议"}}"""
        try:
            response = self.spark.chat(
                [{"role": "user", "content": prompt}], temperature=0.2,
                max_tokens=420, uid=f"{session['session_id']}-evaluation",
            )
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match is None:
                raise ValueError("missing JSON")
            raw = json.loads(match.group(0))
            if not isinstance(raw, dict):
                raise ValueError("invalid JSON object")
            return self._normalize_evaluation(raw, answer)
        except (RuntimeError, ValueError, TypeError, json.JSONDecodeError):
            return self._fallback_evaluation(answer)

    def create_session(self, payload: dict, user_id: int) -> dict:
        session_id = uuid4().hex
        mode = "practice" if payload.get("mode") == "practice" else "interview"
        difficulty = str(payload.get("difficulty") or "中等")
        if difficulty not in {"基础", "中等", "困难"}:
            difficulty = "中等"
        strategy = str(payload.get("question_strategy") or "spark_first")
        if strategy not in {"spark_first", "local_first", "local_only"}:
            strategy = "spark_first"
        session = {
            "session_id": session_id, "user_id": user_id,
            "role": str(payload.get("role") or "多模态算法工程师"),
            "level": str(payload.get("level") or "校招 / 初级"),
            "interview_type": str(payload.get("interview_type") or "技术面"),
            "resume": str(payload.get("resume") or "未提供"),
            "mode": mode, "focus_skill": str(payload.get("focus_skill") or ""),
            "difficulty": difficulty, "question_strategy": strategy,
            "turns": [], "current_question": "", "current_source": "fallback",
            "max_questions": 3 if mode == "practice" else 5, "status": "active",
        }
        initial_question = str(payload.get("initial_question") or "").strip()
        if mode == "practice" and initial_question:
            question, source = initial_question[:500], "practice"
        else:
            question, source = self._generate_question(session, 0)
        session["current_question"] = question
        session["current_source"] = source
        self.repository.create_session(session, user_id)
        with self.lock:
            self.sessions[session_id] = session
        return {
            "session_id": session_id, "role": session["role"], "question": question,
            "question_number": 1, "max_questions": session["max_questions"], "source": source,
            "mode": mode, "focus_skill": session["focus_skill"],
            "difficulty": difficulty, "question_strategy": strategy,
        }

    def get_session(self, session_id: str, user_id: int) -> dict:
        session = self.sessions.get(session_id)
        if session is not None and session.get("user_id") == user_id:
            return session
        session = self.repository.get_session(session_id, user_id)
        if session is None:
            raise KeyError("面试会话不存在或不属于当前用户。")
        with self.lock:
            self.sessions[session_id] = session
        return session

    def submit_answer(
        self, session_id: str, answer: str, user_id: int, duration_seconds: int = 0
    ) -> dict:
        session = self.get_session(session_id, user_id)
        if session.get("status") == "complete":
            raise ValueError("本次面试已经结束。")
        cleaned_answer = answer.strip()
        if not cleaned_answer:
            raise ValueError("回答不能为空。")

        turn = {
            "turn_number": len(session["turns"]) + 1,
            "question": session["current_question"], "answer": cleaned_answer,
            "source": session.get("current_source", "fallback"),
        }
        turn["evaluation"] = self._evaluate_answer(
            session, turn["question"], cleaned_answer
        )
        turn["emotion"] = EmotionService.analyze(cleaned_answer)
        turn["evaluation"]["emotion"] = turn["emotion"]
        self.repository.add_turn(session_id, turn)
        self.mistakes.add(user_id, session_id, turn, session.get("focus_skill") or "综合能力")
        session["turns"].append(turn)
        complete = len(session["turns"]) >= session["max_questions"]
        if complete:
            session["status"] = "complete"
            self.repository.complete(session_id, duration_seconds)
            return {
                "session_id": session_id, "accepted": True, "complete": True,
                "question_number": len(session["turns"]),
                "evaluation": turn["evaluation"],
                "emotion": turn["emotion"],
            }

        question, source = self._generate_question(session, len(session["turns"]))
        session["current_question"] = question
        session["current_source"] = source
        self.repository.update_question(session_id, question, source)
        return {
            "session_id": session_id, "accepted": True, "complete": False,
            "next_question": question, "question_number": len(session["turns"]) + 1,
            "max_questions": session["max_questions"], "source": source,
            "evaluation": turn["evaluation"],
            "emotion": turn["emotion"],
        }
