"""Application logging with rotating files and secret redaction."""

from __future__ import annotations

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SecretFilter(logging.Filter):
    patterns = [
        re.compile(r"(?i)(api[_-]?key|api[_-]?secret|password|authorization)(\s*[=:]\s*)[^\s,;]+"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.patterns:
            message = pattern.sub(r"\1\2[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging(app) -> None:
    log_dir = Path(os.getenv("MOSS_LOG_DIR", Path(__file__).resolve().parent / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_dir / "moss.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.addFilter(SecretFilter())
    for old_handler in app.logger.handlers[:]:
        app.logger.removeHandler(old_handler)
        old_handler.close()
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, os.getenv("MOSS_LOG_LEVEL", "INFO").upper(), logging.INFO))
