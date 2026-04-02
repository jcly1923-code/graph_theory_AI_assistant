"""意图识别、主 Agent 与各子 Agent 的 build_messages。"""
import re
from typing import Any, Dict, List, Optional, Tuple

import openai

from utils.prompt import (
    BACKGROUND_AGENT_PROMPT,
    MAIN_AGENT_PROMPT,
    PAPER_AGENT_PROMPT,
    PRO_QA_EXPLORATION_PROMPT,
    PRO_QA_FACT_PROMPT,
)
from web.config import Config
from web.history import chat_history
from web.paper_excerpt import build_term_retrieval_query_from_paper
from web.qa_professional_mode import classify_professional_qa_mode
from web.retrieval import (
    BackgroundRetriever,
    PaperRetriever,
    TermRetriever,
)
from web.sse import kb_chunks_for_log, sse_log_event, truncate_for_log

# 主 Agent 判定为与图论学术无关时的统一婉拒（前端与会话历史均使用）
OUT_OF_SCOPE_REPLY = "我是一个图论学术助手，我没有办法回答你提出的其他问题。"

# 用户询问「你能做什么」等元问题时返回的固定能力说明（不调用子 Agent）
ASSISTANT_CAPABILITIES_REPLY = """我是 **图论学术助手**，主要能力如下：

1. **图论专业问答**：解答概念、定理、证明思路、方法比较等；可结合论文片段、术语库与背景知识库检索后作答。
2. **论文解析**：上传图论相关 PDF，可进行结构化解读、翻译与术语对齐、证明链拆解与综述式输出。
3. **背景沉淀**：将可复用的符号约定、问题设定等整理并写入背景知识库，供后续对话自动检索。
4. **智能路由**：主 Agent 会根据你的意图自动选择论文解析、背景沉淀或单次问答等路径。
5. **知识库管理**：在「知识库」页面可维护术语、论文索引与背景条目。

**说明**：本助手聚焦图论及相关学术场景；与图论无关的泛泛闲聊或非学术问题将婉拒。"""


class IntentType:
    """意图类型常量"""

    PAPER_ANALYSIS = "paper_analysis"
    BACKGROUND_ANALYSIS = "background_analysis"
    PROFESSIONAL_QA = "professional_qa"
    ASSISTANT_CAPABILITIES = "assistant_capabilities"
    OUT_OF_SCOPE = "out_of_scope"

    ALL = {PAPER_ANALYSIS, BACKGROUND_ANALYSIS, PROFESSIONAL_QA, ASSISTANT_CAPABILITIES, OUT_OF_SCOPE}


class IntentRecognizer:
    """意图识别器（主Agent能力）"""

    # 启发式：明显与图论无关的常见表述（保守；含图论线索时不触发）
    _OFF_TOPIC_HINTS = (
        "天气怎么样",
        "今天天气",
        "天气预报",
        "气温",
        "股票",
        "彩票",
        "世界杯",
        "nba",
        "电影票",
        "外卖",
        "快递到哪",
        "旅游推荐",
    )
    # 用户询问助手能力/功能时的短语（需避免与「介绍图论概念」等学术句混淆，故用较完整短语）
    _CAPS_HINTS = (
        "你能做什么",
        "你会做什么",
        "你可以做什么",
        "你有什么功能",
        "你的功能",
        "功能是什么",
        "有哪些功能",
        "主要功能",
        "你是做什么的",
        "你是干什么的",
        "你能帮我什么",
        "能帮我什么",
        "如何使用",
        "怎么用",
        "可以怎么用",
        "介绍一下你",
        "介绍你自己",
        "助手能做什么",
        "你的能力",
        "你会什么",
        "你会哪些",
        "what can you do",
        "capabilities",
    )
    _GRAPH_SCOPE_HINTS = (
        "图论",
        "graph theory",
        "graph ",
        "顶点",
        "邻接矩阵",
        "邻接",
        "色数",
        "色多项",
        "连通",
        "平面图",
        "哈密顿",
        "chromatic",
        "subgraph",
        "定理",
        "证明",
        "网络流",
        "图同构",
        "完全图",
        "二分图",
        "树宽",
        "turán",
        "ramsey",
    )

    @staticmethod
    def _heuristic_capabilities_query(user_input: str) -> bool:
        """用户是否在询问助手能力/功能（元问题）；含图论求解线索时不触发。"""
        raw = (user_input or "").strip()
        if not raw:
            return False
        if any(h in raw for h in IntentRecognizer._GRAPH_SCOPE_HINTS):
            return False
        if "关于" in raw and len(raw) > 18:
            if not any(
                x in raw
                for x in ("关于你", "关于助手", "关于本助手", "关于系统", "关于这个助手", "关于你的功能")
            ):
                return False
        t = raw.lower()
        if any(h in t for h in IntentRecognizer._CAPS_HINTS):
            return True
        if any(h in raw for h in IntentRecognizer._CAPS_HINTS):
            return True
        return False

    @staticmethod
    def _heuristic_out_of_scope(user_input: str) -> bool:
        """无 PDF 时：仅当明显闲聊/无关且不含图论线索时判为范围外。"""
        raw = user_input or ""
        t = raw.strip().lower()
        if not t:
            return False
        if any(h in raw for h in IntentRecognizer._GRAPH_SCOPE_HINTS):
            return False
        if any(h in t for h in IntentRecognizer._OFF_TOPIC_HINTS):
            return True
        return False

    @staticmethod
    def _heuristic_detect(
        user_input: str,
        file_content: Optional[str] = None,
        detect_text_only: bool = False,
    ) -> str:
        text = (user_input or "").lower()

        paper_keywords = ["论文", "paper", "解析", "总结", "创新点", "方法", "pdf"]
        # 与 MAIN_AGENT_PROMPT 对齐：仅当明显「要沉淀/可复用背景」时走背景，避免「定义」「为什么」等泛词误判
        persist_background_keywords = [
            "沉淀",
            "记住",
            "保存到知识库",
            "写入知识库",
            "录入",
            "背景如下",
            "背景材料",
            "补充背景",
            "符号约定",
            "前提条件",
            "先说明",
            "下面粘贴",
            "供以后",
            "后续讨论",
            "复用",
        ]

        if IntentRecognizer._heuristic_capabilities_query(user_input or ""):
            return IntentType.ASSISTANT_CAPABILITIES

        if not detect_text_only and file_content:
            return IntentType.PAPER_ANALYSIS

        # 无 PDF，或仅判断用户文字（PDF 已存在时的追问）：可判范围外
        if (not file_content or detect_text_only) and IntentRecognizer._heuristic_out_of_scope(
            user_input or ""
        ):
            return IntentType.OUT_OF_SCOPE

        if any(k in text for k in paper_keywords):
            return IntentType.PAPER_ANALYSIS
        if any(k in text for k in persist_background_keywords):
            return IntentType.BACKGROUND_ANALYSIS
        return IntentType.PROFESSIONAL_QA

    @staticmethod
    def detect_test_mode(
        user_input: str,
        file_content: Optional[str] = None,
        detect_text_only: bool = False,
    ) -> Tuple[str, str]:
        intent = IntentRecognizer._heuristic_detect(user_input, file_content, detect_text_only)
        return intent, "启发式规则识别"

    @staticmethod
    def detect_normal_mode(
        client: openai.OpenAI,
        model_name: str,
        user_input: str,
        file_content: Optional[str] = None,
        detect_text_only: bool = False,
    ) -> Tuple[str, str]:
        try:
            system_prompt = MAIN_AGENT_PROMPT
            pdf_hint = "（请忽略PDF上下文，仅根据用户问题文本进行判断）" if detect_text_only else ""
            user_prompt = (
                f"用户问题：{user_input}\n"
                f"是否有PDF上下文：{'是' if bool(file_content) else '否'}{pdf_hint}\n"
                "请输出一个标签。"
            )

            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=20,
                stream=True,
            )

            label_parts = []
            for chunk in resp:
                delta = chunk.choices[0].delta.content
                if delta:
                    label_parts.append(delta)
            label = "".join(label_parts).strip().lower()
            label = re.sub(r"[^a-z_]", "", label)

            if label in IntentType.ALL:
                return label, "大模型意图识别"

            # 大模型未给出合法标签时回退；若明显无关则优先范围外
            intent = IntentRecognizer._heuristic_detect(user_input, file_content, detect_text_only)
            return intent, "启发式意图识别"
        except Exception as e:
            print(f"⚠️ 意图识别失败，回退规则识别: {e}")
            intent = IntentRecognizer._heuristic_detect(user_input, file_content, detect_text_only)
            return intent, "启发式规则识别（异常回退）"


class MainAgent:
    """主Agent：负责历史、摘要、意图识别与任务分发"""

    @staticmethod
    def is_test_mode(settings: Dict[str, Any]) -> bool:
        return bool(settings.get("testMode", False))

    @staticmethod
    def summarize_history(max_chars: int = 1200) -> str:
        history_items = chat_history[1:] if len(chat_history) > 1 else []

        compact_lines = []
        for item in history_items[-(Config.MAX_HISTORY_MESSAGES - 1) :]:
            role = "用户" if item.get("role") == "user" else "助手"
            content = item.get("content", "")

            if "【文档内容开始】" in content and "【文档内容结束】" in content:
                content = re.sub(
                    r"【文档内容开始】[\s\S]*?【文档内容结束】",
                    "【文档内容已省略】",
                    content,
                )

            compact = content.strip().replace("\n", " ")
            compact = compact[:180] + ("..." if len(compact) > 180 else "")
            compact_lines.append(f"- {role}: {compact}")

        summary = "\n".join(compact_lines) if compact_lines else "- 无历史上下文"
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "..."

        return summary

    @staticmethod
    def dispatch_test(
        intent: str,
        user_input: str,
        file_name: Optional[str],
        file_content: Optional[str],
        settings: Dict[str, Any],
        context_summary: str = "",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """测试模式：返回提示词展示文本 + 结构化 log_entries。"""
        result: List[str] = []
        log_entries_out: List[Dict[str, Any]] = []

        result.append("=" * 60)
        result.append("🧪 当前为测试模式")
        result.append("=" * 60)
        result.append("")

        if intent == IntentType.PAPER_ANALYSIS:
            messages, log_entries = PaperAnalysisAgent.build_messages(
                user_input=user_input,
                file_content=file_content,
                settings=settings,
            )
            log_entries_out.extend(log_entries)
            result.append("📋 意图识别：论文解析 (paper_analysis)")
            if file_name:
                result.append(f"📄 关联文件：{file_name}")
            result.append("")

        elif intent == IntentType.BACKGROUND_ANALYSIS:
            messages, log_entries = BackgroundAnalysisAgent.build_messages(
                user_input=user_input,
                file_content=file_content,
                settings=settings,
            )
            log_entries_out.extend(log_entries)
            result.append("📋 意图识别：背景沉淀 (background_analysis)")
            result.append("")

        elif intent == IntentType.ASSISTANT_CAPABILITIES:
            messages = []
            result.append("📋 意图识别：助手能力说明 (assistant_capabilities)")
            result.append("")
            result.append(ASSISTANT_CAPABILITIES_REPLY)
            result.append("")

        elif intent == IntentType.OUT_OF_SCOPE:
            messages = []
            result.append("📋 意图识别：范围外 (out_of_scope)")
            result.append("")
            result.append(OUT_OF_SCOPE_REPLY)
            result.append("")

        else:
            messages, log_entries = ProfessionalQAAgent.build_messages(
                context_summary=context_summary,
                user_input=user_input,
                settings=settings,
            )
            log_entries_out.extend(log_entries)
            result.append("📋 意图识别：专业问答 (professional_qa)")
            result.append("")

            if context_summary:
                result.append("📜 前置对话背景汇总：")
                result.append(context_summary)
                result.append("")

        result.append("=" * 60)
        result.append("📝 完整的系统提示词 (System Prompt)")
        result.append("=" * 60)
        result.append("")
        if intent == IntentType.OUT_OF_SCOPE:
            result.append("（范围外请求不调用子 Agent，无系统提示词）")
        elif intent == IntentType.ASSISTANT_CAPABILITIES:
            result.append("（助手能力说明：不调用子 Agent，无系统提示词）")
        else:
            result.append(messages[0]["content"] if messages else "无系统提示词")
        result.append("")

        result.append("=" * 60)
        result.append("✅ 测试模式：提示词展示完成")
        result.append("   （未与大模型进行真实交互）")
        result.append("=" * 60)

        return "\n".join(result), log_entries_out


class PaperAnalysisAgent:
    """子Agent：论文解析"""

    @staticmethod
    def build_messages(
        user_input: str,
        file_content: Optional[str],
        settings: Dict[str, Any],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
        log_entries: List[Dict[str, Any]] = []
        system_content = PAPER_AGENT_PROMPT

        if file_content:
            query_for_terms, term_query_note = build_term_retrieval_query_from_paper(file_content)
            if not query_for_terms.strip():
                query_for_terms = file_content
                term_query_note = "全文（query 为空）"
            log_entries.append(sse_log_event("term_query_source", source=term_query_note))
            similarity_threshold = settings.get("termSimilarityThreshold", Config.TERM_SIMILARITY_THRESHOLD)
            max_terms = settings.get("termMaxResults", settings.get("maxTerms", Config.TERM_MAX_RESULTS))
            terms = TermRetriever.retrieve_terms(
                query_for_terms,
                max_terms=max_terms,
                similarity_threshold=similarity_threshold,
            )
            if terms:
                terms_prompt = TermRetriever.format_terms_for_prompt(terms)
                system_content += f"\n{terms_prompt}"
            log_entries.append(
                sse_log_event(
                    "term_retrieval",
                    agent="paper_analysis",
                    query_preview=truncate_for_log(query_for_terms),
                    count=len(terms),
                    threshold=similarity_threshold,
                    max_terms=max_terms,
                    terms=kb_chunks_for_log(terms),
                )
            )

        user_content = f"【用户实时问题】\n{user_input}"
        if file_content:
            user_content += f"\n\n【论文文本片段】\n{file_content[:Config.MAX_PDF_CHARS]}"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ], log_entries


class BackgroundAnalysisAgent:
    """子 Agent：背景沉淀（结构化输出将写入背景知识库供后续检索）"""

    @staticmethod
    def build_messages(
        user_input: str,
        file_content: Optional[str],
        settings: Dict[str, Any],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
        log_entries: List[Dict[str, Any]] = []
        system_content = BACKGROUND_AGENT_PROMPT

        bg_threshold = settings.get("backgroundSimilarityThreshold", Config.BACKGROUND_SIMILARITY_THRESHOLD)
        bg_max_results = settings.get("backgroundMaxResults", Config.BACKGROUND_MAX_RESULTS)
        query_text = file_content if file_content else user_input
        contexts = BackgroundRetriever.retrieve_context(
            query_text, max_results=bg_max_results, similarity_threshold=bg_threshold
        )
        if contexts:
            context_prompt = BackgroundRetriever.format_context_for_prompt(contexts)
            system_content += f"\n{context_prompt}"
        log_entries.append(
            sse_log_event(
                "background_retrieval",
                agent="background_analysis",
                query_preview=truncate_for_log(query_text),
                count=len(contexts),
                threshold=bg_threshold,
                max_results=bg_max_results,
                chunks=kb_chunks_for_log(contexts),
            )
        )

        user_content = f"【用户实时问题】\n{user_input}"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ], log_entries


class ProfessionalQAAgent:
    """子Agent：专业问答"""

    @staticmethod
    def build_messages(
        context_summary: str,
        user_input: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
        if settings is None:
            settings = {}
        log_entries: List[Dict[str, Any]] = []

        paper_threshold = settings.get("paperSimilarityThreshold", Config.PAPER_SIMILARITY_THRESHOLD)
        paper_max_results = settings.get("paperMaxResults", Config.PAPER_MAX_RESULTS)
        paper_contexts = PaperRetriever.retrieve_context(
            user_input, max_results=paper_max_results, similarity_threshold=paper_threshold
        )
        log_entries.append(
            sse_log_event(
                "qa_paper_retrieval",
                agent="professional_qa",
                query_preview=truncate_for_log(user_input),
                count=len(paper_contexts),
                threshold=paper_threshold,
                max_results=paper_max_results,
                chunks=kb_chunks_for_log(paper_contexts),
            )
        )

        bg_threshold = settings.get("backgroundSimilarityThreshold", Config.BACKGROUND_SIMILARITY_THRESHOLD)
        bg_max_results = settings.get("backgroundMaxResults", Config.BACKGROUND_MAX_RESULTS)
        bg_contexts = BackgroundRetriever.retrieve_context(
            user_input, max_results=bg_max_results, similarity_threshold=bg_threshold
        )
        log_entries.append(
            sse_log_event(
                "qa_background_retrieval",
                agent="professional_qa",
                query_preview=truncate_for_log(user_input),
                count=len(bg_contexts),
                threshold=bg_threshold,
                max_results=bg_max_results,
                chunks=kb_chunks_for_log(bg_contexts),
            )
        )

        boost_th = float(
            settings.get("qaFactRetrievalBoostThreshold", Config.QA_FACT_RETRIEVAL_BOOST_THRESHOLD)
        )
        qa_mode, qa_mode_reason = classify_professional_qa_mode(
            user_input,
            paper_contexts,
            bg_contexts,
            retrieval_boost_threshold=boost_th,
        )
        log_entries.append(
            sse_log_event(
                "qa_mode",
                mode=qa_mode,
                reason=qa_mode_reason,
                retrieval_boost_threshold=boost_th,
            )
        )

        system_content = (
            PRO_QA_FACT_PROMPT if qa_mode == "fact" else PRO_QA_EXPLORATION_PROMPT
        )
        if paper_contexts:
            paper_prompt = PaperRetriever.format_context_for_prompt(paper_contexts)
            system_content += f"\n{paper_prompt}"
        if bg_contexts:
            bg_prompt = BackgroundRetriever.format_context_for_prompt(bg_contexts)
            system_content += f"\n{bg_prompt}"

        user_content = (
            f"【前置对话背景汇总】\n{context_summary}\n\n"
            f"【用户当前问题】\n{user_input}"
        )
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ], log_entries
