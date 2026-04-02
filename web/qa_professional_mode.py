"""专业问答子模式：事实型 vs 思路探讨型（启发式 + 检索弱信号）。"""
import re
from typing import List, Literal, Tuple

QAMode = Literal["fact", "exploration"]


def _max_similarity(contexts: List[Tuple[str, float]]) -> float:
    if not contexts:
        return 0.0
    return max(float(s) for _, s in contexts)


def _has_exploration_strong(text: str) -> bool:
    t = (text or "").strip()
    if re.search(
        r"(证明|求证|证\s*明|猜想|思路|是否成立|开放问题|如何证|怎么证|怎样证|反例|构造|紧性|研究现状|尚未解决|未解决|未知|前沿进展)",
        t,
    ):
        return True
    if re.search(r"(下界|上界).{0,12}(如何|可否|能否|证明|估计)", t):
        return True
    return False


def _strong_fact_question(text: str) -> bool:
    """明显「定义/含义」类问法。"""
    t = (text or "").strip()
    if re.search(r"(的定义|是什么意思|什么含义|指的是什么|指的是哪|何谓|何意)", t):
        return True
    if re.search(r"^什么是", t):
        return True
    if re.search(r"请解释", t) and not re.search(r"(证明|思路|猜想|是否成立)", t):
        return True
    return False


def _weak_fact_question(text: str) -> bool:
    """在强事实之外，短句、术语向、且无明显探讨词时，可视为事实向（供检索弱信号使用）。"""
    if _strong_fact_question(text):
        return True
    t = (text or "").strip()
    if len(t) > 120:
        return False
    if _has_exploration_strong(t):
        return False
    if re.search(r"(什么|哪个|何种|含义|定义|意思)", t):
        return True
    return False


def classify_professional_qa_mode(
    user_input: str,
    paper_contexts: List[Tuple[str, float]],
    bg_contexts: List[Tuple[str, float]],
    *,
    retrieval_boost_threshold: float,
) -> Tuple[QAMode, str]:
    """
    先排除明显「思路探讨」，再认「事实型」，最后用检索最高分做弱信号补强。
    其余默认思路探讨，减少开放题被短答误伤。
    """
    text = (user_input or "").strip()

    if _has_exploration_strong(text):
        return "exploration", "heuristic_explore"

    if _strong_fact_question(text):
        return "fact", "heuristic_fact"

    combined = paper_contexts + bg_contexts
    mx = _max_similarity(combined)
    if mx >= retrieval_boost_threshold and _weak_fact_question(text):
        return "fact", "retrieval_boost"

    return "exploration", "default_explore"
