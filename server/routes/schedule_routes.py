"""当前用户面试日程和准备任务接口。"""
from flask import Blueprint,jsonify,request,session
from ..db.schedule_repository import ScheduleRepository

schedule_api=Blueprint("schedule_api",__name__);repository=ScheduleRepository()


def _uid():
    value=session.get("user_id");return value if isinstance(value,int) else None


@schedule_api.get("")
def listing():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify(repository.list(user_id))


@schedule_api.post("")
def create():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    payload=request.get_json(silent=True) or {};title=str(payload.get("title","")).strip()[:120];due_at=str(payload.get("due_at","")).strip()[:30];notes=str(payload.get("notes","")).strip()[:500]
    if len(title)<2 or not due_at:return jsonify({"error":"请填写任务名称和计划时间。"}),400
    return jsonify({"task":repository.create(user_id,title,due_at,notes)}),201


@schedule_api.patch("/<int:task_id>")
def complete(task_id:int):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    value=bool((request.get_json(silent=True) or {}).get("completed",True))
    return (jsonify({"ok":True}),200) if repository.complete(user_id,task_id,value) else (jsonify({"error":"日程不存在。"}),404)


@schedule_api.delete("/<int:task_id>")
def delete(task_id:int):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return (jsonify({"ok":True}),200) if repository.delete(user_id,task_id) else (jsonify({"error":"只能删除自己创建的准备事项。"}),404)

