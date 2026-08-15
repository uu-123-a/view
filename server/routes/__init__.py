"""HTTP API 路由注册层。"""

from flask import Flask

from .auth_routes import auth_api
from .interview_routes import interview_api
from .job_routes import job_api
from .resume_routes import resume_api
from .speech_routes import speech_api
from .user_routes import user_api
from .question_admin_routes import question_admin_api
from .system_admin_routes import system_admin_api
from .analytics_routes import analytics_api
from .admin_auth_routes import admin_auth_api
from .training_plan_routes import training_plan_api
from .mistake_routes import mistake_api
from .job_admin_routes import job_admin_api
from .notification_routes import notification_api
from .career_routes import career_api
from .knowledge_routes import knowledge_api
from .application_routes import application_api
from .schedule_routes import schedule_api
from .review_note_routes import review_note_api


def register_routes(app: Flask) -> None:
    app.register_blueprint(auth_api, url_prefix="/api/auth")
    app.register_blueprint(interview_api, url_prefix="/api/interviews")
    app.register_blueprint(job_api, url_prefix="/api/jobs")
    app.register_blueprint(resume_api, url_prefix="/api/resumes")
    app.register_blueprint(speech_api, url_prefix="/api/speech")
    app.register_blueprint(user_api, url_prefix="/api/users")
    app.register_blueprint(question_admin_api, url_prefix="/api/admin/questions")
    app.register_blueprint(system_admin_api, url_prefix="/api/admin/system")
    app.register_blueprint(analytics_api, url_prefix="/api/admin/analytics")
    app.register_blueprint(admin_auth_api, url_prefix="/api/admin/auth")
    app.register_blueprint(training_plan_api, url_prefix="/api/training-plan")
    app.register_blueprint(mistake_api, url_prefix="/api/mistakes")
    app.register_blueprint(job_admin_api, url_prefix="/api/admin/jobs")
    app.register_blueprint(notification_api, url_prefix="/api/notifications")
    app.register_blueprint(career_api, url_prefix="/api/career")
    app.register_blueprint(knowledge_api, url_prefix="/api/knowledge")
    app.register_blueprint(application_api, url_prefix="/api/applications")
    app.register_blueprint(schedule_api, url_prefix="/api/schedule")
    app.register_blueprint(review_note_api, url_prefix="/api/review-notes")
