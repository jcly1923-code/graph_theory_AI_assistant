"""论文纯文本：摘要截取、术语检索 query、英文标题启发式。"""
import re
from typing import List, Optional, Tuple

from web.config import Config


def _extract_abstract_from_paper(text: str) -> Tuple[Optional[str], int]:
    """
    从论文纯文本中启发式截取 Abstract 段落。
    返回 (abstract 或 None, 摘要结束处在 text 中的下标，无摘要时为 0)。
    """
    if not text or len(text) < 80:
        return None, 0
    head = text[:200000]
    m = re.search(r"(?is)(?:^|\n)\s*Abstract\s*\n\s*", head)
    if m:
        rest = head[m.end() :]
        m_end = re.search(
            r"(?m)^\s*(?:"
            r"1\s*\.\s*Introduction\b|"
            r"1\s+Introduction\b|"
            r"\d+\s*\.\s*Introduction\b|"
            r"Introduction\b|"
            r"Keywords\b|"
            r"Key\s+words\b|"
            r"MSC\s*\d|"
            r"AMS\s+subject"
            r")",
            rest,
        )
        if m_end:
            body = rest[: m_end.start()].strip()
            end_in_head = m.end() + m_end.start()
        else:
            raw = rest[: Config.TERM_QUERY_ABSTRACT_MAX_CHARS]
            body = raw.strip()
            end_in_head = m.end() + len(raw)
        if len(body) >= 80:
            clipped = body[: Config.TERM_QUERY_ABSTRACT_MAX_CHARS]
            return clipped, min(end_in_head, len(head))
    m2 = re.search(r"(?is)(?:^|\n)\s*Abstract\s*[:\s.\u2014\-]\s*", head[:50000])
    if m2:
        rest = head[m2.end() :]
        m_end = re.search(
            r"(?m)(?:^\s*$|\n\s*\n|Introduction\b|Keywords\b|Key\s+words\b)",
            rest[:12000],
        )
        if m_end:
            body = rest[: m_end.start()].strip()
            span = m_end.start()
        else:
            body = rest[: Config.TERM_QUERY_ABSTRACT_MAX_CHARS].strip()
            span = len(body)
        if len(body) >= 80:
            clipped = body[: Config.TERM_QUERY_ABSTRACT_MAX_CHARS]
            end_in_head = m2.end() + span
            return clipped, min(end_in_head, len(head))
    return None, 0


def build_term_retrieval_query_from_paper(file_content: str) -> Tuple[str, str]:
    """用「摘要 + 正文前段」拼成术语检索 query。返回 (query_text, 简短说明)。"""
    if not file_content or not file_content.strip():
        return "", ""
    fc = file_content[: Config.MAX_PDF_CHARS]
    abstract, after_idx = _extract_abstract_from_paper(fc)
    if abstract and after_idx > 0:
        body_head = fc[after_idx : after_idx + Config.TERM_QUERY_BODY_HEAD_CHARS]
    else:
        body_head = fc[: Config.TERM_QUERY_BODY_HEAD_CHARS]

    parts: List[str] = []
    if abstract:
        parts.append(abstract.strip())
    bh = body_head.strip()
    if bh:
        parts.append(bh)

    query = "\n\n".join(parts).strip()
    if len(query) < Config.TERM_QUERY_MIN_OK_CHARS:
        query = fc[: Config.TERM_QUERY_FALLBACK_PREFIX_CHARS].strip()
        note = "摘要/前段过短，已回退全文前缀"
    else:
        note = "摘要+正文前段（启发式）" if abstract else "正文前段（未识别到摘要）"

    if len(query) > Config.TERM_QUERY_MAX_TOTAL_CHARS:
        query = query[: Config.TERM_QUERY_MAX_TOTAL_CHARS]
    return query, note


def extract_english_title_from_paper_text(text: str) -> str:
    """从 PDF 提取文本中启发式得到论文英文标题（用于知识库展示）。"""
    if not text or not text.strip():
        return ""
    head = text[:12000]
    head = re.sub(r"\[第\d+/\d+页\]\s*", "", head)
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]

    def latin_letters(s: str) -> int:
        return sum(1 for c in s if "A" <= c <= "Z" or "a" <= c <= "z")

    def looks_like_author_line(s: str) -> bool:
        low = s.lower()
        if "@" in s:
            return True
        if re.search(r"\b(university|department|college|institute|school)\b", low):
            return True
        if re.search(r"\b(and|&)\b", low) and len(s.split()) <= 24:
            return True
        if s.count(",") >= 1 and latin_letters(s) >= 12 and len(s) < 220:
            return True
        return False

    skip_re = re.compile(
        r"^(arxiv:|preprint|doi:|http|www\.|vol\.|pp\.|received|revised|accepted|"
        r"communications in|journal of|proceedings of|email\s*:)",
        re.I,
    )

    for i, line in enumerate(lines[:40]):
        if len(line) < 8:
            continue
        if skip_re.search(line.strip()):
            continue
        if re.match(r"^\d{4}\.\d{4,5}(v\d+)?(\s|$)", line.strip()):
            continue
        low = line.lower()
        if low in ("abstract", "summary", "keywords", "key words", "msc"):
            break
        if re.match(r"^abstract[\s.:]", low):
            break
        if latin_letters(line) < 10:
            continue

        title = re.sub(r"\s+", " ", line).strip()
        if i + 1 < len(lines):
            nxt = lines[i + 1]
            nlow = nxt.lower()
            if nlow in ("abstract", "summary") or nlow.startswith("abstract"):
                return title[:300]
            if looks_like_author_line(nxt):
                return title[:300]
            if (
                latin_letters(nxt) >= 8
                and len(nxt) < 180
                and not looks_like_author_line(nxt)
                and not nlow.startswith("abstract")
                and len(title) < 120
            ):
                title = f"{title} {nxt.strip()}"
        if len(title) >= 10 and latin_letters(title) >= 10:
            return title[:300]
    return ""
