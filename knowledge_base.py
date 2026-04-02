# knowledge_base.py
import os
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from datetime import datetime

class KnowledgeBase:
    """知识库管理类，支持创建、追加、查询和可视化"""
    
    def __init__(self, index_path: str = "./faiss_paper_index", 
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 300,
                 chunk_overlap: int = 50):
        """
        初始化知识库
        
        Args:
            index_path (str): 知识库索引存储路径
            model_name (str): 嵌入模型名称
            chunk_size (int): 文本分块大小
            chunk_overlap (int): 分块重叠大小
        """
        self.index_path = index_path
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = None
        self.vector_store = None
        
    def _initialize_embeddings(self):
        """初始化嵌入模型（使用归一化）"""
        if self.embeddings is None:
            print("🔧 初始化嵌入模型（启用归一化）...")
            # 使用本地模型路径，而不是从网络下载
            local_model_path = os.path.join(os.path.dirname(__file__), "local_models/all-MiniLM-L6-v2")
            # 如果本地模型存在，使用本地路径
            if os.path.exists(local_model_path):
                model_name_or_path = local_model_path
                print(f"📁 使用本地模型: {local_model_path}")
            else:
                # 降级使用在线模型（会触发你遇到的错误）
                model_name_or_path = self.model_name
                print(f"⚠️ 本地模型不存在，尝试从网络下载: {model_name_or_path}")
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name_or_path,
                model_kwargs={"device": "cpu"},  # 可根据需要改为 cuda
                encode_kwargs={"normalize_embeddings": True}
            )
    
    def _split_text(self, text: str) -> List[str]:
        """内部文本分割工具"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
        return text_splitter.split_text(text)
    
    def _ensure_directory(self):
        """确保索引目录存在"""
        os.makedirs(self.index_path, exist_ok=True)
    
    def exists(self) -> bool:
        """检查知识库是否存在"""
        return os.path.exists(os.path.join(self.index_path, "index.faiss"))

    def ensure_loaded(self) -> bool:
        """索引存在时确保 vector_store 已加载。"""
        if not self.exists():
            return False
        if self.vector_store is not None:
            return True
        return self.load()

    def get_all_chunk_texts(self) -> List[str]:
        """按 docstore 顺序返回全部片段文本；不可用则返回空列表。"""
        try:
            if not self.ensure_loaded():
                return []
            docs = list(self.vector_store.docstore._dict.values())
            return [doc.page_content for doc in docs]
        except Exception:
            return []

    def create(self, paper_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建全新的论文知识库（会覆盖已有内容）
        
        Args:
            paper_text (str): 论文原始文本
            metadata (dict): 可选的元数据，如论文标题、作者等
            
        Returns:
            dict: 操作结果信息
        """
        try:
            print("🆕 正在创建新的论文知识库（将覆盖旧内容）...")
            self._initialize_embeddings()
            self._ensure_directory()
            
            # 分割文本
            chunks = self._split_text(paper_text)
            print(f"✅ 文本已分割为 {len(chunks)} 个片段")
            
            # 创建向量存储
            self.vector_store = FAISS.from_texts(chunks, self.embeddings)
            
            # 保存元数据
            if metadata:
                self._save_metadata(metadata, chunks)
            
            # 保存索引
            self.vector_store.save_local(self.index_path)
            print(f"✅ 知识库已保存至 {self.index_path}")
            
            return {
                "success": True,
                "message": f"知识库创建成功，共 {len(chunks)} 个片段",
                "chunk_count": len(chunks),
                "path": self.index_path
            }
        except ValueError as e:
            error_msg = f"创建知识库失败（参数错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except RuntimeError as e:
            error_msg = f"创建知识库失败（运行时错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"创建知识库失败（未知错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def append(self, paper_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        将新论文追加到现有知识库（增量更新）
        
        Args:
            paper_text (str): 新增的论文文本
            metadata (dict): 可选的元数据
            
        Returns:
            dict: 操作结果信息
        """
        try:
            print("📥 正在追加论文到现有知识库...")
            self._initialize_embeddings()
            
            # 分割新文本
            new_chunks = self._split_text(paper_text)
            print(f"✅ 新文本已分割为 {len(new_chunks)} 个片段")
            
            # 检查是否存在旧知识库
            if self.exists():
                print("🔍 检测到已有知识库，正在加载旧内容...")
                self.load()
                
                # 获取旧文本
                old_texts = [doc.page_content for doc in self.vector_store.docstore._dict.values()]
                all_chunks = old_texts + new_chunks
                print(f"📊 合并后共 {len(all_chunks)} 个片段（原 {len(old_texts)} + 新 {len(new_chunks)}）")
            else:
                print("⚠️ 未检测到已有知识库，将创建一个新的。")
                all_chunks = new_chunks
            
            # 重建并保存
            self.vector_store = FAISS.from_texts(all_chunks, self.embeddings)
            self.vector_store.save_local(self.index_path)
            
            # 追加元数据
            if metadata:
                self._append_metadata(metadata, new_chunks)
            
            print(f"✅ 知识库已更新并保存至 {self.index_path}")
            
            return {
                "success": True,
                "message": f"知识库追加成功，当前共 {len(all_chunks)} 个片段",
                "chunk_count": len(all_chunks),
                "new_chunks": len(new_chunks),
                "path": self.index_path
            }
        except ValueError as e:
            error_msg = f"追加知识库失败（参数错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except IOError as e:
            error_msg = f"追加知识库失败（IO错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"追加知识库失败（未知错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def load(self) -> bool:
        """加载现有知识库"""
        try:
            if not self.exists():
                print("❌ 知识库不存在，请先创建！")
                return False
            
            self._initialize_embeddings()
            self.vector_store = FAISS.load_local(
                self.index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"✅ 知识库加载成功")
            return True
        except FileNotFoundError as e:
            print(f"❌ 加载知识库失败（文件不存在）: {e}")
            return False
        except PermissionError as e:
            print(f"❌ 加载知识库失败（权限不足）: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载知识库失败（未知错误）: {e}")
            return False
    
    def query(self, question: str, k: int = 3) -> List[str]:
        """
        从知识库中检索相关片段
        
        Args:
            question (str): 查询问题
            k (int): 返回的片段数量
            
        Returns:
            list: 相关片段列表
        """
        try:
            if not self.ensure_loaded():
                return []
            
            docs = self.vector_store.similarity_search(question, k=k)
            return [doc.page_content for doc in docs]
        except ValueError as e:
            print(f"❌ 查询失败（参数错误）: {e}")
            return []
        except RuntimeError as e:
            print(f"❌ 查询失败（运行时错误）: {e}")
            return []
        except Exception as e:
            print(f"❌ 查询失败（未知错误）: {e}")
            return []
    
    def query_with_scores(self, question: str, k: int = 3, return_normalized: bool = True) -> List[Tuple]:
        """
        从知识库中检索相关片段并返回相似度分数
        
        Args:
            question (str): 查询问题
            k (int): 返回的片段数量
            return_normalized (bool): 是否返回归一化的相似度分数（0-1之间）
            
        Returns:
            list: (片段内容, 相似度分数) 的元组列表
                  如果 return_normalized=True，分数在0-1之间（越大越相似）
                  如果 return_normalized=False，返回原始L2距离（越小越相似）
        """
        try:
            if not self.ensure_loaded():
                return []
            
            # 获取原始结果（返回L2距离）
            docs_with_scores = self.vector_store.similarity_search_with_score(question, k=k)
            
            results = []
            for doc, l2_distance in docs_with_scores:
                # 提取文本内容
                text_content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                
                if return_normalized:
                    # 将L2距离转换为余弦相似度（0-1之间）
                    # 对于归一化向量，余弦相似度 = 1 - (distance / 2)
                    # 注意：l2_distance 已经是平方值
                    cosine_similarity = 1 - (l2_distance / 2)
                    # 确保在0-1范围内（考虑浮点误差）
                    cosine_similarity = max(0.0, min(1.0, cosine_similarity))
                    results.append((text_content, cosine_similarity))
                else:
                    # 返回原始L2距离
                    results.append((text_content, l2_distance))
            
            return results
        except ValueError as e:
            print(f"❌ 带分数查询失败（参数错误）: {e}")
            return []
        except RuntimeError as e:
            print(f"❌ 带分数查询失败（运行时错误）: {e}")
            return []
        except Exception as e:
            print(f"❌ 带分数查询失败（未知错误）: {e}")
            return []
    
    def inspect(self, save_to_file: bool = True, output_file: str = "chunks.md") -> Dict[str, Any]:
        """
        可视化知识库的分段内容
        
        Args:
            save_to_file (bool): 是否保存到文件
            output_file (str): 输出文件名
            
        Returns:
            dict: 分段信息
        """
        try:
            if not self.ensure_loaded():
                return {"success": False, "error": "知识库不存在"}
            
            docs = list(self.vector_store.docstore._dict.values())
            chunk_count = len(docs)
            
            print(f"\n📄 共 {chunk_count} 个分段：\n")
            
            all_content = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content.strip()
                all_content.append(f"# 分段 #{i}\n```\n{content}\n```\n")
            
            if save_to_file:
                with open(os.path.join(self.index_path, output_file), "w", encoding="utf-8") as f:
                    f.write("".join(all_content))
                print(f"\n💾 已保存分段内容到 {os.path.join(self.index_path, output_file)}")
            
            return {
                "success": True,
                "chunk_count": chunk_count,
                "saved_to": os.path.join(self.index_path, output_file) if save_to_file else '未保存'
            }
        except FileNotFoundError as e:
            error_msg = f"检查知识库失败（文件不存在）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except PermissionError as e:
            error_msg = f"检查知识库失败（权限不足）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"检查知识库失败（未知错误）: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            if not self.ensure_loaded():
                return {"exists": False}
            
            docs = list(self.vector_store.docstore._dict.values())
            total_chars = sum(len(doc.page_content) for doc in docs)
            
            return {
                "exists": True,
                "chunk_count": len(docs),
                "total_chars": total_chars,
                "avg_chunk_size": total_chars // len(docs) if docs else 0,
                "path": self.index_path,
                "model": self.model_name,
                "normalized": True  # 标记已启用归一化
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def clear(self) -> bool:
        """清空知识库"""
        try:
            import shutil
            import time
            import glob
            
            # 先释放向量存储的引用，关闭文件句柄
            self.vector_store = None
            self.embeddings = None
            
            # 强制垃圾回收，确保文件句柄被释放
            import gc
            gc.collect()
            time.sleep(0.3)
            
            if os.path.exists(self.index_path):
                # 尝试删除文件夹内的所有文件，而不是删除文件夹本身
                try:
                    # 先尝试删除所有文件
                    for root, dirs, files in os.walk(self.index_path, topdown=False):
                        for name in files:
                            file_path = os.path.join(root, name)
                            try:
                                os.chmod(file_path, 0o777)  # 修改权限
                                os.remove(file_path)
                            except:
                                pass
                        for name in dirs:
                            dir_path = os.path.join(root, name)
                            try:
                                os.rmdir(dir_path)
                            except:
                                pass
                    
                    # 最后删除空文件夹
                    try:
                        os.rmdir(self.index_path)
                    except:
                        pass
                    
                    print(f"🗑️ 已清空知识库: {self.index_path}")
                except Exception as e2:
                    # 如果上面的方法失败，尝试重命名后创建新文件夹
                    backup_path = self.index_path + "_old_" + str(int(time.time()))
                    try:
                        os.rename(self.index_path, backup_path)
                        print(f"🗑️ 知识库已标记为删除（将在重启后清理）: {self.index_path}")
                    except:
                        raise e2
            return True
        except Exception as e:
            print(f"❌ 清空知识库失败: {e}")
            return False
    
    def _save_metadata(self, metadata: Dict, chunks: List[str], paper_id: str = None):
        """保存元数据，支持论文维度的片段追踪"""
        meta_path = os.path.join(self.index_path, "metadata.json")
        import json
        import uuid
        
        # 为每个片段分配ID和所属论文 - 确保paper_id唯一
        if paper_id is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            base_name = metadata.get("filename", "paper")
            paper_id = f"{base_name}_{timestamp}_{unique_id}"
        chunk_entries = []
        for i, chunk in enumerate(chunks):
            chunk_entries.append({
                "id": f"{paper_id}_{i}",
                "paper_id": paper_id,
                "index": i,
                "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                "length": len(chunk)
            })
        
        meta_data = {
            "created_at": datetime.now().isoformat(),
            "papers": [{
                "paper_id": paper_id,
                "metadata": metadata,
                "added_at": datetime.now().isoformat(),
                "chunks": chunk_entries
            }],
            "total_chunks": len(chunks),
            "model": self.model_name,
            "normalized": True
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
    
    def _append_metadata(self, metadata: Dict, new_chunks: List[str]):
        """追加元数据，支持多论文管理"""
        meta_path = os.path.join(self.index_path, "metadata.json")
        import json
        import uuid
        
        # 生成唯一的paper_id，避免重复
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        base_name = metadata.get("filename", "paper")
        paper_id = f"{base_name}_{timestamp}_{unique_id}"
        
        # 构建新片段条目
        new_chunk_entries = []
        start_index = 0
        
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # 计算新论文的起始索引
            for paper in meta_data.get("papers", []):
                start_index += len(paper.get("chunks", []))
            
            meta_data["updated_at"] = datetime.now().isoformat()
            meta_data["total_chunks"] = meta_data.get("total_chunks", 0) + len(new_chunks)
        else:
            meta_data = {
                "created_at": datetime.now().isoformat(),
                "total_chunks": len(new_chunks),
                "model": self.model_name,
                "normalized": True,
                "papers": []
            }
        
        # 创建新片段条目
        for i, chunk in enumerate(new_chunks):
            new_chunk_entries.append({
                "id": f"{paper_id}_{i}",
                "paper_id": paper_id,
                "index": start_index + i,
                "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                "length": len(chunk)
            })
        
        # 添加新论文
        meta_data["papers"].append({
            "paper_id": paper_id,
            "metadata": metadata,
            "added_at": datetime.now().isoformat(),
            "chunks": new_chunk_entries
        })
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
    
    def get_papers(self) -> List[Dict[str, Any]]:
        """获取所有论文列表"""
        try:
            meta_path = os.path.join(self.index_path, "metadata.json")
            if not os.path.exists(meta_path):
                return []
            
            import json
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            papers = []
            for paper in meta_data.get("papers", []):
                papers.append({
                    "paper_id": paper["paper_id"],
                    "title": paper["metadata"].get("title", paper["paper_id"]),
                    "filename": paper["metadata"].get("filename", ""),
                    "added_at": paper["added_at"],
                    "chunk_count": len(paper.get("chunks", []))
                })
            return papers
        except Exception as e:
            print(f"❌ 获取论文列表失败: {e}")
            return []
    
    def get_paper_chunks(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取指定论文的所有片段"""
        try:
            meta_path = os.path.join(self.index_path, "metadata.json")
            if not os.path.exists(meta_path):
                return []
            
            import json
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            for paper in meta_data.get("papers", []):
                if paper["paper_id"] == paper_id:
                    return paper.get("chunks", [])
            return []
        except Exception as e:
            print(f"❌ 获取论文片段失败: {e}")
            return []
    
    def get_chunk_content(self, chunk_index: int) -> Optional[str]:
        """获取指定索引的片段内容"""
        try:
            if not self.vector_store:
                if not self.load():
                    return None
            
            docs = list(self.vector_store.docstore._dict.values())
            if 0 <= chunk_index < len(docs):
                return docs[chunk_index].page_content
            return None
        except Exception as e:
            print(f"❌ 获取片段内容失败: {e}")
            return None
    
    def delete_paper(self, paper_id: str) -> Dict[str, Any]:
        """删除整篇论文及其所有片段"""
        try:
            meta_path = os.path.join(self.index_path, "metadata.json")
            if not os.path.exists(meta_path):
                return {"success": False, "error": "知识库不存在"}
            
            import json
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # 找到要删除的论文
            target_paper = None
            target_index = -1
            for i, paper in enumerate(meta_data.get("papers", [])):
                if paper["paper_id"] == paper_id:
                    target_paper = paper
                    target_index = i
                    break
            
            if not target_paper:
                return {"success": False, "error": f"论文 {paper_id} 不存在"}
            
            # 获取要删除的片段索引集合（用于快速查找）
            indices_to_remove = set(c["index"] for c in target_paper.get("chunks", []))
            
            # 加载所有文档
            if not self.vector_store:
                if not self.load():
                    return {"success": False, "error": "无法加载知识库"}
            
            docs = list(self.vector_store.docstore._dict.values())
            
            # 按顺序保留未删除的文档内容，并记录索引映射
            remaining_texts = []
            index_mapping = {}  # 旧索引 -> 新索引
            new_index = 0
            
            for old_index, doc in enumerate(docs):
                if old_index not in indices_to_remove:
                    remaining_texts.append(doc.page_content)
                    index_mapping[old_index] = new_index
                    new_index += 1
            
            # 重建索引 - 使用from_texts避免文档ID冲突
            if remaining_texts:
                self.vector_store = FAISS.from_texts(remaining_texts, self.embeddings)
                self.vector_store.save_local(self.index_path)
            else:
                # 没有剩余文档，清空知识库
                self.clear()
            
            # 从元数据中移除该论文
            remaining_papers = [p for p in meta_data.get("papers", []) if p["paper_id"] != paper_id]
            
            # 更新所有剩余论文的片段索引
            for paper in remaining_papers:
                for chunk in paper.get("chunks", []):
                    old_idx = chunk["index"]
                    if old_idx in index_mapping:
                        chunk["index"] = index_mapping[old_idx]
                        chunk["id"] = f"{paper['paper_id']}_{chunk['index']}"
            
            # 更新元数据
            meta_data["papers"] = remaining_papers
            meta_data["total_chunks"] = sum(len(p.get("chunks", [])) for p in remaining_papers)
            meta_data["updated_at"] = datetime.now().isoformat()
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"论文 {paper_id} 已删除",
                "deleted_chunks": len(indices_to_remove)
            }
        except Exception as e:
            return {"success": False, "error": f"删除论文失败: {str(e)}"}
    
    def update_chunk(self, chunk_index: int, new_content: str) -> Dict[str, Any]:
        """更新指定索引的片段内容"""
        try:
            if not self.vector_store:
                if not self.load():
                    return {"success": False, "error": "无法加载知识库"}
            
            docs = list(self.vector_store.docstore._dict.values())
            if not (0 <= chunk_index < len(docs)):
                return {"success": False, "error": "片段索引超出范围"}
            
            # 更新文档内容
            docs[chunk_index].page_content = new_content
            
            # 重建索引 - 使用from_texts避免文档ID冲突
            texts = [doc.page_content for doc in docs]
            self.vector_store = FAISS.from_texts(texts, self.embeddings)
            self.vector_store.save_local(self.index_path)
            
            # 更新元数据中的预览
            meta_path = os.path.join(self.index_path, "metadata.json")
            if os.path.exists(meta_path):
                import json
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                for paper in meta_data.get("papers", []):
                    for chunk in paper.get("chunks", []):
                        if chunk["index"] == chunk_index:
                            chunk["preview"] = new_content[:100] + "..." if len(new_content) > 100 else new_content
                            chunk["length"] = len(new_content)
                            break
                
                meta_data["updated_at"] = datetime.now().isoformat()
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": "片段已更新"}
        except Exception as e:
            return {"success": False, "error": f"更新片段失败: {str(e)}"}
    
    def delete_chunk(self, chunk_index: int) -> Dict[str, Any]:
        """删除指定索引的片段"""
        try:
            if not self.vector_store:
                if not self.load():
                    return {"success": False, "error": "无法加载知识库"}
            
            docs = list(self.vector_store.docstore._dict.values())
            if not (0 <= chunk_index < len(docs)):
                return {"success": False, "error": "片段索引超出范围"}
            
            # 移除指定文档
            remaining_texts = [doc.page_content for i, doc in enumerate(docs) if i != chunk_index]
            
            # 重建索引 - 使用from_texts避免文档ID冲突
            if remaining_texts:
                self.vector_store = FAISS.from_texts(remaining_texts, self.embeddings)
                self.vector_store.save_local(self.index_path)
            else:
                self.clear()
            
            # 更新元数据
            meta_path = os.path.join(self.index_path, "metadata.json")
            if os.path.exists(meta_path):
                import json
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                # 找到并移除该片段，更新索引
                for paper in meta_data.get("papers", []):
                    chunks = paper.get("chunks", [])
                    paper["chunks"] = [c for c in chunks if c["index"] != chunk_index]
                
                # 移除空论文
                meta_data["papers"] = [p for p in meta_data["papers"] if p.get("chunks")]
                
                # 重新索引
                new_index = 0
                for paper in meta_data["papers"]:
                    for chunk in paper.get("chunks", []):
                        if chunk["index"] > chunk_index:
                            chunk["index"] -= 1
                        chunk["id"] = f"{chunk.get('paper_id', 'unknown')}_{chunk['index']}"
                        new_index += 1
                
                meta_data["total_chunks"] = new_index
                meta_data["updated_at"] = datetime.now().isoformat()
                
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": "片段已删除"}
        except Exception as e:
            return {"success": False, "error": f"删除片段失败: {str(e)}"}
    
    def add_chunks_to_paper(self, paper_id: str, new_chunks: List[str]) -> Dict[str, Any]:
        """向现有论文添加新片段"""
        try:
            meta_path = os.path.join(self.index_path, "metadata.json")
            if not os.path.exists(meta_path):
                return {"success": False, "error": "知识库不存在"}
            
            import json
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # 找到目标论文
            target_paper = None
            for paper in meta_data.get("papers", []):
                if paper["paper_id"] == paper_id:
                    target_paper = paper
                    break
            
            if not target_paper:
                return {"success": False, "error": f"论文 {paper_id} 不存在"}
            
            # 加载现有文档
            if not self.vector_store:
                if not self.load():
                    return {"success": False, "error": "无法加载知识库"}
            
            docs = list(self.vector_store.docstore._dict.values())
            
            # 计算新片段的起始索引
            start_index = len(docs)
            
            # 合并所有文本并重建索引 - 使用from_texts避免文档ID冲突
            all_texts = [doc.page_content for doc in docs] + new_chunks
            self.vector_store = FAISS.from_texts(all_texts, self.embeddings)
            self.vector_store.save_local(self.index_path)
            
            # 更新元数据
            new_chunk_entries = []
            for i, chunk in enumerate(new_chunks):
                new_chunk_entries.append({
                    "id": f"{paper_id}_{start_index + i}",
                    "paper_id": paper_id,
                    "index": start_index + i,
                    "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "length": len(chunk)
                })
            
            target_paper["chunks"].extend(new_chunk_entries)
            meta_data["total_chunks"] = len(all_texts)
            meta_data["updated_at"] = datetime.now().isoformat()
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"已向论文 {paper_id} 添加 {len(new_chunks)} 个片段",
                "added_chunks": len(new_chunks)
            }
        except Exception as e:
            return {"success": False, "error": f"添加片段失败: {str(e)}"}