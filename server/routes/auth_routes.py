"""注册、登录、退出与当前用户接口。"""

import re

from flask import Blueprint, jsonify, request, session

from ..db.user_repository import UserRepository

auth_api = Blueprint("auth_api", __name__)
repository = UserRepository()
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _credentials() -> tuple[str, str, str]:
    payload = request.get_json(silent=True) or {}
    return (
        str(payload.get("name", "")).strip(),
        str(payload.get("email", "")).strip().lower(),
        str(payload.get("password", "")),
    )


@auth_api.post("/register")
def register():
    name, email, password = _credentials()
    if len(name) < 2 or len(name) > 24:
        return jsonify({"error": "昵称长度应为 2–24 个字符。"}), 400
    if not EMAIL_PATTERN.match(email):
        return jsonify({"error": "请输入有效的邮箱地址。"}), 400
    if len(password) < 8:
        return jsonify({"error": "密码至少需要 8 个字符。"}), 400
    try:
        user = repository.create(name, email, password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409
    session.clear()
    session["user_id"] = user["id"]
    return jsonify({"user": user}), 201


@auth_api.post("/login")
def login():
    _, email, password = _credentials()
    user = repository.authenticate(email, password)
    if user is None:
        return jsonify({"error": "邮箱或密码不正确。"}), 401
    session.clear()
    session["user_id"] = user["id"]
    return jsonify({"user": user})


@auth_api.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_api.get("/me")
def current_user():
    user_id = session.get("user_id")
    user = repository.get(user_id) if isinstance(user_id, int) else None
    if user is None:
        return jsonify({"user": None}), 401
    return jsonify({"user": user})
