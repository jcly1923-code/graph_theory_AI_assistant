# knowledge.py — 术语/论文索引脚本示例（逻辑委托给 knowledge_base.KnowledgeBase，避免与主程序重复实现 FAISS 流程）
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from knowledge_base import KnowledgeBase

INDEX_PATH = os.path.join(_ROOT, "knowledge", "term", "faiss_term")

_kb = KnowledgeBase(
    index_path=INDEX_PATH,
    model_name="all-MiniLM-L6-v2",
    chunk_size=300,
    chunk_overlap=50,
)


def create_paper_kb(paper_text: str):
    """创建全新的知识库（覆盖已有内容）。"""
    result = _kb.create(paper_text)
    if not result.get("success"):
        print("❌", result.get("error", "创建失败"))
    return result


def add_paper_to_kb(paper_text: str):
    """追加到现有知识库；不存在则创建。"""
    if _kb.exists():
        result = _kb.append(paper_text)
    else:
        result = _kb.create(paper_text)
    if not result.get("success"):
        print("❌", result.get("error", "更新失败"))
    return result


def inspect_paper_kb(save_to_file: bool = True):
    """可视化分段（输出到索引目录下的 chunks.md）。"""
    result = _kb.inspect(save_to_file=save_to_file, output_file="chunks.md")
    if not result.get("success"):
        print("❌", result.get("error", "知识库不存在或加载失败"))
    return result


def query_paper_kb(question: str, k: int = 2):
    """从知识库检索相关片段。"""
    return _kb.query(question, k=k)


# ========================
# 模拟数据
# ========================
PAPER_1 = """
📄 **文档分析报告**

**论文标题**：《Expediting Contrastive Language-Image Pretraining via Self-Distilled Encoders》（ECLIPSE）
**作者**：Kim等 (LG AI Research)
**发表时间**：2024年

## 🎯 研究背景与问题

大规模视觉-语言预训练（VLP）面临两大挑战：

1. **数据效率低**：网络爬取的图像-文本对存在严重**弱相关性**，传统CLIP训练需要海量数据
2. **计算成本高**：现有知识蒸馏方案（如ALBEF、COTS）需额外维护图像和文本动量编码器

## 🔧 核心创新：ECLIPSE框架

### 1️⃣ 共享文本编码器蒸馏架构

> **仅使用一个图像动量编码器（教师）**，在线图像编码器（学生）与动量图像编码器**共享同一文本编码器**，并对学生网络应用**停止梯度（stop-gradient）**

✅ **消除额外文本动量编码器**，大幅降低参数量
✅ **统一文本嵌入空间**，蒸馏过程更高效

### 2️⃣ 在线编码器加速策略

> 将**EViT令牌稀疏化技术**应用于学生网络

- **教师网络**：处理**全局视图**（完整图像）
- **学生网络**：处理**局部视图**（稀疏令牌）
- **效果**：形成**互补性交互**，找到性能与速度的最佳平衡点

### 3️⃣ 训练机制

- **教师对齐矩阵 `Ā`**：动量图像编码器 + 文本编码器
- **学生对齐矩阵 `A`**：加速在线编码器 + 停止梯度文本编码器
- **损失函数**：学生匹配教师的软对齐矩阵（KL散度）
- **参数更新**：教师 ← EMA(学生)

## 📊 实验结果

| 配置 | ImageNet零样本 | 推理加速 | 训练效率 |
|------|----------------|----------|----------|
| CLIP ViT-B/16 | 基线 | 1.0× | 基线 |
| **ECLIPSE (加速版)** | **+1.27%** | **+101%** (2.0×) | **提升** |
| **ECLIPSE (全容量)** | **+3.22%** | - | - |

### ✨ 关键发现

- **推理速度翻倍**的同时**准确率提升**，打破"加速必降质"传统认知
- **无需额外调优阶段**，避免FLIP的训练-测试分布不一致问题
- **灵活选择**：想要速度选加速版，想要极致性能选全容量版

## 💡 技术价值

1. **理论创新**：首次证明**共享文本空间蒸馏**可替代双动量编码器
2. **工程价值**：**101%推理加速**对实际部署意义重大
3. **学术启示**：**模型加速**与**性能提升**可兼得，关键在于架构设计

## 📌 总结

ECLIPSE通过**共享文本编码器蒸馏**与**在线编码器加速**的创新组合，在**推理速度翻倍**的同时实现**性能提升**，为高效视觉-语言预训练提供了新范式。该工作发表于2024年，已在多个下游任务上达到SOTA。
"""

PAPER_2 = """
论文标题：《FastVLP: Efficient Vision-Language Pretraining with Sparse Attention》
作者：Zhang et al.
发表时间：2025年

摘要：本文提出 FastVLP，一种基于稀疏注意力的高效 VLP 框架。
通过动态 token 选择机制，在保持 98% 性能的同时减少 60% 的计算量。
实验表明，FastVLP 在 COCO 和 Flickr30K 上均达到 SOTA。
"""


def main():
    # 示例 1：新建知识库（只含 PAPER_1）
    # create_paper_kb(PAPER_1)

    # 示例 2：追加 PAPER_2
    # add_paper_to_kb(PAPER_2)

    # 可视化分段
    # inspect_paper_kb(save_to_file=True)

    # 术语知识库新建
    create_paper_kb(PAPER_1)


if __name__ == "__main__":
    main()
