"""普通用户职业助手对话接口。"""
from flask import Blueprint,jsonify,request,session

from ..db.career_repository import CareerRepository
from ..modules.career_service import CareerService

career_api=Blueprint("career_api",__name__);repository=CareerRepository();service=CareerService()


def _uid():
    value=session.get("user_id");return value if isinstance(value,int) else None


@career_api.get("")
def listing():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify({"items":repository.list(user_id)})


@career_api.post("")
def create():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    title=str((request.get_json(silent=True) or {}).get("title") or "新的职业咨询").strip()
    return jsonify({"conversation":repository.create(user_id,title)}),201


@career_api.get("/<conversation_id>")
def detail(conversation_id:str):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    item=repository.get(user_id,conversation_id)
    return jsonify({"conversation":item}) if item else (jsonify({"error":"对话不存在。"}),404)


@career_api.post("/<conversation_id>/messages")
def send(conversation_id:str):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    item=repository.get(user_id,conversation_id)
    if item is None:return jsonify({"error":"对话不存在。"}),404
    question=str((request.get_json(silent=True) or {}).get("content","")).strip()[:2000]
    if len(question)<2:return jsonify({"error":"请输入完整问题。"}),400
    answer,source=service.answer(question,repository.context(user_id),item["messages"])
    repository.add(user_id,conversation_id,"user",question,"user");repository.add(user_id,conversation_id,"assistant",answer,source)
    return jsonify({"answer":answer,"source":source,"conversation":repository.get(user_id,conversation_id)})


@career_api.delete("/<conversation_id>")
def delete(conversation_id:str):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return (jsonify({"ok":True}),200) if repository.delete(user_id,conversation_id) else (jsonify({"error":"对话不存在。"}),404)

