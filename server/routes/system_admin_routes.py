import os
from flask import Blueprint,jsonify,request,session
from ..db.system_repository import SystemRepository
from ..db.user_repository import UserRepository
from ..db.admin_repository import current_admin,repository as admins

system_admin_api=Blueprint("system_admin_api",__name__);systems=SystemRepository();users=UserRepository()
def denied():
    return None if current_admin(session) else (jsonify({"error":"仅管理员可以访问系统设置。"}),403)
@system_admin_api.get("")
def status():
    d=denied()
    if d:return d
    return jsonify({"settings":systems.settings(),"status":{"spark_configured":all(os.getenv(k) for k in ("SPARKAI_APP_ID","SPARKAI_API_SECRET","SPARKAI_API_KEY")),"whisper_model":os.getenv("WHISPER_MODEL","small")},"users":users.list_all(),"administrators":admins.list_all(),"events":systems.events()})
@system_admin_api.put("/settings")
def settings():
    d=denied()
    if d:return d
    p=request.get_json(silent=True) or {}
    for key in ("spark_enabled","whisper_enabled"):
        if key in p:systems.set(key,bool(p[key]))
    return jsonify({"settings":systems.settings()})
