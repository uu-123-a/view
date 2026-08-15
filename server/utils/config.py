"""环境配置读取。"""

import os


class Config:
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    NEO4J_URI = os.getenv("NEO4J_URI", "")
