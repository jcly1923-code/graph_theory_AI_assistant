"""FAISS 知识库实例初始化与全局引用。"""
from typing import Dict, Optional, Tuple

from knowledge_base import KnowledgeBase

from web.config import Config


def _make_kb(index_path: str, chunk_size: Optional[int] = None) -> KnowledgeBase:
    cs = Config.DEFAULT_CHUNK_SIZE if chunk_size is None else chunk_size
    return KnowledgeBase(
        index_path=index_path,
        model_name=Config.DEFAULT_MODEL_NAME,
        chunk_size=cs,
        chunk_overlap=Config.DEFAULT_CHUNK_OVERLAP,
    )


paper_knowledge_base = _make_kb(Config.PAPER_FAISS_PATH)
term_knowledge_base = _make_kb(Config.TERM_FAISS_PATH, Config.TERM_CHUNK_SIZE)
background_knowledge_base = _make_kb(Config.BACKGROUND_FAISS_PATH)

KB_TYPE_REGISTRY: Dict[str, Tuple[KnowledgeBase, str]] = {
    "paper": (paper_knowledge_base, Config.PAPER_FAISS_PATH),
    "term": (term_knowledge_base, Config.TERM_FAISS_PATH),
    "background": (background_knowledge_base, Config.BACKGROUND_FAISS_PATH),
}

print("\n🔍 检查知识库状态:")
for kb, label, path, icon, extra_hint in (
    (paper_knowledge_base, "论文", Config.PAPER_FAISS_PATH, "📦", None),
    (term_knowledge_base, "术语", Config.TERM_FAISS_PATH, "⚠️", "     请通过知识库管理页面上传术语文件"),
    (background_knowledge_base, "背景", Config.BACKGROUND_FAISS_PATH, "📦", None),
):
    if kb.exists():
        kb.load()
        stats = kb.get_stats()
        print(f"  ✅ {label}知识库: {stats.get('chunk_count', 0)} 个片段")
    else:
        print(f"  {icon} {label}知识库: 尚未创建 (路径: {path})")
        if extra_hint:
            print(extra_hint)
