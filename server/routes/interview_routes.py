"""模拟面试、持久化历史与报告接口。"""

from flask import Blueprint, jsonify, request, session

from ..modules.evaluation_service import EvaluationService
from ..modules.interview_service import InterviewService

interview_api = Blueprint("interview_api", __name__)
service = InterviewService()
evaluation = EvaluationService()


def _user_id() -> int | None:
    value = session.get("user_id")
    return value if isinstance(value, int) else None


def _unauthorized():
    return jsonify({"error": "请先登录后再使用面试功能。"}), 401


@interview_api.post("/sessions")
def create_session():
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    return jsonify(
        service.create_session(request.get_json(silent=True) or {}, user_id)
    ), 201


@interview_api.post("/sessions/<session_id>/answers")
def submit_answer(session_id: str):
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(
            service.submit_answer(
                session_id,
                str(payload.get("answer", "")),
                user_id,
                int(payload.get("duration_seconds", 0) or 0),
            )
        )
    except KeyError as exc:
        return jsonify({"error": str(exc.args[0])}), 404
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@interview_api.get("/sessions/<session_id>/report")
def interview_report(session_id: str):
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    saved = service.repository.get_report(session_id, user_id)
    if saved is not None:
        if "turn_reviews" not in saved:
            try:
                interview = service.get_session(session_id, user_id)
                saved = evaluation.enrich(saved, interview)
                service.repository.save_report(session_id, saved)
            except KeyError:
                pass
        return jsonify(saved)
    try:
        interview = service.get_session(session_id, user_id)
        if interview.get("status") != "complete":
            return jsonify({"error": "面试尚未完成，暂时不能生成报告。"}), 409
        report = evaluation.evaluate(interview)
        service.repository.save_report(session_id, report)
        return jsonify(report)
    except KeyError as exc:
        return jsonify({"error": str(exc.args[0])}), 404


@interview_api.get("/history")
def interview_history():
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    return jsonify({"items": service.repository.list_by_user(user_id)})


@interview_api.get("/practice-progress")
def practice_progress():
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    return jsonify({"items": service.repository.practice_progress(user_id)})


@interview_api.delete("/history/<session_id>")
def delete_interview(session_id: str):
    user_id = _user_id()
    if user_id is None:
        return _unauthorized()
    deleted = service.repository.delete(session_id, user_id)
    service.sessions.pop(session_id, None)
    if not deleted:
        return jsonify({"error": "面试记录不存在。"}), 404
    return jsonify({"ok": True})
