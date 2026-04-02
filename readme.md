# 科研工具 —— 基于大模型的学术助理

一个面向科研人员的本地 Web 应用，支持论文解析、知识库管理和学术问答，基于 Flask + OpenAI 兼容接口构建。这个版本只支持图论方向，其余方向也可根据自己的需求进行定制修改。

---

## 项目简介

本项目是一个运行在本地的科研辅助工具，核心能力包括：

- **论文解析**：上传 PDF 论文，由大模型自动提取摘要、背景、方法、结论等关键信息，并存入知识库。
- **背景知识识别**：自动识别段落中的背景知识（含"背景如下"、"已知"等特征词），单独归档到背景知识库。
- **基于知识库的学术问答**：结合已建立的论文知识库和术语知识库，对学术问题给出有据可查的回答。
- **多知识库管理**：支持论文知识库、术语知识库、背景知识库的独立管理和可视化查看。

整体架构采用**主 Agent + 子 Agent** 模式：主 Agent 负责意图识别和任务分发，三类子 Agent（论文解析 / 背景解析 / 专业问答）分别执行具体任务。

---

## 功能概览

| 功能模块 | 说明 |
|---|---|
| PDF 上传与解析 | 支持最大 20MB 的 PDF，使用 PyPDF2 提取文本后由大模型分析 |
| 流式对话 | SSE 流式输出，支持文件上下文 + 普通文本问答 |
| 意图识别 | 正常模式由大模型识别，失败时自动回退规则识别 |
| 向量知识库 | 基于 FAISS + 本地向量模型，支持创建、追加、查询、统计 |
| 术语增强检索 | 检索术语知识库，结果自动拼接到子 Agent 提示词 |
| 历史记录管理 | 保留有限轮次上下文，支持一键清空 |
| 设置面板 | 前端可配置 API Base URL、API Key、模型名、温度等参数 |
| 主题切换 | 支持日间 / 夜间 / 跟随系统三种主题 |
| 测试模式 | 本地模拟数据，不调用外部接口，适合开发调试 |
| 知识库管理页 | 可视化查看分段详情，导出统计，重建术语索引 |

---

## 目录结构

```
科研工具/
├── app.py                 # Flask 入口，注册路由
├── knowledge_base.py      # 向量知识库核心逻辑
├── requirements.txt       # Python 依赖
├── List.md                # 功能清单（开发进度追踪）
├── knowledge/             # 知识库数据目录
│   └── paper/origin_paper # 论文解析结果（Markdown 格式）
├── local_models/          # 本地向量嵌入模型（不随仓库提供，见下方「下载模型」）
├── static/                # 前端静态资源（JS / CSS）
├── templates/             # HTML 模板（首页 + 知识库管理页）
├── utils/                 # 工具模块
│   └── download.py        # 本地嵌入模型下载脚本
├── web/                   # Flask 路由与业务逻辑
│   ├── routes.py          # 路由注册
│   └── knowledge_bases.py # 知识库初始化
└── test/                  # 测试数据与脚本
```

---

## 快速开始

### 1. 安装依赖

建议使用 Python 3.10+ 并在虚拟环境中安装：

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 下载本地嵌入模型（首次使用 / 克隆仓库后必做）

本仓库**不包含** `local_models/` 中的权重文件（避免仓库体积过大）。向量知识库依赖本地嵌入模型，**首次使用或新克隆后**请在项目根目录执行：

```bash
python utils/download.py
```

模型将保存到 `local_models/all-MiniLM-L6-v2/`，后续无需重复下载。打包为 exe 前也需先完成此步骤（见「Windows 打包」）。

### 3. 配置 API

启动应用后，在前端**设置面板**（右上角齿轮图标）中填写：

| 参数 | 说明 |
|---|---|
| API Base URL | OpenAI 兼容接口地址，例如 `https://api.openai.com/v1` |
| API Key | 对应服务的 API 密钥 |
| 模型名称 | 例如 `gpt-4o`、`deepseek-v3`、`qwen-plus` 等 |
| 温度 | 生成多样性，0~1，学术场景建议 0.3~0.5 |

设置会自动保存到浏览器本地存储，刷新后不丢失。

> 本工具兼容所有支持 OpenAI 接口格式的服务商，包括 OpenAI、阿里云百炼、DeepSeek、Moonshot 等。

### 4. 启动应用

```bash
python app.py
```

启动后在终端查看提示地址（默认 `http://localhost:5000`），浏览器打开即可使用。

---

## Windows 打包（PyInstaller）

在 **Windows** 上可将本应用打成**单文件可执行程序**，便于分发。脚本与配置以仓库内 `pack.bat`、`app.spec` 为准。

### 前置条件

1. 已安装 **Python 3.10+**，并能在命令行使用 `python`。
2. 已执行上文 **「安装依赖」**，并完成 **`python utils/download.py`**，使 `local_models/all-MiniLM-L6-v2/` 存在（打包时会一并打入 exe，否则向量功能不可用）。
3. 额外安装打包工具（未写入 `requirements.txt`，需单独安装）：

   ```bat
   pip install pyinstaller
   ```

### 方式一：一键脚本（推荐）

在项目根目录（与 `pack.bat` 同级）双击运行 **`pack.bat`**，或在 **cmd** 中执行：

```bat
pack.bat
```

脚本会检测是否存在 `pyinstaller` 命令；若无，则自动使用 `python -m PyInstaller`。成功后在 **`dist\`** 下生成 **`app.exe`**（名称以 `app.spec` 中 `name=` 为准）。

### 方式二：手动命令

与 `pack.bat` 等价的核心命令如下（在项目根目录执行）：

```bat
python -m PyInstaller -F --add-data "templates;templates" --add-data "static;static" --add-data "local_models;local_models" --hidden-import=flask --clean app.py
```

更完整的隐藏导入与数据路径见根目录 **`app.spec`**；需要定制打包行为时可先 **`pyinstaller app.spec`** 再按需修改 spec。

### 打包后说明

- 运行 exe 时，程序会在**可执行文件所在目录**查找 `templates`、`static` 及运行时生成的 `knowledge/` 等（与 `app.py` 中 frozen 逻辑一致）。
- 若杀毒软件误报，可自行添加信任或改用源码运行 `python app.py`。

---

## 主要页面说明

### 首页（对话页）

- **左上角**：显示当前运行模式（正常模式 / 测试模式）
- **文件上传区**：点击或拖拽上传 PDF，上传后自动填充解析提问模板
- **对话区**：支持 Markdown 渲染，有示例问题快捷按钮
- **清空历史**：清除当前对话上下文，从头开始

### 知识库管理页（`/knowledge_base`）

- 查看论文、术语、背景三类知识库的统计信息
- 查看各知识库的分段详情
- 导出论文 / 背景统计报告
- 加载、编辑、重建术语索引

---

## 技术栈

| 层次 | 技术 |
|---|---|
| 后端框架 | Flask 3.0 |
| 大模型接口 | OpenAI Python SDK（兼容任意 OpenAI 格式接口） |
| 向量检索 | FAISS + sentence-transformers（本地嵌入） |
| PDF 解析 | PyPDF2 |
| 知识库编排 | LangChain |
| 前端渲染 | 原生 JS + Marked.js + DOMPurify |

---

## 开发模式

在设置面板开启**测试模式**后，所有大模型调用将返回本地模拟数据，不消耗 API 额度，适合功能调试和前端开发。

---

## 代码统计（截至 2026-03-14）

| 目录 / 文件 | 总行数 | 纯代码 | 注释 | 空行 |
|---|---|---|---|---|
| static/ | 3297 | 2631 | 214 | 452 |
| templates/ | 362 | 333 | 7 | 22 |
| utils/ | 362 | 320 | 16 | 26 |
| app.py | 1308 | 942 | 307 | 59 |
| knowledge_base.py | 414 | 279 | 92 | 43 |
| **合计** | **5743** | **4505** | **636** | **602** |

---

## 注意事项

- API Key 请仅在前端设置面板中配置，保存于本地浏览器，**不要硬编码到代码或配置文件中**。
- **`knowledge/`**：个人知识库数据，已在 `.gitignore` 中忽略；公开推送前请确认未使用 `git add -f` 强行纳入历史。
- **`local_models/`**：嵌入模型权重，已在 `.gitignore` 中忽略；协作者与使用者需自行执行 `python utils/download.py`。若你曾经把该目录提交进 Git，**历史里仍可能保留大文件**，公开前可用 `git filter-repo` 等工具清理（进阶操作）。
- **`.venv/`**：虚拟环境目录已在 `.gitignore` 中排除。
