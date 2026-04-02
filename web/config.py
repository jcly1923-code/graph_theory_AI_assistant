"""应用配置与运行时根目录。"""
import os
import sys

from utils.prompt import MAIN_AGENT_PROMPT


def get_runtime_base_dir() -> str:
    """源码模式为项目目录，打包后为 exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """应用统一配置"""

    MAX_PDF_CHARS = 100000
    MAX_FILE_SIZE_MB = 20

    MAX_HISTORY_TURNS = 3
    MAX_HISTORY_MESSAGES = MAX_HISTORY_TURNS * 2 + 1

    BASE_DIR = get_runtime_base_dir()

    SAVE_DIR = "knowledge/paper/origin_paper"
    SAVE_PATH = os.path.join(BASE_DIR, SAVE_DIR)

    SYSTEM_PROMPT = {
        "role": "system",
        "content": MAIN_AGENT_PROMPT,
    }

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50
    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

    PAPER_FAISS_PATH = os.path.join(BASE_DIR, "knowledge", "paper", "faiss_paper")
    PAPER_ORIGIN_PATH = os.path.join(BASE_DIR, "knowledge", "paper", "origin_paper")

    TERM_FAISS_PATH = os.path.join(BASE_DIR, "knowledge", "term", "faiss_term")
    TERM_ORIGIN_PATH = os.path.join(BASE_DIR, "knowledge", "term", "origin_term", "terms.txt")
    TERM_CHUNK_SIZE = 300

    BACKGROUND_FAISS_PATH = os.path.join(BASE_DIR, "knowledge", "background", "faiss_background")
    BACKGROUND_ORIGIN_PATH = os.path.join(BASE_DIR, "knowledge", "background", "origin_background")

    TERM_SIMILARITY_THRESHOLD = 0.5
    BACKGROUND_SIMILARITY_THRESHOLD = 0.5
    PAPER_SIMILARITY_THRESHOLD = 0.5

    TERM_MAX_RESULTS = 15
    BACKGROUND_MAX_RESULTS = 5
    PAPER_MAX_RESULTS = 5

    # 专业问答：检索最高分高于此阈值且问句像「定义类」时，弱信号强化为事实型
    QA_FACT_RETRIEVAL_BOOST_THRESHOLD = 0.78

    TERM_QUERY_ABSTRACT_MAX_CHARS = 4000
    TERM_QUERY_BODY_HEAD_CHARS = 8000
    TERM_QUERY_MAX_TOTAL_CHARS = 12000
    TERM_QUERY_FALLBACK_PREFIX_CHARS = 8000
    TERM_QUERY_MIN_OK_CHARS = 200

    @classmethod
    def ensure_directories(cls) -> None:
        os.makedirs(cls.SAVE_PATH, exist_ok=True)
        os.makedirs(cls.PAPER_FAISS_PATH, exist_ok=True)
        os.makedirs(cls.PAPER_ORIGIN_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(cls.TERM_ORIGIN_PATH), exist_ok=True)
        os.makedirs(cls.TERM_FAISS_PATH, exist_ok=True)
        os.makedirs(cls.BACKGROUND_FAISS_PATH, exist_ok=True)
        os.makedirs(cls.BACKGROUND_ORIGIN_PATH, exist_ok=True)

        print("📁 目录创建/检查完成:")
        print(f"  - 文件保存目录: {cls.SAVE_PATH}")
        print(f"  - 论文知识库: {cls.PAPER_FAISS_PATH}")
        print(f"  - 术语知识库: {cls.TERM_FAISS_PATH}")
        print(f"  - 术语原始文件: {cls.TERM_ORIGIN_PATH}")
        print(f"  - 背景知识库: {cls.BACKGROUND_FAISS_PATH}")


Config.ensure_directories()
