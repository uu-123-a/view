"""允许通过 ``python -m server`` 启动后端。"""

from .app import create_app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
