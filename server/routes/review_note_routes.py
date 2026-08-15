"""当前用户面试复盘笔记接口。"""
from flask import Blueprint,jsonify,request,session
from ..db.review_note_repository import ReviewNoteRepository

review_note_api=Blueprint("review_note_api",__name__);repository=ReviewNoteRepository()


def _uid():
    value=session.get("user_id");return value if isinstance(value,int) else None


@review_note_api.get("")
def listing():
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify({"items":repository.list_notes(user_id,str(request.args.get("search","")).strip()[:50]),"interviews":repository.available(user_id)})


@review_note_api.put("/<session_id>")
def save(session_id:str):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    payload=request.get_json(silent=True) or {};note=str(payload.get("note","")).strip()[:5000]
    actions=[str(x).strip()[:200] for x in payload.get("actions",[]) if str(x).strip()][:15];tags=[str(x).strip()[:30] for x in payload.get("tags",[]) if str(x).strip()][:12]
    if len(note)<5:return jsonify({"error":"复盘笔记至少需要 5 个字符。"}),400
    item=repository.save(user_id,session_id,note,actions,tags,bool(payload.get("starred",False)))
    return jsonify({"note":item}) if item else (jsonify({"error":"面试记录不存在。"}),404)


@review_note_api.delete("/<int:note_id>")
def delete(note_id:int):
    user_id=_uid()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return (jsonify({"ok":True}),200) if repository.delete(user_id,note_id) else (jsonify({"error":"笔记不存在。"}),404)
