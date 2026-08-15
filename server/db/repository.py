"""面试记录仓储接口。"""


class InterviewRepository:
    def save(self, record: dict) -> dict:
        raise NotImplementedError("请在此接入 MySQL、SQLite 或其他持久化服务")

    def list_by_user(self, user_id: str) -> list[dict]:
        raise NotImplementedError("请在此实现用户历史查询")
