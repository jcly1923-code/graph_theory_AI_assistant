"""知识库 REST API。"""
import os
import traceback

from flask import Flask, jsonify, request

from web.config import Config
from web.kb_operations import kb_delete_chunk_json, kb_update_chunk_json
from web.knowledge_bases import KB_TYPE_REGISTRY, background_knowledge_base, paper_knowledge_base


def register_kb_routes(app: Flask) -> None:
    @app.route("/api/kb/stats", methods=["GET"])
    def get_kb_stats():
        try:
            payload = {"success": True}
            for key, (kb, path) in KB_TYPE_REGISTRY.items():
                payload[key] = kb.get_stats() if kb.exists() else {"exists": False, "path": path}
            return jsonify(payload)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/term/load", methods=["GET"])
    def load_term_content():
        try:
            if os.path.exists(Config.TERM_ORIGIN_PATH):
                with open(Config.TERM_ORIGIN_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = ""

            return jsonify({"success": True, "content": content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/term/rebuild", methods=["POST"])
    def rebuild_term_index():
        import web.knowledge_bases as kb_mod

        try:
            data = request.json
            content = data.get("content") if data else None

            default_content = """
【术语】cycle（圈）
【定义】一条长度大于等于3的、首尾相交的路径，其中除了起点和终点是同一个顶点外，其余顶点和边都不重复。
【语境】"A graph is bipartite if and only if it contains no odd cycle." → "图是二分图当且仅当它不包含奇圈。"
"""

            if content is not None:
                print("📝 使用前端传入的内容...")
                if content.strip():
                    final_content = content
                    print("✅ 使用用户编辑的内容")
                else:
                    print("📄 前端传入内容为空，使用默认内容...")
                    final_content = default_content
            else:
                if os.path.exists(Config.TERM_ORIGIN_PATH):
                    print("📂 使用现有文件内容...")
                    with open(Config.TERM_ORIGIN_PATH, "r", encoding="utf-8") as f:
                        final_content = f.read()
                else:
                    print("📄 文件不存在，使用默认内容...")
                    final_content = default_content

            print(f"💾 保存内容到文件: {Config.TERM_ORIGIN_PATH}")
            os.makedirs(os.path.dirname(Config.TERM_ORIGIN_PATH), exist_ok=True)
            with open(Config.TERM_ORIGIN_PATH, "w", encoding="utf-8") as f:
                f.write(final_content)

            print("🔨 重建术语库索引...")
            kb_mod.term_knowledge_base = kb_mod._make_kb(
                Config.TERM_FAISS_PATH, Config.TERM_CHUNK_SIZE
            )
            kb_mod.KB_TYPE_REGISTRY["term"] = (
                kb_mod.term_knowledge_base,
                Config.TERM_FAISS_PATH,
            )

            if kb_mod.term_knowledge_base.exists():
                kb_mod.term_knowledge_base.clear()
                print("🗑️ 已清空原有知识库")

            result = kb_mod.term_knowledge_base.create(
                final_content, metadata={"source": "term_library"}
            )
            print(f"✅ 知识库创建成功，共 {result.get('chunk_count', 0)} 个片段")

            print("📊 生成分段可视化文件...")
            inspect_result = kb_mod.term_knowledge_base.inspect(
                save_to_file=True, output_file="term_chunks.md"
            )

            chunks_file_path = os.path.join(Config.TERM_FAISS_PATH, "term_chunks.md")

            file_info = ""
            if inspect_result["success"]:
                file_info = f"\n\n📄 分段可视化已保存至: `{chunks_file_path}`"
                print(f"✅ 分段可视化已保存: {chunks_file_path}")

            return jsonify(
                {
                    "success": True,
                    "chunk_count": result.get("chunk_count", 0),
                    "message": f"术语库重建成功，共 {result.get('chunk_count', 0)} 个片段{file_info}",
                    "chunks_file": chunks_file_path if inspect_result["success"] else None,
                }
            )

        except Exception as e:
            print(f"❌ 重建术语库失败: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/<kb_type>/inspect", methods=["GET"])
    def inspect_kb(kb_type):
        try:
            if kb_type not in KB_TYPE_REGISTRY:
                return jsonify({"success": False, "error": "未知的知识库类型"}), 400

            kb, path = KB_TYPE_REGISTRY[kb_type]

            if not kb.exists():
                return jsonify({"success": False, "error": f"知识库不存在: {path}"}), 404

            chunks = kb.get_all_chunk_texts()
            return jsonify(
                {
                    "success": True,
                    "chunks": chunks,
                    "count": len(chunks),
                    "path": path,
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/paper/papers", methods=["GET"])
    def get_paper_list():
        try:
            if not paper_knowledge_base.exists():
                return jsonify({"success": True, "papers": []})

            papers = paper_knowledge_base.get_papers()
            return jsonify({"success": True, "papers": papers})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/paper/papers/<paper_id>/chunks", methods=["GET"])
    def get_paper_chunks_api(paper_id):
        try:
            if not paper_knowledge_base.exists():
                return jsonify({"success": False, "error": "知识库不存在"}), 404

            chunks_meta = paper_knowledge_base.get_paper_chunks(paper_id)

            chunks_with_content = []
            for chunk_meta in chunks_meta:
                content = paper_knowledge_base.get_chunk_content(chunk_meta["index"])
                chunks_with_content.append({**chunk_meta, "content": content})

            return jsonify({"success": True, "chunks": chunks_with_content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/paper/chunks/<int:chunk_index>", methods=["PUT"])
    def update_paper_chunk(chunk_index):
        return kb_update_chunk_json(paper_knowledge_base, chunk_index)

    @app.route("/api/kb/paper/chunks/<int:chunk_index>", methods=["DELETE"])
    def delete_paper_chunk(chunk_index):
        return kb_delete_chunk_json(paper_knowledge_base, chunk_index)

    @app.route("/api/kb/paper/papers/<paper_id>", methods=["DELETE"])
    def delete_paper(paper_id):
        try:
            result = paper_knowledge_base.delete_paper(paper_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/paper/papers", methods=["POST"])
    def add_new_paper():
        try:
            data = request.get_json()
            title = data.get("title", "")
            filename = data.get("filename", "")
            chunks = data.get("chunks", [])

            if not title or not chunks:
                return jsonify({"success": False, "error": "标题和片段内容不能为空"}), 400

            metadata = {
                "title": title,
                "filename": filename or title,
                "source": "manual",
            }

            if paper_knowledge_base.exists():
                result = paper_knowledge_base.append("\n\n".join(chunks), metadata)
            else:
                result = paper_knowledge_base.create("\n\n".join(chunks), metadata)

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/paper/papers/<paper_id>/chunks", methods=["POST"])
    def add_chunks_to_paper_api(paper_id):
        try:
            data = request.get_json()
            new_chunks = data.get("chunks", [])

            if not new_chunks:
                return jsonify({"success": False, "error": "片段内容不能为空"}), 400

            result = paper_knowledge_base.add_chunks_to_paper(paper_id, new_chunks)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/background/chunks", methods=["GET"])
    def get_background_chunks():
        try:
            if not background_knowledge_base.exists():
                return jsonify({"success": True, "chunks": []})
            texts = background_knowledge_base.get_all_chunk_texts()
            chunks = [
                {
                    "index": i,
                    "content": text,
                    "preview": text[:100] + "..." if len(text) > 100 else text,
                    "length": len(text),
                }
                for i, text in enumerate(texts)
            ]
            return jsonify({"success": True, "chunks": chunks})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/kb/background/chunks/<int:chunk_index>", methods=["PUT"])
    def update_background_chunk(chunk_index):
        return kb_update_chunk_json(background_knowledge_base, chunk_index)

    @app.route("/api/kb/background/chunks/<int:chunk_index>", methods=["DELETE"])
    def delete_background_chunk(chunk_index):
        return kb_delete_chunk_json(background_knowledge_base, chunk_index)

    @app.route("/api/kb/background/chunks", methods=["POST"])
    def add_background_chunk():
        try:
            data = request.get_json()
            content = data.get("content", "")

            if not content:
                return jsonify({"success": False, "error": "内容不能为空"}), 400

            if background_knowledge_base.exists():
                result = background_knowledge_base.append(content, {"source": "manual"})
            else:
                result = background_knowledge_base.create(content, {"source": "manual"})

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
