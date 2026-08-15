"""当前普通用户个人资料与账号安全接口。"""
from flask import Blueprint, jsonify, request, session

from ..db.user_repository import UserRepository

user_api = Blueprint("user_api", __name__)
repository = UserRepository()


def _user_id() -> int | None:
    value = session.get("user_id")
    return value if isinstance(value, int) else None


def _unauthorized():
    return jsonify({"error": "请先登录。"}), 401


@user_api.get("/me/profile")
def profile():
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    data = repository.profile(user_id)
    return jsonify(data) if data else (jsonify({"error": "账号不存在。"}), 404)


@user_api.patch("/me/profile")
def update_profile():
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()
    if len(name) < 2 or len(name) > 24:
        return jsonify({"error": "昵称长度应为 2—24 个字符。"}), 400
    return jsonify({"user": repository.update_name(user_id, name)})


@user_api.put("/me/password")
def change_password():
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    payload = request.get_json(silent=True) or {}
    current = str(payload.get("current_password", ""))
    new = str(payload.get("new_password", ""))
    if len(new) < 8 or new == current:
        return jsonify({"error": "新密码至少 8 位，且不能与当前密码相同。"}), 400
    if not repository.change_password(user_id, current, new):
        return jsonify({"error": "当前密码不正确。"}), 403
    return jsonify({"ok": True})

