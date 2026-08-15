"""当前用户知识图谱接口。"""
from flask import Blueprint,jsonify,session
from ..modules.knowledge_service import KnowledgeService

knowledge_api=Blueprint("knowledge_api",__name__);service=KnowledgeService()


@knowledge_api.get("")
def graph():
    user_id=session.get("user_id")
    if not isinstance(user_id,int):return jsonify({"error":"请先登录。"}),401
    return jsonify(service.build(user_id))

