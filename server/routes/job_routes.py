"""岗位浏览、收藏和简历匹配接口。"""
import re

from flask import Blueprint, jsonify, request, session

from ..db.job_repository import JobRepository
from ..db.resume_repository import ResumeRepository

job_api = Blueprint("job_api", __name__)
jobs = JobRepository()
resumes = ResumeRepository()


def _user_id() -> int | None:
    value = session.get("user_id")
    return value if isinstance(value, int) else None


def _unauthorized():
    return jsonify({"error": "请先登录后再使用岗位功能。"}), 401


def _match(job: dict, resume: dict | None) -> dict:
    if resume is None:
        return {"score": 0, "matched": [], "missing": job["skills"], "advice": "请先在面试设置中上传简历，再进行岗位匹配。"}
    analysis = resume.get("analysis") or {}
    haystack = " ".join([resume.get("content", ""), *analysis.get("skills", [])]).lower()
    matched = [skill for skill in job["skills"] if re.search(rf"(?<!\w){re.escape(skill.lower())}(?!\w)", haystack) or skill.lower() in haystack]
    missing = [skill for skill in job["skills"] if skill not in matched]
    score = round(len(matched) * 100 / max(1, len(job["skills"])))
    return {"score": score, "matched": matched, "missing": missing, "advice": "匹配度较高，可以重点准备项目深挖和技术取舍。" if score >= 60 else "建议补充缺失技能的项目证据，并先完成针对性练习。"}


@job_api.get("")
def list_jobs():
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    keyword = str(request.args.get("keyword", "")).strip()[:40]
    city = str(request.args.get("city", "")).strip()[:20]
    return jsonify({"items": jobs.list(user_id, keyword, city)})


@job_api.get("/<int:job_id>")
def job_detail(job_id: int):
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    job = jobs.get(user_id, job_id)
    if job is None: return jsonify({"error": "岗位不存在。"}), 404
    saved = resumes.list_by_user(user_id)
    resume = saved[0] if saved else None
    return jsonify({"job": job, "match": _match(job, resume), "resume": {"id": resume["id"], "filename": resume["filename"]} if resume else None})


@job_api.put("/<int:job_id>/saved")
def save_job(job_id: int):
    user_id = _user_id()
    if user_id is None: return _unauthorized()
    value = bool((request.get_json(silent=True) or {}).get("saved", True))
    if not jobs.save(user_id, job_id, value): return jsonify({"error": "岗位不存在。"}), 404
    return jsonify({"saved": value})

