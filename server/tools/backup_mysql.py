"""Create recoverable dumps for the business and administrator MySQL databases."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> None:
    executable = os.getenv("MYSQLDUMP_PATH") or shutil.which("mysqldump")
    if not executable:
        fallback = Path("E:/MYSQL/mysql-8.0.26-winx64/bin/mysqldump.exe")
        executable = str(fallback) if fallback.is_file() else None
    if not executable:
        raise RuntimeError("找不到 mysqldump，请设置 MYSQLDUMP_PATH。")
    output_dir = ROOT / "backups" / f"mysql-{datetime.now():%Y%m%d-%H%M%S}"
    output_dir.mkdir(parents=True, exist_ok=False)
    config = "\n".join([
        "[client]", f"host={os.getenv('MYSQL_HOST', '127.0.0.1')}",
        f"port={os.getenv('MYSQL_PORT', '3306')}", f"user={os.getenv('MYSQL_USER', 'root')}",
        f"password={os.getenv('MYSQL_PASSWORD', '')}", "default-character-set=utf8mb4", "",
    ])
    config_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".cnf", delete=False) as file:
            file.write(config)
            config_path = file.name
        for database in (os.getenv("MYSQL_DATABASE", "view"), os.getenv("MYSQL_ADMIN_DATABASE", "view_admin")):
            target = output_dir / f"{database}.sql"
            subprocess.run([
                executable, f"--defaults-extra-file={config_path}", "--single-transaction",
                "--routines", "--events", "--databases", database, f"--result-file={target}",
            ], check=True)
            print(f"BACKED_UP {database} -> {target}")
    finally:
        if config_path:
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
