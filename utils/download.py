# 在任何有网络的地方运行此脚本
from sentence_transformers import SentenceTransformer
import os

# 下载模型到指定目录
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save_pretrained('./local_models/all-MiniLM-L6-v2')

print("✅ 模型已下载到本地: ./local_models/all-MiniLM-L6-v2")