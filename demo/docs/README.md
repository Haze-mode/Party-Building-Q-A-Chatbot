# 文档使用指南

> 帮助你快速找到需要的文档

## 📚 文档分类

### 🎯 我是新手，想快速上手

**推荐阅读顺序：**

1. **[README.md](../README.md)** - 先看这个！项目总览和快速开始
2. **[QUICKSTART.md](QUICKSTART.md)** - 5分钟启动指南
3. **[MOCK_MODE_GUIDE.md](MOCK_MODE_GUIDE.md)** - 无需模型即可体验

**预计时间：** 10-15分钟

---

### 💻 我是开发者，想了解代码

**推荐阅读顺序：**

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - 系统架构和核心模块
2. **[CODE_STRUCTURE.md](CODE_STRUCTURE.md)** - 详细代码说明（每个文件的职责）
3. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 项目目录结构
4. **[API_REFERENCE.md](API_REFERENCE.md)** - API接口文档

**预计时间：** 30-60分钟

---

### 🚀 我要部署到服务器

**根据部署环境选择：**

#### AutoDL云平台
- **[AUTODL_DEPLOYMENT.md](AUTODL_DEPLOYMENT.md)** - 完整的AutoDL部署指南
  - Git克隆代码
  - 环境配置
  - 模型准备
  - 启动服务

#### 本地/其他服务器
- 参考 `AUTODL_DEPLOYMENT.md` 中的"直接运行"部分
- 或使用Mock模式快速测试

**预计时间：** 30-60分钟（取决于网络速度）

---

### ⚡ 我想优化性能

**阅读：**

- **[MULTI_CONCURRENCY_OPTIMIZATION.md](MULTI_CONCURRENCY_OPTIMIZATION.md)** - 并发优化指南
  - LRU缓存机制
  - 会话管理优化
  - 性能监控
  - 扩展建议

**预计时间：** 20-30分钟

---

## 📋 文档清单

| 文档 | 大小 | 适合人群 | 核心内容 |
|------|------|---------|---------|
| [README.md](../README.md) | 中 | 所有人 | 项目介绍、快速开始、技术栈 |
| [QUICKSTART.md](QUICKSTART.md) | 小 | 新手 | 5分钟启动、常见问题 |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | 中 | 所有人 | 系统架构、核心特性、使用场景 |
| [CODE_STRUCTURE.md](CODE_STRUCTURE.md) | 大 | 开发者 | 代码详解、模块说明、数据流程 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 小 | 开发者 | 目录结构、文件职责 |
| [API_REFERENCE.md](API_REFERENCE.md) | 中 | 开发者 | REST API接口文档 |
| [AUTODL_DEPLOYMENT.md](AUTODL_DEPLOYMENT.md) | 中 | 运维 | AutoDL部署、环境配置 |
| [MOCK_MODE_GUIDE.md](MOCK_MODE_GUIDE.md) | 小 | 开发者 | Mock模式使用、本地调试 |
| [MULTI_CONCURRENCY_OPTIMIZATION.md](MULTI_CONCURRENCY_OPTIMIZATION.md) | 大 | 高级用户 | 性能优化、并发处理 |

---

## ❓ 常见问题

### Q: 我应该从哪个文档开始？

**A:** 
- 如果是第一次接触项目 → 从 `README.md` 开始
- 如果想快速运行 → 从 `QUICKSTART.md` 开始
- 如果想了解代码 → 从 `PROJECT_OVERVIEW.md` 开始

### Q: 文档太多，看不完怎么办？

**A:** 
不需要看完所有文档！根据你的角色选择：
- **用户**：只看 README + QUICKSTART
- **开发者**：看 PROJECT_OVERVIEW + CODE_STRUCTURE + API_REFERENCE
- **运维**：看 AUTODL_DEPLOYMENT + MULTI_CONCURRENCY_OPTIMIZATION

### Q: 遇到问题是看哪个文档？

**A:**
- 安装/启动问题 → `QUICKSTART.md` 的"常见问题"章节
- 部署问题 → `AUTODL_DEPLOYMENT.md` 的"故障排查"章节
- API调用问题 → `API_REFERENCE.md`
- 代码问题 → `CODE_STRUCTURE.md`

---

## 🔄 文档更新

本文档最后更新：2026-04-27

如有文档缺失或错误，请提交Issue或联系项目维护者。

---

**提示：** 所有文档都使用Markdown格式，可以使用任何Markdown阅读器查看，推荐VS Code + Markdown Preview插件。
