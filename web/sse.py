"""SSE 格式化与流式分块。"""
import json
import time
from typing import Any, Dict, List, Tuple

LOG_SCHEMA_VERSION = 1


def truncate_for_log(text: str, max_len: int = 200) -> str:
    """运行日志中展示的 query 截断。"""
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + "…"


def kb_chunks_for_log(contexts: List[Tuple[str, float]], preview_len: int = 220) -> List[Dict[str, Any]]:
    """知识库召回片段 → 运行日志中的结构化列表（含相似度）。"""
    out: List[Dict[str, Any]] = []
    for doc, score in contexts:
        d = doc or ""
        preview = d if len(d) <= preview_len else d[:preview_len] + "…"
        out.append({"preview": preview, "similarity": round(float(score), 4)})
    return out


def sse_log_event(kind: str, **fields: Any) -> Dict[str, Any]:
    """运行日志结构化事件（前端按 kind 渲染）。"""
    payload: Dict[str, Any] = {"v": LOG_SCHEMA_VERSION, "kind": kind}
    payload.update(fields)
    return payload


def format_sse(data: Dict[str, Any]) -> str:
    """SSE。可含 `text`（主回复正文）与 `log`（运行日志 JSON）。"""
    json_str = json.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n"


def stream_text_chunks(text: str, chunk_size: int = 6, delay: float = 0.01):
    """将文本按 chunk 流式输出为 SSE。"""
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        yield format_sse({"text": chunk})
        if delay > 0:
            time.sleep(delay)
