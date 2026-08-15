"""MOSS backend application factory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv(Path(__file__).with_name(".env"))

from .logging_config import configure_logging
from .routes import register_routes
from .security import register_security


def _boolean(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> Flask:
    environment = os.getenv("MOSS_ENV", "development").lower()
    secret_key = os.getenv("MOSS_SECRET_KEY", "")
    if environment == "production" and len(secret_key) < 32:
        raise RuntimeError("生产环境必须配置至少 32 个字符的 MOSS_SECRET_KEY。")

    dist_dir = Path(__file__).resolve().parents[1] / "dist"
    app = Flask(__name__, static_folder=str(dist_dir), static_url_path="")
    app.config.update(
        SECRET_KEY=secret_key or "moss-local-development-key",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_boolean("MOSS_COOKIE_SECURE", environment == "production"),
        PERMANENT_SESSION_LIFETIME=8 * 60 * 60,
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        JSON_AS_ASCII=False,
    )
    if _boolean("MOSS_TRUST_PROXY", False):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    configure_logging(app)
    register_security(app)
    register_routes(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "moss-view"})

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path: str = ""):
        if path == "api" or path.startswith("api/"):
            return jsonify({"error": "接口不存在。"}), 404
        candidate = dist_dir / path
        if path and candidate.is_file():
            return send_from_directory(dist_dir, path)
        index = dist_dir / "index.html"
        if index.is_file():
            return send_from_directory(dist_dir, "index.html")
        return jsonify({"error": "前端尚未构建，请先运行 npm run build。"}), 503

    @app.errorhandler(413)
    def file_too_large(_error):
        return jsonify({"error": "上传文件不能超过 25MB。"}), 413

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(
            "Unhandled server error",
            exc_info=(type(error), error, error.__traceback__),
        )
        return jsonify({"error": "服务器暂时无法处理请求，请稍后重试。"}), 500

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=_boolean("MOSS_DEBUG", True))
