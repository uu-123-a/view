"""当前登录用户的简历上传、分析与管理接口。"""

from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename

from ..db.resume_repository import ResumeRepository
from ..modules.resume_service import ResumeService
from ..modules.resume_optimizer import ResumeOptimizer
from ..db.job_repository import JobRepository

resume_api = Blueprint("resume_api", __name__)
repository = ResumeRepository()
service = ResumeService()
optimizer = ResumeOptimizer()
jobs = JobRepository()


def _user_id() -> int | None:
    value = session.get("user_id")
    return value if isinstance(value, int) else None


@resume_api.get("")
def list_resumes():
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "请先登录。"}), 401
    return jsonify({"items": repository.list_by_user(user_id)})


@resume_api.post("")
def upload_resume():
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "请先登录。"}), 401
    upload = request.files.get("resume")
    if upload is None or not upload.filename:
        return jsonify({"error": "请选择简历文件。"}), 400
    try:
        content, file_type = service.extract(upload)
        analysis = service.analyze(content)
        filename = secure_filename(upload.filename) or f"resume.{file_type}"
        item = repository.save(user_id, filename, file_type, content, analysis)
        return jsonify({"resume": item}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@resume_api.delete("/<resume_id>")
def delete_resume(resume_id: str):
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "请先登录。"}), 401
    if not repository.delete(resume_id, user_id):
        return jsonify({"error": "简历不存在。"}), 404
    return jsonify({"ok": True})


@resume_api.patch("/<resume_id>")
def rename_resume(resume_id:str):
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    filename=str((request.get_json(silent=True) or {}).get("filename","")).strip()[:120]
    if len(filename)<3:return jsonify({"error":"简历名称至少需要 3 个字符。"}),400
    if not repository.rename(resume_id,user_id,filename):return jsonify({"error":"简历不存在。"}),404
    return jsonify({"ok":True})


@resume_api.get("/optimizations")
def optimization_history():
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    return jsonify({"items":repository.optimizations(user_id)})


@resume_api.post("/<resume_id>/optimize")
def optimize_resume(resume_id:str):
    user_id=_user_id()
    if user_id is None:return jsonify({"error":"请先登录。"}),401
    resume=repository.get(resume_id,user_id)
    if resume is None:return jsonify({"error":"简历不存在。"}),404
    try:job_id=int((request.get_json(silent=True) or {}).get("job_id",0))
    except (TypeError,ValueError):return jsonify({"error":"请选择目标岗位。"}),400
    job=jobs.get(user_id,job_id)
    if job is None:return jsonify({"error":"岗位不存在或已停用。"}),404
    result=optimizer.optimize(resume,job)
    return jsonify({"optimization":repository.save_optimization(user_id,resume_id,job_id,job["title"],result)})
