"""页面与 PDF 上传。"""
import io

from flask import Flask, abort, jsonify, render_template, request

from web.config import Config
from web.pdf import PDFProcessor

# 知识库详情页 slug → 展示用元数据（与 web.knowledge_bases.KB_TYPE_REGISTRY 键一致）
KB_DETAIL_PAGES = {
    "term": {
        "title": "术语知识库",
        "description": "编辑术语原文、查看分段并重建向量索引，供论文解析与问答对齐译名。",
        "icon": "📖",
        "badge": "可编辑",
    },
    "paper": {
        "title": "论文知识库",
        "description": "管理已入库论文与片段，支持检索、编辑与导出统计。",
        "icon": "📄",
        "badge": "可管理",
    },
    "background": {
        "title": "背景知识库",
        "description": "维护可复用的背景条目，供对话中自动检索与引用。",
        "icon": "🌐",
        "badge": "可管理",
    },
}


def register_page_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/knowledge_base")
    def knowledge_base_index():
        return render_template("knowledge_base.html", page="index", kb_pages=KB_DETAIL_PAGES)

    @app.route("/knowledge_base/<kb_type>")
    def knowledge_base_detail(kb_type: str):
        if kb_type not in KB_DETAIL_PAGES:
            abort(404)
        return render_template(
            "knowledge_base.html",
            page="detail",
            kb_type=kb_type,
            kb_meta=KB_DETAIL_PAGES[kb_type],
            kb_pages=KB_DETAIL_PAGES,
        )

    @app.route("/upload_pdf", methods=["POST"])
    def upload_pdf():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "没有上传文件"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "文件名为空"}), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"success": False, "error": "请上传PDF文件"}), 400

        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            if file_size > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
                return jsonify(
                    {
                        "success": False,
                        "error": f"文件大小不能超过{Config.MAX_FILE_SIZE_MB}MB",
                    }
                ), 400

            file_stream = io.BytesIO(file.read())
            extracted_text = PDFProcessor.extract_text(file_stream)

            print(f"✅ 成功提取PDF文本，长度: {len(extracted_text)}字符")

            page_count = len([p for p in extracted_text.split("\n\n") if p.startswith("[第")])

            return jsonify(
                {
                    "success": True,
                    "content": extracted_text,
                    "filename": file.filename,
                    "page_count": page_count,
                    "char_count": len(extracted_text),
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
