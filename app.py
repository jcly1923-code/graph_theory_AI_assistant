# 基于 Flask 的科研助理 Web 应用：入口与静态资源路径
import os
import sys

from flask import Flask

import web.knowledge_bases  # noqa: F401  # 初始化知识库与目录

from web.routes import register_routes


def _runtime_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


_ROOT = _runtime_root()

app = Flask(
    __name__,
    template_folder=os.path.join(_ROOT, "templates"),
    static_folder=os.path.join(_ROOT, "static"),
)
register_routes(app)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
