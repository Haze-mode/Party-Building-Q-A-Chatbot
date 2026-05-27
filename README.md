## 许可说明
本项目代码仅用于**个人学习、招聘能力评估**场景的阅读参考。
**不授予任何商业使用、修改、分发的权利。**
详见 [LICENSE](./LICENSE) 文件。

# 党建知识智能问答系统 🎯

基于 GLM-4-9B-Chat 大语言模型的 RAG（检索增强生成）问答系统，专为党建知识查询设计。这是一个完整的毕业设计项目，包含后端服务、前端界面和模型微调功能。

## ✨ 项目亮点

- 🤖 **智能问答**：基于 GLM-4-9B-Chat 大语言模型
- 🔍 **RAG 检索**：TF-IDF 知识库检索，支持文档扩展
- 💬 **多轮对话**：完整的会话管理和上下文理解
- 🔐 **用户认证**：基于 Token 的身份验证系统
- ⚡ **性能优化**：LRU 缓存机制，提升响应速度
- 📁 **知识库管理**：支持 TXT/PDF/DOCX 多种格式
- 🎨 **友好界面**：现代化的 Web 聊天界面

## 📂 项目结构

```
Party Building Q&A Chatbot/
├── demo/                      # 后端服务（核心）
│   ├── src/                   # Python 源代码
│   │   ├── web_server.py      # Tornado 服务入口
│   │   ├── api_handlers.py    # API 接口处理
│   │   ├── chat_engine.py     # RAG 问答引擎
│   │   ├── knowledge_base.py  # 知识库管理
│   │   ├── cache.py           # LRU 缓存系统
│   │   ├── auth.py            # 用户认证
│   │   └── ...
│   ├── data/示例知识库/        # 党建知识文档
│   ├── tests/                 # 测试脚本
│   └── README.md              # 详细技术文档
│
├── chatbot_html-master/       # 前端界面
│   ├── index.html             # 聊天主页面
│   ├── login.html             # 登录页面
│   ├── kb_manager.html        # 知识库管理后台
│   └── chatJs/, chatCss/      # 前端资源
│
├── archive1/finetune_demo/    # 模型微调（可选）
│   ├── finetune.py            # LoRA 微调脚本
│   ├── configs/               # 训练配置
│   ├── data/                  # 训练数据集
│   └── README.md              # 微调说明
│
├── .gitignore                 # Git 忽略配置
└── README.md                  # 本文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyTorch 2.5.1+
- 推荐：GPU（用于真实模型推理），或使用 Mock 模式

### 安装步骤

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd Party-Building-Q-A-Chatbot

# 2. 安装依赖
cd demo
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置模型路径等配置

# 4. 启动服务（Mock 模式，无需 GPU）
./start_mock.sh          # Linux/Mac
start_mock.bat           # Windows

# 5. 访问应用
# 浏览器打开: http://localhost:6006
```

### 默认账号

- **管理员**：admin / admin123
- **普通用户**：user / user123

## 📖 详细文档

- [后端服务详细说明](demo/README.md)
- [API 接口文档](demo/docs/API_REFERENCE.md)
- [AutoDL 部署指南](demo/docs/AUTODL_DEPLOYMENT.md)
- [Mock 模式使用](demo/docs/MOCK_MODE_GUIDE.md)
- [模型微调教程](archive1/finetune_demo/README.md)

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端框架** | Tornado (异步 HTTP) |
| **深度学习** | PyTorch, Transformers, PEFT |
| **检索算法** | scikit-learn (TF-IDF), FAISS (可选) |
| **文档处理** | LangChain, pypdf, docx2txt |
| **前端技术** | HTML5, CSS3, JavaScript, jQuery |
| **认证系统** | SHA256 + UUID Token |

## 📊 项目特色功能

### 1. RAG 检索增强生成
- 自动从党建知识库检索相关文档
- 结合大模型生成准确回答
- 支持引用来源追溯

### 2. 智能缓存系统
- 问答结果缓存（500 条，30分钟）
- 检索结果缓存（1000 条，1小时）
- 会话状态缓存（2000 条，2小时）

### 3. 知识库管理
- 支持上传 TXT/PDF/DOCX 文档
- 自动文档分割和索引构建
- 实时重载知识库

### 4. 模型微调支持
- LoRA 高效微调
- 自定义党建知识数据集
- 自动化评估指标（ROUGE, BLEU）

## ⚠️ 注意事项

1. **模型文件**：GLM-4-9B 模型较大（约 18GB），需单独下载，未包含在仓库中
2. **FAISS 支持**：当前默认使用 TF-IDF，如需 FAISS 需安装 `faiss-cpu` 或 `faiss-gpu`
3. **GPU 要求**：真实模型推理需要 GPU，本地调试可使用 Mock 模式
4. **数据隐私**：请确保知识库文档不包含敏感信息

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

本项目为毕业设计作品，展示了 RAG 技术在垂直领域的应用实践。

## 🙏 致谢

- [THUDM/GLM-4](https://github.com/THUDM/GLM-4) - 基础大语言模型
- [LangChain](https://github.com/langchain-ai/langchain) - 文档处理框架
- [Hugging Face Transformers](https://github.com/huggingface/transformers) - 模型加载库

---

**提示**：如遇到任何问题，请查看 [demo/README.md](demo/README.md) 中的"已知局限"部分，或提交 Issue。
