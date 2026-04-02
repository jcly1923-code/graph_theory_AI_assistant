"""向量检索与 Term / Paper / Background 检索器。"""
from typing import List, Tuple

from knowledge_base import KnowledgeBase

from web.config import Config
import web.knowledge_bases as kb_store


def _retrieve_scored_from_kb(
    kb: KnowledgeBase,
    query_text: str,
    *,
    max_results: int,
    similarity_threshold: float,
    log_label: str,
) -> List[Tuple[str, float]]:
    """从指定知识库按相似度阈值检索片段（归一化分数）。"""
    try:
        if not kb.exists():
            print(f"⚠️ {log_label}不存在，跳过检索")
            return []
        if not kb.ensure_loaded():
            return []
        results = kb.query_with_scores(
            query_text, k=max_results * 2, return_normalized=True
        )
        filtered = [(doc, sim) for doc, sim in results if sim >= similarity_threshold]
        filtered.sort(key=lambda x: x[1], reverse=True)
        filtered = filtered[:max_results]
        print(
            f"📚 {log_label}检索完成: 共 {len(results)} 个候选，"
            f"高于阈值 {similarity_threshold} 的有 {len(filtered)} 个"
        )
        return filtered
    except (ValueError, RuntimeError) as e:
        print(f"❌ {log_label}检索失败: {e}")
        return []
    except Exception as e:
        print(f"❌ {log_label}检索失败（未知错误）: {e}")
        return []


def _format_scored_context_for_prompt(
    contexts: List[Tuple[str, float]],
    *,
    heading_line: str,
    intro: str,
    item_prefix: str,
) -> str:
    """论文/背景知识库共用的检索结果格式化。"""
    if not contexts:
        return ""
    out = f"\n\n{heading_line}\n\n"
    out += intro + "\n\n"
    for i, (content, similarity) in enumerate(contexts, 1):
        out += f"### {item_prefix} {i} (相关度: {similarity:.2f})\n{content.strip()}\n\n"
    return out


class TermRetriever:
    """术语检索工具"""

    @staticmethod
    def retrieve_terms(
        query_text: str,
        max_terms: int = 15,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        return _retrieve_scored_from_kb(
            kb_store.term_knowledge_base,
            query_text,
            max_results=max_terms,
            similarity_threshold=similarity_threshold,
            log_label="术语知识库",
        )

    @staticmethod
    def format_terms_for_prompt(terms: List[Tuple[str, float]]) -> str:
        if not terms:
            return ""

        formatted_terms = "\n\n## 📖 参考术语定义\n\n"
        formatted_terms += "以下是从术语知识库中检索到的相关术语定义，请参考这些术语来解释论文内容：\n\n"

        for i, (term_content, similarity) in enumerate(terms, 1):
            term_clean = term_content.strip()
            formatted_terms += f"### 术语 {i} (相似度: {similarity:.2f})\n{term_clean}\n\n"

        formatted_terms += "请基于以上术语定义，对论文进行准确的专业解析。\n"

        return formatted_terms


class BackgroundRetriever:
    """背景知识检索工具"""

    @staticmethod
    def retrieve_context(
        query_text: str, max_results: int = 5, similarity_threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        return _retrieve_scored_from_kb(
            kb_store.background_knowledge_base,
            query_text,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            log_label="背景知识库",
        )

    @staticmethod
    def format_context_for_prompt(contexts: List[Tuple[str, float]]) -> str:
        return _format_scored_context_for_prompt(
            contexts,
            heading_line="## 🌐 参考背景知识",
            intro="以下是从背景知识库中检索到的相关信息，请参考这些内容来增强回答：",
            item_prefix="背景",
        )


class PaperRetriever:
    """论文知识检索工具"""

    @staticmethod
    def retrieve_context(
        query_text: str,
        max_results: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        return _retrieve_scored_from_kb(
            kb_store.paper_knowledge_base,
            query_text,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            log_label="论文知识库",
        )

    @staticmethod
    def format_context_for_prompt(contexts: List[Tuple[str, float]]) -> str:
        return _format_scored_context_for_prompt(
            contexts,
            heading_line="## 📄 参考论文知识",
            intro="以下是从论文知识库中检索到的相关知识片段，请参考这些内容进行回答：",
            item_prefix="论文片段",
        )
