"""使用星火生成结构化面试报告。"""

from __future__ import annotations

import json
import re
from .emotion_service import EmotionService

from .spark_service import SparkService


class EvaluationService:
    def __init__(self) -> None:
        self.spark = SparkService()

    @staticmethod
    def fallback() -> dict:
        return {
            "score": 78,
            "verdict": "基础表现稳定",
            "summary": "回答覆盖了主要问题，但还可以通过结论前置和量化结果提高说服力。",
            "strength": {"title": "思路较完整", "detail": "能够围绕问题给出具体行动。"},
            "improvement": {"title": "加强结构表达", "detail": "建议使用结论—依据—行动—结果的顺序。"},
            "practice": {"title": "STAR 项目表达", "detail": "继续训练个人贡献和量化结果。"},
            "practice_questions": [
                "请用 STAR 结构重新介绍一个最有代表性的项目。",
                "请说明一次技术决策的备选方案、取舍依据和最终结果。",
                "请选择一项项目成果，并用可验证的数据说明你的贡献。",
            ],
            "radar": [
                {"name": "专业能力", "score": 80}, {"name": "逻辑表达", "score": 74},
                {"name": "岗位匹配", "score": 79}, {"name": "沟通协作", "score": 72},
                {"name": "问题解决", "score": 82}, {"name": "稳定自信", "score": 76},
            ],
            "source": "fallback",
        }

    @classmethod
    def _normalize_report(cls, report: dict) -> dict:
        """将模型的不稳定 JSON 转换为前端始终可用的固定结构。"""
        fallback = cls.fallback()

        def text(value: object, default: str, limit: int = 180) -> str:
            cleaned = str(value or "").strip()
            return cleaned[:limit] if cleaned else default

        def card(value: object, default: dict) -> dict[str, str]:
            if isinstance(value, dict):
                return {
                    "title": text(value.get("title"), default["title"], 30),
                    "detail": text(value.get("detail"), default["detail"]),
                }
            if isinstance(value, str) and value.strip():
                return {"title": default["title"], "detail": value.strip()[:180]}
            return default.copy()

        try:
            score = max(0, min(100, int(float(report.get("score", fallback["score"])))))
        except (TypeError, ValueError):
            score = fallback["score"]

        radar_by_name: dict[str, int] = {}
        raw_radar = report.get("radar")
        if isinstance(raw_radar, list):
            for item in raw_radar:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                try:
                    radar_by_name[name] = max(0, min(100, int(float(item.get("score", 0)))))
                except (TypeError, ValueError):
                    continue

        normalized_radar = [
            {"name": item["name"], "score": radar_by_name.get(item["name"], item["score"])}
            for item in fallback["radar"]
        ]
        return {
            "score": score,
            "verdict": text(report.get("verdict"), fallback["verdict"], 24),
            "summary": text(report.get("summary"), fallback["summary"]),
            "strength": card(report.get("strength"), fallback["strength"]),
            "improvement": card(report.get("improvement"), fallback["improvement"]),
            "practice": card(report.get("practice"), fallback["practice"]),
            "practice_questions": report.get("practice_questions", fallback["practice_questions"]),
            "radar": normalized_radar,
            "source": "spark",
        }

    @classmethod
    def enrich(cls, report: dict, session: dict) -> dict:
        """Attach deterministic review details so saved and fallback reports stay useful."""
        enriched = dict(report)
        turn_reviews: list[dict] = []
        for index, turn in enumerate(session.get("turns", []), start=1):
            evaluation = turn.get("evaluation") if isinstance(turn.get("evaluation"), dict) else {}
            try:
                score = max(0, min(100, int(float(evaluation.get("score", 70)))))
            except (TypeError, ValueError):
                score = 70
            turn_reviews.append({
                "number": index,
                "question": str(turn.get("question") or "")[:500],
                "answer": str(turn.get("answer") or "")[:4000],
                "score": score,
                "feedback": str(evaluation.get("feedback") or "已完成本题作答。")[:180],
                "strength": str(evaluation.get("strength") or "能够围绕问题给出回答。")[:180],
                "improvement": str(evaluation.get("improvement") or "建议补充具体行动与量化结果。")[:180],
                "source": str(evaluation.get("source") or "fallback"),
            })
        enriched["turn_reviews"] = turn_reviews
        enriched["score_trend"] = [
            {"turn": f"Q{item['number']}", "score": item["score"]}
            for item in turn_reviews
        ]
        observations = []
        for turn in session.get("turns", []):
            evaluation = turn.get("evaluation") if isinstance(turn.get("evaluation"), dict) else {}
            emotion = turn.get("emotion") or evaluation.get("emotion")
            if isinstance(emotion, dict):
                observations.append(emotion)
        enriched["emotion_summary"] = EmotionService.summarize(observations)

        radar = enriched.get("radar") if isinstance(enriched.get("radar"), list) else []
        valid_radar = [item for item in radar if isinstance(item, dict) and "name" in item]
        enriched["weak_skills"] = sorted(
            ({"name": str(item["name"]), "score": int(item.get("score", 0))} for item in valid_radar),
            key=lambda item: item["score"],
        )[:3]

        raw_questions = enriched.get("practice_questions")
        questions = (
            [str(item).strip()[:240] for item in raw_questions if str(item).strip()]
            if isinstance(raw_questions, list) else []
        )
        if not questions:
            weakness = "、".join(item["name"] for item in enriched["weak_skills"]) or "结构化表达"
            questions = [
                f"针对{weakness}，请用 STAR 结构重新回答本次最薄弱的一题。",
                "请说明一个项目中的关键技术取舍，并比较至少两个备选方案。",
                "请选择一项成果，用数据说明你的个人贡献和业务价值。",
            ]
        enriched["practice_questions"] = questions[:5]
        return enriched

    def evaluate(self, session: dict) -> dict:
        transcript = "\n\n".join(
            f"问题：{turn['question']}\n回答：{turn['answer']}" for turn in session["turns"]
        )
        prompt = f"""你是严格且建设性的中文面试评估专家。请根据完整面试记录生成报告。
岗位：{session['role']}；级别：{session['level']}；类型：{session['interview_type']}
记录：
{transcript[:9000]}

只输出合法 JSON，不要 Markdown。格式必须为：
{{"score":0到100整数,"verdict":"12字内结论","summary":"80字内总结","strength":{{"title":"标题","detail":"说明"}},"improvement":{{"title":"标题","detail":"说明"}},"practice":{{"title":"标题","detail":"说明"}},"radar":[{{"name":"专业能力","score":整数}},{{"name":"逻辑表达","score":整数}},{{"name":"岗位匹配","score":整数}},{{"name":"沟通协作","score":整数}},{{"name":"问题解决","score":整数}},{{"name":"稳定自信","score":整数}}]}}"""
        try:
            raw = self.spark.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=1500,
                uid=session["session_id"],
            )
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match is None:
                raise ValueError("报告不是 JSON")
            report = json.loads(match.group(0))
            if not isinstance(report, dict):
                raise ValueError("报告不是对象")
            normalized = self._normalize_report(report)
        except (RuntimeError, ValueError, KeyError, json.JSONDecodeError, TypeError):
            normalized = self.fallback()
        return self.enrich(normalized, session)
