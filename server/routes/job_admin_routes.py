"""独立管理员岗位 CRUD、启停与 CSV 导入。"""
import csv
import io

from flask import Blueprint, jsonify, request, session

from ..db.admin_repository import current_admin
from ..db.job_repository import JobRepository

job_admin_api = Blueprint("job_admin_api", __name__)
jobs = JobRepository()


def _denied():
    return None if current_admin(session) else (jsonify({"error": "仅管理员可以管理岗位。"}), 403)


def _clean(data: dict) -> dict:
    skills = data.get("skills", [])
    if isinstance(skills, str): skills = [item.strip() for item in skills.replace("，", ",").split(",") if item.strip()]
    result = {
        "title": str(data.get("title", "")).strip()[:60], "company": str(data.get("company", "")).strip()[:60],
        "city": str(data.get("city", "")).strip()[:20], "salary": str(data.get("salary", "")).strip()[:30],
        "experience": str(data.get("experience", "")).strip()[:30], "education": str(data.get("education", "")).strip()[:20],
        "skills": [str(item).strip()[:30] for item in skills if str(item).strip()][:15],
        "description": str(data.get("description", "")).strip()[:1200],
        "enabled": 0 if str(data.get("enabled", "1")).lower() in {"0", "false", "否", "停用"} else 1,
    }
    if any(not result[key] for key in ("title","company","city","salary","experience","education","description")): raise ValueError("请完整填写岗位信息。")
    if not result["skills"]: raise ValueError("请至少填写一个岗位技能。")
    return result


@job_admin_api.get("")
def listing():
    denied = _denied()
    if denied: return denied
    return jsonify({"items": jobs.admin_list(str(request.args.get("search", "")).strip()[:50])})


@job_admin_api.post("")
def create():
    denied = _denied()
    if denied: return denied
    try: return jsonify({"job": jobs.create(_clean(request.get_json(silent=True) or {}))}), 201
    except ValueError as exc: return jsonify({"error": str(exc)}), 400


@job_admin_api.put("/<int:job_id>")
def update(job_id: int):
    denied = _denied()
    if denied: return denied
    try:
        if not jobs.update(job_id, _clean(request.get_json(silent=True) or {})): return jsonify({"error": "岗位不存在。"}), 404
        return jsonify({"ok": True})
    except ValueError as exc: return jsonify({"error": str(exc)}), 400


@job_admin_api.delete("/<int:job_id>")
def delete(job_id: int):
    denied = _denied()
    if denied: return denied
    return (jsonify({"ok": True}), 200) if jobs.delete(job_id) else (jsonify({"error": "岗位不存在。"}), 404)


@job_admin_api.post("/import")
def import_csv():
    denied = _denied()
    if denied: return denied
    text = str((request.get_json(silent=True) or {}).get("csv_text", ""))
    imported, errors = 0, []
    for line, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        try: jobs.create(_clean(row)); imported += 1
        except ValueError as exc: errors.append(f"第{line}行：{exc}")
    return jsonify({"imported": imported, "errors": errors[:20]})

