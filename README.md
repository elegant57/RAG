# RAG 智能客服

基于 Streamlit、LangChain、Chroma 和通义模型的知识库问答项目。上传 TXT 资料后，系统将文本转换为向量并保存到本地；用户提问时，先检索相关资料，再结合对话历史生成流式回答。

项目提供两个独立的 Web 页面：**知识库更新服务**和**智能客服**。`data/` 中附带尺码推荐、洗涤养护、颜色选择等示例资料，可用于体验服装客服场景。

## 功能

- **知识库上传**：每次上传一个 UTF-8 编码的 TXT 文件。
- **文本切分**：较长文本按段落、标点等分隔符切分，保留相邻片段的重叠内容。
- **重复内容检查**：通过文本内容的 MD5 避免重复入库，文件名不同但内容相同也会跳过。
- **向量检索**：从 Chroma 检索与当前问题相似的文本片段。
- **流式问答**：结合检索资料与历史消息，逐步显示模型回答。
- **会话持久化**：将对话消息以 JSON 格式保存到本地文件。
- **知识库维护**：提供按文件名、向量 ID 删除数据，以及删除集合的 Python 接口，并同步清理不再使用的 MD5 记录；这些接口尚未接入页面。

## 工作流程

```text
上传 TXT → UTF-8 解码 → MD5 去重 → 按长度切分 → 文本向量化 → Chroma 本地存储

用户提问 → 相似文本检索 → 组合参考资料与对话历史 → 通义模型 → 流式回答
                                                            ↓
                                                     本地保存对话消息
```

## 项目结构

```text
P4_RAG_program/
├── app_file_uploader.py    # 知识库上传页面
├── app_qa.py               # 智能客服问答页面
├── config_data.py          # 模型、路径、切分、检索和会话配置
├── knowledge_base.py       # 文本入库、MD5 去重与数据删除
├── vector_store.py         # Chroma 向量库与检索器封装
├── rag.py                  # 提示词、检索链、模型调用与历史消息组合
├── file_history_store.py   # 基于本地文件的会话历史存储
├── data/                  # 示例 TXT 资料
│   ├── 尺码推荐.txt
│   ├── 洗涤养护.txt
│   └── 颜色选择.txt
├── chroma_db/             # 本地向量数据库
├── chat_history/          # 本地会话历史
├── md5.txt                # 已入库文本的 MD5 记录
└── README.md
```

## 安装与配置

以下命令在项目根目录执行。需要 Python 环境，以及能够调用所配置模型的 DashScope API Key。项目暂未提供依赖锁定文件，下面的依赖清单根据源码导入整理，未验证特定版本组合。

### 1. 创建环境并安装依赖

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install streamlit langchain-core langchain-community langchain-chroma langchain-text-splitters dashscope
```

Linux / macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install streamlit langchain-core langchain-community langchain-chroma langchain-text-splitters dashscope
```

后续 PowerShell 命令使用虚拟环境中的 Python；Linux / macOS 在激活环境后将其替换为 `python` 即可。

### 2. 配置 API Key

Windows PowerShell：

```powershell
$env:DASHSCOPE_API_KEY = "替换为你的 DashScope API Key"
```

Linux / macOS：

```bash
export DASHSCOPE_API_KEY="替换为你的 DashScope API Key"
```

环境变量需要在启动页面的终端中设置。若使用两个终端分别启动服务，请在两个终端中分别设置。当前代码没有加载 `.env` 文件的逻辑。

文本向量化和回答生成会调用远程模型服务，因此运行时需要网络连接，并会向模型服务发送待向量化文本，以及回答所需的问题、参考资料和历史消息。

### 3. 修改本地存储路径

源码中的存储位置当前为固定的 Linux 绝对路径。在其他位置运行前，需要修改两处。

在 `config_data.py` 中增加项目根目录定义，并替换原有的 `md5_path`、`persist_directory`：

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
md5_path = str(BASE_DIR / "md5.txt")
persist_directory = str(BASE_DIR / "chroma_db")
```

在 `file_history_store.py` 中增加 `Path` 导入，并将原有 `get_history` 函数替换为：

```python
from pathlib import Path

def get_history(session_id):
    session_path = str(Path(__file__).resolve().parent / "chat_history")
    return FileChatMessageHistory(session_id, session_path)
```

上传页与问答页必须使用相同的数据库路径和集合名称，才能访问同一份知识库。

### 4. 检查模型与检索配置

`config_data.py` 中的主要配置如下：

| 配置项 | 源码当前值 | 含义 |
| --- | --- | --- |
| `collection_name` | `RAG` | Chroma 集合名称 |
| `embedding_model_name` | `text-embedding-v4` | 问答检索使用的向量模型 |
| `chat_model_name` | `qwen3.7-max` | 回答生成使用的模型标识 |
| `chunk_size` | `1000` | 触发切分后，每个片段的目标最大字符数 |
| `chunk_overlap` | `100` | 相邻片段重叠字符数 |
| `max_split_char_number` | `1500`（`chunk_size * 1.5`） | 文本长度超过此值才进行切分 |
| `similarity_threshold` | `2` | 检索返回的片段数量 `k`，并非相似度分数阈值 |
| `session_config` 中的 `session_id` | `user001` | 历史消息对应的会话标识 |

模型名称是源码现有配置，使用前需确认对应模型在你的服务账号及接入区域可用；如不可用，请修改为账号支持的模型标识。

**向量模型需保持一致**：`knowledge_base.py` 的入库模型目前直接写为 `text-embedding-v4`，没有读取 `embedding_model_name`。如需更换向量模型，必须同时修改入库与检索两处，并使用新模型重新构建知识库。

## 启动与使用

### 1. 启动知识库上传页

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_file_uploader.py --server.port 8501
```

打开 [知识库上传页](http://localhost:8501)，选择 `data/` 中的 TXT 文件，或上传自己的 UTF-8 TXT 资料。页面显示“【成功】内容已经成功载入向量库”后，即完成入库。重复内容会显示“【跳过】内容已经存在知识库中”。

上传每个文件都会调用向量模型；`data/` 目录中的资料不会自动导入，需要逐个上传。

### 2. 启动问答页

在另一个已设置 API Key 的终端中执行：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_qa.py --server.port 8502
```

打开 [智能客服问答页](http://localhost:8502)，输入与已上传资料相关的问题，例如：

```text
如何选择合适的尺码？
这类衣物应该如何洗涤和保养？
选择衣服颜色时有什么建议？
```

问题应与实际资料内容对应。系统会检索参考片段，再生成回答。

## 数据与会话说明

- `chroma_db/` 保存向量数据，`md5.txt` 保存入库去重记录，迁移或备份知识库时应一起处理。
- `chat_history/` 按会话 ID 保存消息，默认文件名为 `user001`，文件内容是 JSON，文件名没有 `.json` 后缀。
- 默认所有访问者使用固定会话 ID `user001`，会共用同一份后端历史；当前实现没有用户登录和会话隔离机制。
- 页面上的消息列表保存在 Streamlit 会话状态中；新建页面会话时，界面不会自动回显磁盘上的旧消息，但后端仍会按会话 ID 读取历史用于回答。
- 修改同名 TXT 的内容后重新上传，会追加新向量，旧内容不会自动替换；需要替换时可通过维护接口先删除原文件的数据。
- 提示词要求优先参考资料，但代码没有强制拒答或核验回答的机制，也没有在问答页面单独展示引用来源。

## 常见问题

**启动时提示找不到模块**

确认使用安装依赖时的同一个 Python 环境启动 Streamlit。Windows 可直接使用上文的 `.\.venv\Scripts\python.exe -m streamlit` 命令。

**提示路径不存在，或数据保存到了意外位置**

检查 `config_data.py` 中的两个路径，以及 `file_history_store.py` 中的历史目录，确保已按本机位置修改。

**模型调用失败**

检查启动终端中的 `DASHSCOPE_API_KEY`、网络连接、模型访问权限、模型名称和服务额度。具体错误可查看终端输出。

**TXT 上传出现 `UnicodeDecodeError`**

上传页固定使用 UTF-8 解码。请先将文件另存为 UTF-8 编码后再上传。

**删除向量库后，重新上传却提示内容已存在**

去重依据是独立的 `md5.txt` 文件。只删除数据库会留下旧的去重记录；重新构建知识库时，需要同步处理对应的 MD5 记录。

**问答没有使用预期资料**

检查文件是否已成功上传、两个页面是否连接同一数据库和集合，以及向量模型是否一致。当前只检索两个片段，可通过 `similarity_threshold` 调整返回数量。检索仅使用当前问题，历史消息会在之后加入生成提示词，依赖上下文的简短追问可能影响检索效果。

## 当前实现边界

本项目适合学习 RAG 流程和进行本地演示。目前仅支持 TXT，没有 PDF、Word、批量上传、自动扫描目录或网页抓取入口；暂未提供依赖版本锁定文件、自动化测试和多用户服务配置。

`rag.py` 会在终端输出组合后的提示词，包含本次参考资料及对话历史。`knowledge_base.py` 的直接运行入口会写入一条测试数据，因此常规使用应通过上传页导入资料。
