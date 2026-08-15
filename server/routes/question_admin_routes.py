"""Administrator-only question bank CRUD and CSV import."""

import csv
import io
import sqlite3

from flask import Blueprint, jsonify, request, session

from ..db.question_repository import QuestionRepository
from ..db.admin_repository import current_admin

question_admin_api = Blueprint("question_admin_api", __name__)
questions = QuestionRepository()


def admin_error():
    return None if current_admin(session) else (jsonify({"error": "仅管理员可以管理题库。"}), 403)


def clean(data: dict) -> dict:
    result = {
        "category": str(data.get("category") or "通用").strip()[:30],
        "interview_type": str(data.get("interview_type") or "技术面").strip()[:20],
        "difficulty": str(data.get("difficulty") or "中等").strip()[:10],
        "question": str(data.get("question") or "").strip()[:1000],
        "enabled": 1 if str(data.get("enabled", "1")).lower() not in {"0", "false", "否"} else 0,
    }
    if len(result["question"]) < 5:
        raise ValueError("题目内容至少需要 5 个字符。")
    if result["difficulty"] not in {"基础", "中等", "困难"}:
        raise ValueError("难度必须为基础、中等或困难。")
    return result


@question_admin_api.get("")
def list_questions():
    denied = admin_error()
    if denied: return denied
    return jsonify({"items": questions.list(request.args.get("search", ""))})


@question_admin_api.post("")
def create_question():
    denied = admin_error()
    if denied: return denied
    try:
        return jsonify({"question": questions.create(clean(request.get_json(silent=True) or {}))}), 201
    except (ValueError, sqlite3.IntegrityError) as exc:
        return jsonify({"error": str(exc)}), 400


@question_admin_api.put("/<int:question_id>")
def update_question(question_id: int):
    denied = admin_error()
    if denied: return denied
    try:
        return jsonify({"ok": questions.update(question_id, clean(request.get_json(silent=True) or {}))})
    except (ValueError, sqlite3.IntegrityError) as exc:
        return jsonify({"error": str(exc)}), 400


@question_admin_api.delete("/<int:question_id>")
def delete_question(question_id: int):
    denied = admin_error()
    if denied: return denied
    return jsonify({"ok": questions.delete(question_id)})


@question_admin_api.post("/import")
def import_questions():
    denied = admin_error()
    if denied: return denied
    text = str((request.get_json(silent=True) or {}).get("csv_text") or "")
    reader = csv.DictReader(io.StringIO(text))
    imported, errors = 0, []
    for line, row in enumerate(reader, start=2):
        try:
            questions.create(clean(row)); imported += 1
        except (ValueError, sqlite3.IntegrityError) as exc:
            errors.append(f"第{line}行：{exc}")
    return jsonify({"imported": imported, "errors": errors[:20]})
