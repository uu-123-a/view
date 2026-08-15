import unittest
from unittest.mock import patch

from server.app import create_app


class FakeUserRepository:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def create(self, name, email, password):
        if email in self.users:
            raise ValueError("邮箱已注册")
        user = {"id": self.next_id, "name": name, "email": email, "role": "user"}
        self.next_id += 1
        self.users[email] = {**user, "password": password}
        return user

    def authenticate(self, email, password):
        user = self.users.get(email)
        if not user or user["password"] != password:
            return None
        return {key: user[key] for key in ("id", "name", "email", "role")}

    def get(self, user_id):
        for user in self.users.values():
            if user["id"] == user_id:
                return {key: user[key] for key in ("id", "name", "email", "role")}
        return None


class FakeAdminRepository:
    admin = {"id": 7, "name": "管理员", "email": "admin@example.com", "role": "administrator"}

    def authenticate(self, email, password):
        return dict(self.admin) if email == self.admin["email"] and password == "admin-pass" else None

    def get(self, admin_id):
        return dict(self.admin) if admin_id == self.admin["id"] else None


class HealthAndAuthTests(unittest.TestCase):
    def setUp(self):
        self.user_repository = FakeUserRepository()
        self.admin_repository = FakeAdminRepository()
        self.patches = [
            patch("server.routes.auth_routes.repository", self.user_repository),
            patch("server.routes.admin_auth_routes.repository", self.admin_repository),
            patch("server.routes.admin_auth_routes.current_admin", lambda session: self.admin_repository.get(session.get("admin_id"))),
        ]
        for item in self.patches:
            item.start()
        app = create_app()
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "service": "moss-view"})

    def test_register_login_and_logout(self):
        response = self.client.post("/api/auth/register", json={"name": "测试用户", "email": "user@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["email"], "user@example.com")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrong-pass"}).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"}).status_code, 200)

    def test_user_and_admin_sessions_are_isolated(self):
        self.client.post("/api/auth/register", json={"name": "测试用户", "email": "user@example.com", "password": "password123"})
        self.assertEqual(self.client.get("/api/admin/auth/me").status_code, 401)
        response = self.client.post("/api/admin/auth/login", json={"email": "admin@example.com", "password": "admin-pass"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["admin"]["role"], "administrator")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/api/admin/auth/me").status_code, 200)


if __name__ == "__main__":
    unittest.main()
