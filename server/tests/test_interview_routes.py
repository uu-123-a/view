import unittest
from unittest.mock import patch

from server.app import create_app


class InterviewRouteTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def test_interview_endpoints_require_user_login(self):
        self.assertEqual(self.client.get("/api/interviews/history").status_code, 401)
        self.assertEqual(self.client.post("/api/interviews/sessions", json={}).status_code, 401)

    def test_authenticated_session_creation_contract(self):
        expected = {"session_id": "session-1", "question": "测试题", "question_number": 1, "max_questions": 5, "source": "fallback", "mode": "interview"}
        with self.client.session_transaction() as session:
            session["user_id"] = 42
        with patch("server.routes.interview_routes.service.create_session", return_value=expected) as create_session:
            response = self.client.post("/api/interviews/sessions", json={"role": "Python 工程师"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["session_id"], "session-1")
        create_session.assert_called_once_with({"role": "Python 工程师"}, 42)


if __name__ == "__main__":
    unittest.main()
