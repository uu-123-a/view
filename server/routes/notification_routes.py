"""当前用户通知列表与已读状态接口。"""
from flask import Blueprint,jsonify,session

from ..db.notification_repository import NotificationRepository

notification_api=Blueprint("notification_api",__name__);repository=NotificationRepository()


def _user_id():
    value=session.get("user_id");return value if isinstance(value,int) else None


@notification_api.get("")
def listing():
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify(repository.list(user_id))


@notification_api.patch("/<int:notification_id>/read")
def mark(notification_id:int):
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    if not repository.mark(user_id,notification_id):return jsonify({"error":"通知不存在。"}),404
    return jsonify({"ok":True})


@notification_api.post("/read-all")
def mark_all():
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify({"updated":repository.mark_all(user_id)})

