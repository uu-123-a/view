"""当前用户求职投递管理接口。"""
from flask import Blueprint,jsonify,request,session
from ..db.application_repository import ApplicationRepository,STATUSES

application_api=Blueprint("application_api",__name__);repository=ApplicationRepository()


def _uid():
    value=session.get("user_id");return value if isinstance(value,int) else None


@application_api.get("")
def listing():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify(repository.list(user_id))


@application_api.post("")
def create():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    try:job_id=int((request.get_json(silent=True) or {}).get("job_id",0))
    except (TypeError,ValueError):return jsonify({"error":"请选择岗位。"}),400
    item=repository.create(user_id,job_id)
    return (jsonify({"application":item}),201) if item else (jsonify({"error":"岗位不存在或已停用。"}),404)


@application_api.put("/<int:application_id>")
def update(application_id:int):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    payload=request.get_json(silent=True) or {};status=str(payload.get("status","wishlist"))
    if status not in STATUSES:return jsonify({"error":"无效的投递状态。"}),400
    interview_at=str(payload.get("interview_at","")).strip()[:30] or None;notes=str(payload.get("notes","")).strip()[:1000]
    if not repository.update(user_id,application_id,status,interview_at,notes):return jsonify({"error":"投递记录不存在。"}),404
    return jsonify({"ok":True})


@application_api.delete("/<int:application_id>")
def delete(application_id:int):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return (jsonify({"ok":True}),200) if repository.delete(user_id,application_id) else (jsonify({"error":"投递记录不存在。"}),404)

