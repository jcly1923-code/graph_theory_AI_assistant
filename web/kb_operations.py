"""论文/背景知识库写入与 SSE 辅助。"""
import os
from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify, request

from knowledge_base import KnowledgeBase

from web.config import Config
from web.file_saver import FileSaver
from web.knowledge_bases import (
    background_knowledge_base,
    paper_knowledge_base,
)
from web.paper_excerpt import extract_english_title_from_paper_text
from web.sse import format_sse, sse_log_event


def paper_file_save(content: str, filename: Optional[str]):
    """处理文件保存（成功/失败提示走对话正文 text）。"""
    save_result = FileSaver.save_analysis(content=content, original_filename=filename)

    if save_result["success"]:
        pdf_hint = (
            f"\n\n💾 已保存分析结果：`{save_result['filename']}`"
            f"（项目内 `{Config.SAVE_DIR}`）\n"
        )
        print(
            f"✅ 分析结果已自动保存: {save_result['file_path']} "
            f"({save_result['size']} 字符)"
        )
    else:
        print(f"❌ 自动保存失败: {save_result['error']}")
        pdf_hint = (
            f"\n\n⚠️ **自动保存失败** — {save_result['error']}\n"
            f"*请检查该目录是否可写、磁盘空间是否充足。*\n"
        )

    yield format_sse({"text": pdf_hint})


def _sse_kb_append_or_create(
    kb: KnowledgeBase,
    content: str,
    metadata: dict,
    *,
    kb_key: str,
    kb_name: str,
    fallback_path: str,
    icon: str = "📚",
) -> Dict[str, Any]:
    base = sse_log_event(
        "kb_update",
        kb_key=kb_key,
        kb_name=kb_name,
        icon=icon,
        success=False,
    )
    try:
        if kb.exists():
            print(f"📥 正在追加到现有{kb_name}...")
            result = kb.append(content, metadata=metadata)
            if result["success"]:
                base["success"] = True
                base["mode"] = "append"
                base["chunk_count"] = result.get("chunk_count", 0)
                base["new_chunks"] = result.get("new_chunks", 0)
            else:
                base["error"] = result.get("error", "未知错误")
        else:
            print(f"🆕 正在创建新的{kb_name}...")
            result = kb.create(content, metadata=metadata)
            if result["success"]:
                base["success"] = True
                base["mode"] = "create"
                base["chunk_count"] = result.get("chunk_count", 0)
                base["new_chunks"] = result.get("new_chunks", 0)
            else:
                base["error"] = result.get("error", "未知错误")
        if result["success"]:
            stats = kb.get_stats()
            path = stats.get("path", fallback_path)
            inspect_result = kb.inspect(output_file="chunks.md")
            base["index_path"] = path
            base["chunks_inspect_path"] = inspect_result.get("saved_to")
            print(
                f"📍 {kb_name} 索引路径: {path} | "
                f"分段可视化: {inspect_result.get('saved_to', '')}"
            )
    except Exception as e:
        base["error"] = str(e)
        print(f"❌ {kb_name}处理异常: {e}")
    return base


def paper_knowledge_base_update(
    content: str, filename: Optional[str], file_content: Optional[str] = None
):
    """论文知识库更新，yield SSE log。"""
    title = extract_english_title_from_paper_text(file_content or "")
    if not title:
        title = os.path.splitext(filename or "paper")[0] or "paper"
    print(f"📌 论文知识库标题: {title[:150]}{'...' if len(title) > 150 else ''}")
    metadata = {
        "filename": filename,
        "title": title,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content_type": "paper_analysis",
    }
    payload = _sse_kb_append_or_create(
        paper_knowledge_base,
        content,
        metadata,
        kb_key="paper",
        kb_name="论文知识库",
        fallback_path=Config.PAPER_FAISS_PATH,
        icon="📚",
    )
    payload["paper_title"] = title
    payload["filename"] = filename
    yield format_sse({"log": payload})


def background_knowledge_base_update(content: str, hint_prefix: str = ""):
    """背景知识库更新。"""
    metadata = {
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content_type": "background_analysis",
        "source": hint_prefix or "user_input",
    }
    payload = _sse_kb_append_or_create(
        background_knowledge_base,
        content,
        metadata,
        kb_key="background",
        kb_name="背景知识库",
        fallback_path=Config.BACKGROUND_FAISS_PATH,
        icon="🌐",
    )
    payload["hint_prefix"] = hint_prefix
    yield format_sse({"log": payload})


def kb_update_chunk_json(kb: KnowledgeBase, chunk_index: int):
    """论文/背景知识库共用的片段更新 JSON 响应。"""
    try:
        data = request.get_json()
        new_content = (data or {}).get("content", "")
        if not new_content:
            return jsonify({"success": False, "error": "内容不能为空"}), 400
        result = kb.update_chunk(chunk_index, new_content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def kb_delete_chunk_json(kb: KnowledgeBase, chunk_index: int):
    """论文/背景知识库共用的片段删除 JSON 响应。"""
    try:
        result = kb.delete_chunk(chunk_index)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
