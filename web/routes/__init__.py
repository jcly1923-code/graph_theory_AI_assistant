"""注册 Flask 路由。"""
from flask import Flask

from web.routes.chat import register_chat_routes
from web.routes.kb import register_kb_routes
from web.routes.pages import register_page_routes


def register_routes(app: Flask) -> None:
    register_page_routes(app)
    register_chat_routes(app)
    register_kb_routes(app)
