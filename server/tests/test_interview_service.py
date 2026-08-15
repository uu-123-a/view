import unittest

from server.modules.interview_service import FALLBACK_QUESTIONS, InterviewService


class FailingSpark:
    def chat(self, *_args, **_kwargs):
        raise RuntimeError("spark unavailable")


class EmptyQuestionBank:
    def select(self, *_args, **_kwargs):
        return None


class MemoryInterviewRepository:
    def __init__(self):
        self.sessions = {}
        self.turns = {}

    def create_session(self, session, user_id):
        self.sessions[session["session_id"]] = {**session, "user_id": user_id}

    def add_turn(self, session_id, turn):
        self.turns.setdefault(session_id, []).append(turn)

    def update_question(self, session_id, question, source):
        self.sessions[session_id].update(current_question=question, current_source=source)

    def complete(self, session_id, duration_seconds):
        self.sessions[session_id].update(status="complete", duration_seconds=duration_seconds)

    def get_session(self, session_id, user_id):
        session = self.sessions.get(session_id)
        return session if session and session["user_id"] == user_id else None


class MemoryMistakes:
    def __init__(self):
        self.items = []

    def add(self, *args):
        self.items.append(args)


def make_service():
    service = InterviewService.__new__(InterviewService)
    service.spark = FailingSpark()
    service.repository = MemoryInterviewRepository()
    service.questions = EmptyQuestionBank()
    service.mistakes = MemoryMistakes()
    service.sessions = {}
    from threading import Lock
    service.lock = Lock()
    return service


class InterviewServiceTests(unittest.TestCase):
    def test_spark_failure_falls_back_without_crashing(self):
        service = make_service()
        result = service.create_session({"role": "Python 工程师", "question_strategy": "spark_first"}, user_id=11)
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["question"], FALLBACK_QUESTIONS[0])
        self.assertTrue(result["session_id"])

    def test_local_only_never_calls_spark(self):
        service = make_service()
        result = service.create_session({"question_strategy": "local_only"}, user_id=11)
        self.assertEqual(result["source"], "fallback")

    def test_practice_session_and_answer_validation(self):
        service = make_service()
        created = service.create_session({"mode": "practice", "initial_question": "请介绍你的项目", "focus_skill": "项目表达"}, user_id=11)
        self.assertEqual(created["source"], "practice")
        self.assertEqual(created["max_questions"], 3)
        with self.assertRaises(ValueError):
            service.submit_answer(created["session_id"], "   ", user_id=11)

    def test_session_is_not_visible_to_another_user(self):
        service = make_service()
        created = service.create_session({"question_strategy": "local_only"}, user_id=11)
        with self.assertRaises(KeyError):
            service.get_session(created["session_id"], user_id=22)


if __name__ == "__main__":
    unittest.main()
