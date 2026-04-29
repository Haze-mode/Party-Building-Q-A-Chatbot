  # GLM-4 党建知识智能问答系统

  基于 GLM-4-9B-Chat 大语言模型的 RAG（检索增强生成）问答系统，支持 TF-IDF 知识库检索、多轮对话、用户认证和 LRU 缓存。

  ## 项目组成

  | 目录 | 说明 |
  |------|------|
  | `demo/` | Tornado 后端服务 —— RAG 引擎、知识库检索、缓存、认证、REST API |
  | `chatbot_html-master/` | 前端界面 —— 聊天页、登录页、知识库管理后台 |
  | `archive1/finetune_demo/` | 模型微调管线 —— LoRA 训练脚本、数据集构建、评估代码 |

  ## 技术栈

  以下均从 `requirements.txt`、`config.py`、`web_server.py` 及各模块 `import` 语句中提取：

  | 类别 | 库 | 版本（requirements.txt） | 用途 |
  |------|---|-------------------------|------|
  | Web 框架 | tornado | ≥6.3 | 异步 HTTP 服务 (`web_server.py`) |
  | 深度学习 | torch | ==2.5.1 | 模型推理 (`model_loader.py`) |
  | | transformers | ==4.46.2 | 模型加载与生成 (`chat_engine.py`) |
  | | peft | ==0.13.2 | LoRA adapter 加载 (`model_loader.py`) |
  | | accelerate | ==1.1.1 | 分布式推理加速 |
  | 检索 | scikit-learn | ≥1.5.0 | TfidfVectorizer (`knowledge_base.py:303`) |
  | 文档处理 | langchain | ≥0.3.0 | 文档加载与分割 (`knowledge_base.py:20-21`) |
  | | langchain-community | ≥0.3.0 | TextLoader/PyPDFLoader/Docx2txtLoader |
  | | pypdf | ≥5.0.0 | PDF 解析 |
  | | docx2txt | ≥0.8 | Word 文档解析 |
  | 认证 | hashlib, uuid | 标准库 | SHA256 密码哈希 + UUID Token (`auth.py`) |
  | 工具 | python-dotenv | ≥1.0.0 | `.env` 环境变量加载 |

  ## 快速开始

  ### 安装依赖

  ```bash
  cd demo
  pip install -r requirements.txt

  配置环境变量

  编辑 demo/.env（或通过 shell 环境变量设置）：

  MODEL_PATH=/root/models/glm-4-9b-chat   # 基座模型路径（Mock 模式下不需要）
  KB_DIR=./data/示例知识库                  # 知识库文档目录
  USE_MOCK=false                           # 设为 true 启用 Mock 调试模式
  WEB_PORT=6006                            # HTTP 服务端口
  LOG_LEVEL=INFO                           # 日志级别

  启动服务

  Mock 模式（无需 GPU，本地调试）：
  # Windows
  start_mock.bat

  # Linux/Mac
  ./start_mock.sh

  真实模型模式：
  cd src
  python web_server.py

  访问 http://localhost:6006

  默认账号：
  - 管理员：admin / admin123
  - 普通用户：user / user123

  微调模型训练

  cd archive1/finetune_demo
  pip install -r requirements.txt
  python finetune.py data/ /root/autodl-tmp/glm-4-9b-chat configs/lora1.yaml

  训练配置见 configs/lora1.yaml：LoRA rank=16，最大步数 800，学习率 5e-5，有效批次 8（2×4 梯度累积），每 200
  步保存检查点。

  项目结构

  demo/
  ├── src/
  │   ├── web_server.py      # Tornado 服务入口，组件初始化与中间件注入
  │   ├── api_handlers.py    # 11 个 HTTP Handler（登录/聊天/会话/知识库 CRUD）
  │   ├── chat_engine.py     # RAG 引擎：检索增强 + 多轮对话 + 缓存集成
  │   ├── knowledge_base.py  # 知识库：文档加载/TF-IDF 索引/FAISS（可选）
  │   ├── cache.py           # LRU 缓存：问答缓存(500)/检索缓存(1000)/会话缓存(2000)
  │   ├── auth.py            # 用户认证：SHA256 密码/UUID Token/角色鉴权装饰器
  │   ├── config.py          # 集中配置：dataclass + 环境变量覆盖
  │   ├── model_loader.py    # 模型加载器：AutoModel/AutoPeftModel + FP16
  │   ├── mock_model.py      # Mock 模型：本地无 GPU 调试
  │   └── __init__.py
  ├── data/示例知识库/        # 知识库文档（TXT/PDF/DOCX）
  ├── tests/                 # 测试脚本
  ├── .env                   # 环境变量
  └── requirements.txt       # Python 依赖

  API 接口

  所有接口均在 api_handlers.py:create_handlers() 中注册：

  ┌──────────────────────┬──────────┬─────────────────────────────────────────────────────────────────┬─────────────┐
  │         接口         │   方法   │                              功能                               │    权限     │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/login           │ POST     │ 用户登录，返回 Token                                            │ 公开        │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/logout          │ POST     │ 用户登出                                                        │ Bearer      │
  │                      │          │                                                                 │ Token       │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/chatbot         │ GET/POST │ 智能问答（参数 infos, session_id, top_p, temperature,           │ 公开        │
  │                      │          │ max_new_tokens）                                                │             │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/session/history │ GET      │ 获取会话对话历史                                                │ 公开        │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/session/clear   │ GET      │ 清空会话历史                                                    │ 公开        │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/session/list    │ GET      │ 列出所有活跃会话 ID                                             │ 公开        │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/kb/files        │ GET      │ 知识库文件列表                                                  │ 管理员      │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/kb/upload       │ POST     │ 上传文件（字段名 file 或 files）                                │ 管理员      │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/kb/reload       │ GET/POST │ 重载知识库索引                                                  │ 管理员      │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/kb/files/delete │ POST     │ 通过请求体删除文件                                              │ 管理员      │
  ├──────────────────────┼──────────┼─────────────────────────────────────────────────────────────────┼─────────────┤
  │ /api/kb/files/(.+)   │ DELETE   │ 通过 URL 删除文件                                               │ 管理员      │
  └──────────────────────┴──────────┴─────────────────────────────────────────────────────────────────┴─────────────┘

  请求/响应示例

  # 登录
  curl -X POST http://localhost:6006/api/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}'

  # 问答
  curl -X POST http://localhost:6006/api/chatbot \
    -H "Content-Type: application/json" \
    -d '{"infos":"什么是三会一课？","session_id":"default"}'

  # 知识库上传（需管理员 Token）
  curl -X POST http://localhost:6006/api/kb/upload \
    -H "Authorization: Bearer <token>" \
    -F "file=@document.pdf"

  核心模块说明

  1. 知识库检索 (knowledge_base.py)

  - 文档加载：load_documents() 遍历目录，按扩展名选择 Loader（TextLoader/PyPDFLoader/Docx2txtLoader），调用
  RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 分割
  - 检索算法：优先尝试 FAISS (KnowledgeBaseFAISS)，HAS_FAISS=False 时回退到 scikit-learn TfidfVectorizer（即
  KnowledgeBaseTFIDF）
  - 检索参数：Top-K 默认 3（config.py:RetrievalConfig.k）

  2. 缓存系统 (cache.py)

  ┌─────────────────┬──────┬───────────────┬────────────────────────────────────┐
  │    缓存实例     │ 容量 │      TTL      │                用途                │
  ├─────────────────┼──────┼───────────────┼────────────────────────────────────┤
  │ answer_cache    │ 500  │ 1800s (30min) │ 问答结果缓存，key = MD5(问题+参数) │
  ├─────────────────┼──────┼───────────────┼────────────────────────────────────┤
  │ retrieval_cache │ 1000 │ 3600s (1h)    │ 检索结果缓存                       │
  ├─────────────────┼──────┼───────────────┼────────────────────────────────────┤
  │ session_cache   │ 2000 │ 7200s (2h)    │ 用户会话缓存                       │
  └─────────────────┴──────┴───────────────┴────────────────────────────────────┘

  - 实现：OrderedDict + MD5 哈希键 + TTL 过期
  - 淘汰策略：容量满时淘汰最久未使用条目（LRU）
  - 清理：PeriodicCallback 每 300 秒清理过期项；知识库更新时全量清空

  3. 会话管理 (chat_engine.py:SessionData)

  - 每会话最多保留 10 轮历史（config.py:SessionConfig.max_history_length）
  - 超时时间：3600 秒（config.py:SessionConfig.timeout）
  - 清理间隔：3600000 毫秒（config.py:SessionConfig.cleanup_interval）

  4. 文本生成 (chat_engine.py:_generate_text)

  - 使用 GLM-4 对话模板：<|system|>, <|user|>, <|assistant|> 格式
  - 同步模式：TextIteratorStreamer 流式生成，但最后 thread.join() 等待完成后以完整 JSON 返回（非 SSE 实时流式）
  - 默认参数：max_new_tokens=512（硬编码），temperature=0.8，top_p=0.9，repetition_penalty=1.1
  - 可通过请求参数覆盖 max_new_tokens、top_p、temperature

  5. 模型微调 (finetune.py + lora1.yaml)

  - 基座模型：GLM-4-9B-Chat
  - 微调方法：LoRA，rank=16，alpha=32，dropout=0.05
  - 目标模块：query_key_value，dense
  - 训练步数：800，有效批次 8，学习率 5e-5（warmup_ratio=0.1，cosine 衰减）
  - 评估指标：Jieba 分词后计算 ROUGE-1/2/L + BLEU-4（finetune.py:compute_metrics）
  - 最终选用：checkpoint-600

  微调训练指标

  数据来源：output/checkpoint-{step}/trainer_state.json 的 log_history 字段

  ┌──────────┬───────────┬─────────┬─────────┬─────────┬──────────┐
  │ 训练步数 │ 训练 Loss │ ROUGE-1 │ ROUGE-2 │ ROUGE-L │  BLEU-4  │
  ├──────────┼───────────┼─────────┼─────────┼─────────┼──────────┤
  │ 200      │ 0.1910    │ 2.97    │ 0.00    │ 0.63    │ 0.00053  │
  ├──────────┼───────────┼─────────┼─────────┼─────────┼──────────┤
  │ 400      │ 0.0085    │ 4.39    │ 1.56    │ 1.32    │ 0.00131  │
  ├──────────┼───────────┼─────────┼─────────┼─────────┼──────────┤
  │ 600      │ 0.0035    │ 4.42    │ 1.40    │ 1.34    │ 0.00112  │
  ├──────────┼───────────┼─────────┼─────────┼─────────┼──────────┤
  │ 800      │ 0.0033    │ 0.078   │ 0.030   │ 0.022   │ 0.000016 │
  └──────────┴───────────┴─────────┴─────────┴─────────┴──────────┘

  800 步时验证集指标全面崩跌（ROUGE-1 从 4.42 骤降至 0.078），训练 Loss 趋近于零，呈现典型小样本过拟合。lora1.yaml 设置
  load_best_model_at_end: true，metric_for_best_model: eval_rouge-l，自动选取 checkpoint-600 为最优模型。

  微调测试集评估

  数据来源：test_eval.json（5 条测试样本，使用 checkpoint-1000 评估）

  ┌────────────────────────────┬─────────┬─────────┬─────────┬────────┐
  │            模型            │ ROUGE-1 │ ROUGE-2 │ ROUGE-L │ BLEU-4 │
  ├────────────────────────────┼─────────┼─────────┼─────────┼────────┤
  │ 基座模型 (GLM-4-9B-Chat)   │ 0.175   │ 0.123   │ 0.149   │ 0.062  │
  ├────────────────────────────┼─────────┼─────────┼─────────┼────────┤
  │ 微调模型 (checkpoint-1000) │ 1.0     │ 1.0     │ 1.0     │ 1.0    │
  └────────────────────────────┴─────────┴─────────┴─────────┴────────┘

  ▎ 微调模型指标异常高（均为 1.0），查看 test_eval.json 细节后发现微调模型对 5
  ▎ 条测试样本完全逐字复现了参考答案，而该测试集与训练集存在严重数据泄漏（check_data_leak.py
  ▎ 脚本存在但未阻止此问题），此指标不能反映真实泛化能力。

  已知局限

  1. FAISS 检索未启用：knowledge_base.py 已实现 KnowledgeBaseFAISS 类（L2 距离 +
  paraphrase-multilingual-MiniLM-L12-v2），但因运行环境缺少 faiss-cpu/faiss-gpu 编译依赖，HAS_FAISS=False，线上回退到
  TF-IDF 关键词匹配（KnowledgeBaseTFIDF）
  2. 未做 Docker 容器化：项目在 AutoDL 云服务器上直接运行，无 Dockerfile 或容器编排配置
  3. 同步推理模式：chat_engine.py:_generate_text() 使用 TextIteratorStreamer 但最后 thread.join() 等待完整生成后以 JSON
  返回，前端非逐 token 实时流式渲染
  4. 小样本过拟合：数百条训练数据训练 800 步，验证集 ROUGE 指标在 600 步后崩跌；测试集存在数据泄漏，BLEU-4/ROUGE
  定量指标不可信
  5. 并发未压测：web_server.py 使用 Tornado 单进程异步模型，未进行严格并发压力测试，论文中"支持 15 并发"为估算值
  6. BLEU-4 自动评估分数极低：验证集 BLEU-4 < 0.002（trainer_state.json），模型效果以人工定性评估为主
  7. 缓存全量清空：知识库更新时 retrieval_cache.clear() + answer_cache.clear() 全量清空，不支持细粒度失效
  8. 知识库覆盖有限：当前仅包含一份党建知识文档（data/示例知识库/党建知识库（完整版）.docx）