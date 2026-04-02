"""流式对话与历史清理。"""
import openai
from flask import Flask, Response, jsonify, request, stream_with_context

from utils.agent_test_data import INTENT_TEST_LABELS
from web.agents import (
    ASSISTANT_CAPABILITIES_REPLY,
    BackgroundAnalysisAgent,
    IntentRecognizer,
    IntentType,
    MainAgent,
    OUT_OF_SCOPE_REPLY,
    PaperAnalysisAgent,
    ProfessionalQAAgent,
)
from web.history import ChatHistoryManager
from web.kb_operations import (
    background_knowledge_base_update,
    paper_file_save,
    paper_knowledge_base_update,
)
from web.sse import format_sse, sse_log_event, stream_text_chunks


def register_chat_routes(app: Flask) -> None:
    @app.route("/chat_stream_real", methods=["POST"])
    def chat_stream_real():
        data = request.json
        user_input = data.get("message", "")
        file_content = data.get("file_content")
        file_name = data.get("file_name")
        settings = data.get("settings", {})

        test_mode = MainAgent.is_test_mode(settings)
        api_base_url = settings.get("apiBaseUrl")
        api_key = settings.get("apiKey")
        model_name = settings.get("modelName", "deepseek-v3.2")
        temperature = float(settings.get("temperature", 0.7))

        if not test_mode and (not api_base_url or not api_key):
            return jsonify({"error": "未配置API信息"}), 400

        if file_content and file_name:
            ChatHistoryManager.add_user_message(
                user_input,
                {"file_name": file_name, "file_content": file_content},
            )
        else:
            ChatHistoryManager.add_user_message(user_input)

        def generate():
            try:
                client = None
                if not test_mode:
                    client = openai.OpenAI(base_url=api_base_url, api_key=api_key)

                if test_mode:
                    overall_intent, overall_method = IntentRecognizer.detect_test_mode(
                        user_input, file_content
                    )
                else:
                    overall_intent, overall_method = IntentRecognizer.detect_normal_mode(
                        client=client,
                        model_name=model_name,
                        user_input=user_input,
                        file_content=file_content,
                    )

                text_intent = None
                text_method = None
                if file_content and user_input.strip():
                    if test_mode:
                        text_intent, text_method = IntentRecognizer.detect_test_mode(
                            user_input, file_content, detect_text_only=True
                        )
                    else:
                        text_intent, text_method = IntentRecognizer.detect_normal_mode(
                            client=client,
                            model_name=model_name,
                            user_input=user_input,
                            file_content=file_content,
                            detect_text_only=True,
                        )

                yield format_sse(
                    {
                        "log": sse_log_event(
                            "intent",
                            overall_intent=overall_intent,
                            overall_label=INTENT_TEST_LABELS.get(overall_intent, overall_intent),
                            overall_method=overall_method,
                            text_intent=text_intent,
                            text_label=INTENT_TEST_LABELS.get(text_intent, text_intent)
                            if text_intent
                            else None,
                            text_method=text_method,
                            test_mode=test_mode,
                        )
                    }
                )

                full_text = ""

                if not test_mode and overall_intent == IntentType.ASSISTANT_CAPABILITIES:
                    full_text = ASSISTANT_CAPABILITIES_REPLY
                    yield from stream_text_chunks(full_text, chunk_size=5, delay=0.02)
                    yield "data: [DONE]\n\n"
                    ChatHistoryManager.add_assistant_message(full_text)
                    return

                if not test_mode and not file_content and overall_intent == IntentType.OUT_OF_SCOPE:
                    full_text = OUT_OF_SCOPE_REPLY
                    yield from stream_text_chunks(full_text, chunk_size=5, delay=0.02)
                    yield "data: [DONE]\n\n"
                    ChatHistoryManager.add_assistant_message(full_text)
                    return

                if test_mode:
                    context_summary = ""
                    if overall_intent == IntentType.PROFESSIONAL_QA:
                        context_summary = MainAgent.summarize_history()

                    full_text, test_log_entries = MainAgent.dispatch_test(
                        intent=overall_intent,
                        user_input=user_input,
                        file_name=file_name,
                        file_content=file_content,
                        settings=settings,
                        context_summary=context_summary,
                    )
                    for entry in test_log_entries:
                        yield format_sse({"log": entry})
                    yield from stream_text_chunks(full_text, chunk_size=5, delay=0.02)
                else:
                    if file_content and not user_input.strip():
                        messages, notes = PaperAnalysisAgent.build_messages(
                            user_input=user_input,
                            file_content=file_content,
                            settings=settings,
                        )
                        for note in notes:
                            yield format_sse({"log": note})

                        resp = client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=10000,
                            stream=True,
                        )

                        for chunk in resp:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                full_text += delta
                                yield format_sse({"text": delta})

                        yield from paper_file_save(full_text, file_name)
                        yield from paper_knowledge_base_update(
                            full_text, file_name, file_content
                        )

                    elif file_content and user_input.strip():
                        yield format_sse(
                            {
                                "log": sse_log_event(
                                    "pipeline_step",
                                    step=1,
                                    phase="paper_analysis",
                                    label="论文分析（PDF）",
                                )
                            }
                        )

                        paper_messages, paper_notes = PaperAnalysisAgent.build_messages(
                            user_input="请总结这篇论文的核心内容",
                            file_content=file_content,
                            settings=settings,
                        )
                        for note in paper_notes:
                            yield format_sse({"log": note})

                        paper_resp = client.chat.completions.create(
                            model=model_name,
                            messages=paper_messages,
                            temperature=temperature,
                            max_tokens=10000,
                            stream=True,
                        )

                        paper_text = ""
                        for chunk in paper_resp:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                paper_text += delta
                                yield format_sse({"text": delta})

                        yield from paper_file_save(paper_text, file_name)
                        yield from paper_knowledge_base_update(
                            paper_text, file_name, file_content
                        )

                        if text_intent and text_intent != IntentType.PAPER_ANALYSIS:
                            yield format_sse(
                                {
                                    "log": sse_log_event(
                                        "pipeline_step",
                                        step=2,
                                        phase="followup",
                                        label="处理用户问题",
                                    )
                                }
                            )

                            if text_intent == IntentType.BACKGROUND_ANALYSIS:
                                bg_messages, bg_notes = BackgroundAnalysisAgent.build_messages(
                                    user_input=user_input,
                                    file_content=None,
                                    settings=settings,
                                )
                                for note in bg_notes:
                                    yield format_sse({"log": note})

                                bg_resp = client.chat.completions.create(
                                    model=model_name,
                                    messages=bg_messages,
                                    temperature=temperature,
                                    max_tokens=10000,
                                    stream=True,
                                )

                                bg_text = ""
                                for chunk in bg_resp:
                                    delta = chunk.choices[0].delta.content
                                    if delta:
                                        bg_text += delta
                                        yield format_sse({"text": delta})

                                yield from background_knowledge_base_update(
                                    bg_text, hint_prefix=user_input[:60]
                                )
                                full_text = (
                                    f"**论文分析：**\n{paper_text}\n\n"
                                    f"**背景知识分析：**\n{bg_text}"
                                )

                            elif text_intent == IntentType.OUT_OF_SCOPE:
                                yield format_sse(
                                    {
                                        "log": sse_log_event(
                                            "pipeline_step",
                                            step=2,
                                            phase="out_of_scope",
                                            label="追问与图论学术无关，已婉拒",
                                        )
                                    }
                                )
                                refusal = OUT_OF_SCOPE_REPLY
                                yield from stream_text_chunks(refusal, chunk_size=5, delay=0.02)
                                full_text = (
                                    f"**论文分析：**\n{paper_text}\n\n"
                                    f"**问题回答：**\n{refusal}"
                                )

                            elif text_intent == IntentType.ASSISTANT_CAPABILITIES:
                                yield format_sse(
                                    {
                                        "log": sse_log_event(
                                            "pipeline_step",
                                            step=2,
                                            phase="assistant_capabilities",
                                            label="助手能力说明",
                                        )
                                    }
                                )
                                cap = ASSISTANT_CAPABILITIES_REPLY
                                yield from stream_text_chunks(cap, chunk_size=5, delay=0.02)
                                full_text = (
                                    f"**论文分析：**\n{paper_text}\n\n"
                                    f"**说明：**\n{cap}"
                                )

                            else:
                                context_summary = MainAgent.summarize_history()
                                qa_messages, qa_notes = ProfessionalQAAgent.build_messages(
                                    context_summary=context_summary,
                                    user_input=user_input,
                                    settings=settings,
                                )
                                for note in qa_notes:
                                    yield format_sse({"log": note})

                                qa_resp = client.chat.completions.create(
                                    model=model_name,
                                    messages=qa_messages,
                                    temperature=temperature,
                                    max_tokens=10000,
                                    stream=True,
                                )

                                qa_text = ""
                                for chunk in qa_resp:
                                    delta = chunk.choices[0].delta.content
                                    if delta:
                                        qa_text += delta
                                        yield format_sse({"text": delta})

                                full_text = (
                                    f"**论文分析：**\n{paper_text}\n\n"
                                    f"**问题回答：**\n{qa_text}"
                                )
                        else:
                            full_text = paper_text

                    else:
                        if overall_intent == IntentType.PAPER_ANALYSIS:
                            messages, notes = PaperAnalysisAgent.build_messages(
                                user_input=user_input,
                                file_content=None,
                                settings=settings,
                            )
                            for note in notes:
                                yield format_sse({"log": note})

                            resp = client.chat.completions.create(
                                model=model_name,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=10000,
                                stream=True,
                            )

                            for chunk in resp:
                                delta = chunk.choices[0].delta.content
                                if delta:
                                    full_text += delta
                                    yield format_sse({"text": delta})
                        elif overall_intent == IntentType.BACKGROUND_ANALYSIS:
                            messages, notes = BackgroundAnalysisAgent.build_messages(
                                user_input=user_input,
                                file_content=None,
                                settings=settings,
                            )
                            for note in notes:
                                yield format_sse({"log": note})

                            resp = client.chat.completions.create(
                                model=model_name,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=10000,
                                stream=True,
                            )

                            for chunk in resp:
                                delta = chunk.choices[0].delta.content
                                if delta:
                                    full_text += delta
                                    yield format_sse({"text": delta})

                            yield from background_knowledge_base_update(
                                full_text, hint_prefix=user_input[:60]
                            )
                        else:
                            context_summary = MainAgent.summarize_history()
                            messages, notes = ProfessionalQAAgent.build_messages(
                                context_summary=context_summary,
                                user_input=user_input,
                                settings=settings,
                            )
                            for note in notes:
                                yield format_sse({"log": note})

                            resp = client.chat.completions.create(
                                model=model_name,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=10000,
                                stream=True,
                            )

                            for chunk in resp:
                                delta = chunk.choices[0].delta.content
                                if delta:
                                    full_text += delta
                                    yield format_sse({"text": delta})

                yield "data: [DONE]\n\n"

                ChatHistoryManager.add_assistant_message(full_text)

            except Exception as e:
                error_msg = f"抱歉，处理请求时出现错误: {str(e)}"
                yield format_sse({"text": error_msg})

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    @app.route("/clear_history", methods=["POST"])
    def clear_history():
        ChatHistoryManager.clear()
        return jsonify({"success": True})
