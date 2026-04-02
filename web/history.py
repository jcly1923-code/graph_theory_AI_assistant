"""主 Agent 聊天历史（内存）。"""
from typing import Any, Dict, Optional

from web.config import Config

chat_history: list = [Config.SYSTEM_PROMPT.copy()]


class ChatHistoryManager:
    """聊天历史管理类"""

    @staticmethod
    def add_user_message(message: str, file_info: Optional[Dict[str, Any]] = None) -> None:
        global chat_history

        if file_info:
            file_content = file_info["file_content"]

            enhanced_message = (
                f"{message}\n\n"
                f"【参考文档：{file_info['file_name']}】\n"
                f"【文档内容开始】\n"
                f"{file_content}\n"
                f"【文档内容结束】"
            )
            chat_history.append({"role": "user", "content": enhanced_message})
        else:
            chat_history.append({"role": "user", "content": message})

        ChatHistoryManager.trim_history()

    @staticmethod
    def add_assistant_message(content: str) -> None:
        global chat_history
        chat_history.append({"role": "assistant", "content": content})
        ChatHistoryManager.trim_history()

    @staticmethod
    def trim_history() -> None:
        global chat_history
        if len(chat_history) > Config.MAX_HISTORY_MESSAGES:
            chat_history = [chat_history[0]] + chat_history[-(Config.MAX_HISTORY_MESSAGES - 1) :]

    @staticmethod
    def clear() -> None:
        global chat_history
        chat_history = [Config.SYSTEM_PROMPT.copy()]
