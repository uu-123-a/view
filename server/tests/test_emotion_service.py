import unittest

from server.modules.emotion_service import EmotionService


class EmotionServiceTests(unittest.TestCase):
    def test_confident_structured_answer(self):
        result = EmotionService.analyze("首先我负责核心模块，最后将响应时间降低了 35%，并完成上线。")
        self.assertGreaterEqual(result["confidence"], 60)
        self.assertEqual(result["basis"], "answer_text")

    def test_nervous_language_produces_training_tip(self):
        result = EmotionService.analyze("我不太清楚，可能大概是这样，也许需要再确认。")
        self.assertEqual(result["label"], "nervous")
        self.assertGreaterEqual(result["tension"], 55)

    def test_summary_contains_timeline(self):
        observations = [EmotionService.analyze("首先我主导开发并提升性能。"), EmotionService.analyze("我可能不太确定。")]
        summary = EmotionService.summarize(observations)
        self.assertEqual(len(summary["timeline"]), 2)
        self.assertIn("average_confidence", summary)


if __name__ == "__main__":
    unittest.main()
