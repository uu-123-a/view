"""Privacy-preserving expression-state analysis for interview answers.

The service analyses answer text only. It does not receive video frames, perform
face recognition, or make medical/psychological diagnoses.
"""

from __future__ import annotations

from collections import Counter


class EmotionService:
    LABELS = {
        "confident": "自信",
        "calm": "平稳",
        "nervous": "紧张",
        "positive": "积极",
    }
    CONFIDENT_TERMS = ("我负责", "我主导", "结果", "提升", "降低", "完成", "落地", "数据")
    NERVOUS_TERMS = ("可能", "大概", "不确定", "不太清楚", "应该是", "也许", "抱歉", "不知道")
    POSITIVE_TERMS = ("学习", "改进", "合作", "解决", "成长", "主动", "感谢", "机会")
    STRUCTURE_TERMS = ("首先", "其次", "然后", "最后", "第一", "第二", "因此", "总结")

    @classmethod
    def analyze(cls, answer: str) -> dict:
        text = str(answer or "").strip()[:4000]
        confident_hits = sum(text.count(term) for term in cls.CONFIDENT_TERMS)
        nervous_hits = sum(text.count(term) for term in cls.NERVOUS_TERMS)
        positive_hits = sum(text.count(term) for term in cls.POSITIVE_TERMS)
        structure_hits = sum(text.count(term) for term in cls.STRUCTURE_TERMS)

        confidence = min(100, 48 + min(len(text), 600) // 15 + confident_hits * 6 + structure_hits * 4 - nervous_hits * 8)
        confidence = max(0, confidence)
        tension = min(100, max(0, 24 + nervous_hits * 16 + text.count("……") * 8 - structure_hits * 4))
        positivity = min(100, max(0, 45 + positive_hits * 8 + confident_hits * 3))
        stability = min(100, max(0, 82 - tension // 2 + structure_hits * 4))

        scores = {
            "confident": confidence,
            "calm": stability,
            "nervous": tension,
            "positive": positivity,
        }
        dominant = max(("confident", "calm", "positive", "nervous"), key=scores.get)
        if nervous_hits and tension >= 55:
            dominant = "nervous"

        tips = []
        if tension >= 55:
            tips.append("先停顿一秒，再用“结论—依据—结果”的顺序回答。")
        if confidence < 60:
            tips.append("减少“可能、应该”等模糊词，补充你亲自完成的行动和数据。")
        if structure_hits == 0:
            tips.append("使用“首先、其次、最后”帮助面试官快速抓住重点。")
        if not tips:
            tips.append("表达状态稳定，继续保持当前语速并补充量化结果。")

        return {
            "label": dominant,
            "label_text": cls.LABELS[dominant],
            "confidence": confidence,
            "tension": tension,
            "positivity": positivity,
            "stability": stability,
            "tip": tips[0],
            "basis": "answer_text",
            "disclaimer": "仅用于表达训练，不代表心理或医学结论。",
        }

    @classmethod
    def summarize(cls, observations: list[dict]) -> dict:
        valid = [item for item in observations if isinstance(item, dict) and item.get("label") in cls.LABELS]
        if not valid:
            return {
                "timeline": [],
                "dominant_emotion": "unknown",
                "dominant_text": "暂无数据",
                "average_confidence": 0,
                "average_tension": 0,
                "average_stability": 0,
                "suggestion": "完成一次文本作答后即可生成表达情绪趋势。",
            }
        dominant = Counter(item["label"] for item in valid).most_common(1)[0][0]
        average = lambda key: round(sum(int(item.get(key, 0)) for item in valid) / len(valid))
        tension = average("tension")
        return {
            "timeline": [
                {"turn": f"Q{index}", "label": item["label_text"], "confidence": item["confidence"], "tension": item["tension"], "stability": item["stability"]}
                for index, item in enumerate(valid, start=1)
            ],
            "dominant_emotion": dominant,
            "dominant_text": cls.LABELS[dominant],
            "average_confidence": average("confidence"),
            "average_tension": tension,
            "average_stability": average("stability"),
            "suggestion": "紧张信号偏高，建议刻意放慢语速并先说结论。" if tension >= 55 else "整体表达较稳定，继续用具体行动与数据增强自信感。",
            "disclaimer": "结果来自回答文本特征，仅用于表达训练，不代表心理或医学结论。",
        }
