# Mock 调试模式使用指南

## 🎭 什么是 Mock 模式？

Mock 模式是一种**无需真实大模型**即可运行和调试代码的模式。它使用模拟的模型行为来替代真实的AI推理，让您可以在本地快速测试所有功能。

---

## ✨ 为什么需要 Mock 模式？

### 传统方式的问题
- ❌ 需要下载几十GB的模型文件
- ❌ 需要强大的GPU（16GB+显存）
- ❌ 启动时间长（5-10分钟）
- ❌ 占用大量资源

### Mock 模式的优势
- ✅ **无需模型文件** - 立即启动
- ✅ **无需GPU** - CPU即可运行
- ✅ **秒级启动** - 几乎无等待
- ✅ **轻量级** - 内存占用<500MB
- ✅ **功能完整** - 所有API都可测试

---

## 🚀 快速开始

### 方法1: 环境变量启动（推荐）

```bash
# Windows PowerShell
$env:USE_MOCK="true"
python web_server.py

# Windows CMD
set USE_MOCK=true
python web_server.py

# Linux/Mac
export USE_MOCK=true
python web_server.py
```

### 方法2: 命令行参数

```bash
# Windows
set USE_MOCK=1 && python web_server.py

# Linux/Mac
USE_MOCK=1 python web_server.py
```

### 方法3: 修改代码（永久启用）

编辑 `web_server.py` 最后一行：

```python
if __name__ == '__main__':
    start_server(use_mock=True)  # 强制使用Mock模式
```

---

## 📊 Mock 模式 vs 真实模式对比

| 特性 | Mock模式 | 真实模式 |
|------|----------|----------|
| 启动时间 | <5秒 | 5-10分钟 |
| 内存占用 | ~300MB | 8-16GB |
| GPU需求 | 不需要 | 必需 |
| 模型文件 | 不需要 | 需要(10-20GB) |
| 回答质量 | 模拟回答 | 真实AI生成 |
| 适用场景 | 开发调试 | 生产环境 |
| API接口 | ✅ 完全相同 | ✅ 完全相同 |
| 会话管理 | ✅ 完全相同 | ✅ 完全相同 |
| 知识库检索 | ✅ 完全相同 | ✅ 完全相同 |

---

## 🔧 Mock 模式工作原理

### 1. MockTokenizer（模拟分词器）

```python
class MockTokenizer:
    """模拟分词器，不真正分词"""
    
    def apply_chat_template(self, messages, ...):
        # 返回模拟的tensor对象
        return MockTensor()
```

### 2. MockModel（模拟模型）

```python
class MockModel:
    """模拟语言模型"""
    
    def generate(self, input_ids, streamer, ...):
        # 1. 延迟0.5秒（模拟推理时间）
        time.sleep(0.5)
        
        # 2. 从预设回答中随机选择一个
        response = self._get_mock_response()
        
        # 3. 逐字输出（模拟流式生成）
        for char in response:
            streamer.put(char)
            time.sleep(0.02)
```

### 3. 预设回答模板

Mock模式内置了5种回答模板，会随机选择：

```python
mock_responses = [
    "这是一个很好的问题！基于我的知识...",
    "感谢您的提问！让我来解答...",
    "好问题！我来为您详细说明...",
    "很高兴为您解答！",
    "让我想想... 这是一个很有深度的问题！"
]
```

---

## 💻 实际使用示例

### 1. 启动服务

```bash
# 启用Mock模式
$env:USE_MOCK="true"  # Windows
python web_server.py
```

**启动输出**：
```
============================================================
GLM-4 问答服务启动中...
🎭 模式: Mock调试模式（无需真实模型）
============================================================
正在加载 Mock 模型...
============================================================
🎭 正在加载 Mock 模型（调试模式）
============================================================
MockTokenizer 初始化完成
MockModel 初始化完成
✅ Mock 模型加载完成
⚠️  注意：当前使用模拟回答，非真实AI生成
============================================================
✓ Mock模型加载完成
正在加载知识库: ../党建知识库
...
🚀 服务已启动！
📍 地址: http://0.0.0.0:6006
```

### 2. 测试聊天接口

```bash
# 发送问题
curl "http://localhost:6006/api/chatbot?infos=什么是人工智能"
```

**返回结果**：
```json
{
  "answer": "这是一个很好的问题！基于我的知识，我可以这样回答：\n\n首先，这个概念涉及到多个方面...",
  "sources": ["相关段落1", "相关段落2"],
  "session_id": "default",
  "retrieved_count": 3,
  "history_length": 1
}
```

### 3. 测试多轮对话

```bash
# 第1轮
curl "http://localhost:6006/api/chatbot?infos=问题1&session_id=test"

# 第2轮
curl "http://localhost:6006/api/chatbot?infos=问题2&session_id=test"

# 查看历史
curl "http://localhost:6006/api/session/history?session_id=test"
```

### 4. 测试所有API

```bash
# 登录
curl -X POST http://localhost:6006/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 上传文件
curl -X POST http://localhost:6006/api/kb/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"

# 重载知识库
curl -X POST http://localhost:6006/api/kb/reload \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**所有API在Mock模式下都能正常工作！**

---

## 🎯 Mock 模式的用途

### 1. **前端开发调试**

```javascript
// 前端开发者可以立即开始工作，无需等待模型部署
fetch('http://localhost:6006/api/chatbot', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({infos: '测试问题'})
})
.then(res => res.json())
.then(data => {
  console.log('回答:', data.answer);
  // 继续开发UI逻辑
});
```

### 2. **API接口测试**

```python
import requests

# 测试所有接口
base_url = "http://localhost:6006"

# 聊天
response = requests.get(f"{base_url}/api/chatbot", 
                       params={"infos": "测试"})
print(response.json())

# 会话管理
response = requests.get(f"{base_url}/api/session/list")
print(response.json())
```

### 3. **业务流程验证**

```bash
# 完整的用户流程测试
# 1. 注册/登录
# 2. 上传知识库
# 3. 发起对话
# 4. 查看历史
# 5. 清空会话

# 所有步骤都可以测试，无需真实AI
```

### 4. **性能测试**

```bash
# 压力测试API响应速度
ab -n 100 -c 10 "http://localhost:6006/api/chatbot?infos=test"

# Mock模式可以快速响应，适合测试并发能力
```

### 5. **CI/CD 集成**

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start server in mock mode
        run: |
          export USE_MOCK=true
          python web_server.py &
          sleep 5
      - name: Run tests
        run: pytest tests/
```

---

## 🔍 Mock 模式的限制

### ❌ 不能做的事情

1. **测试真实的AI回答质量**
   - Mock回答是预设的，不是真正生成的
   
2. **测试模型性能**
   - 无法评估真实推理速度
   
3. **测试显存占用**
   - Mock模式不使用GPU

### ✅ 可以做的事情

1. **测试所有API接口** ✓
2. **测试业务逻辑** ✓
3. **测试前端集成** ✓
4. **测试会话管理** ✓
5. **测试知识库功能** ✓
6. **测试认证授权** ✓
7. **测试错误处理** ✓
8. **测试并发性能** ✓

---

## 🛠️ 自定义 Mock 回答

如果您想让Mock回答更智能，可以修改 `mock_model.py`：

### 方法1: 基于关键词匹配

```python
def _get_mock_response(self) -> str:
    """根据问题内容返回相关回答"""
    
    # 获取最近的用户问题（需要从chat_engine传入）
    # 这里简化处理
    
    if "python" in self.last_question.lower():
        return "Python是一种流行的编程语言..."
    elif "java" in self.last_question.lower():
        return "Java是一种面向对象的编程语言..."
    else:
        return random.choice(self.default_responses)
```

### 方法2: 添加更多回答模板

```python
mock_responses = [
    # 添加您自己的回答模板
    "关于这个问题，我的看法是...\n\n[您的自定义回答]",
    "根据相关资料...\n\n[您的自定义回答]",
    # ... 更多
]
```

### 方法3: 从文件读取回答

```python
def _load_mock_responses(self):
    """从JSON文件加载回答"""
    with open('mock_responses.json', 'r', encoding='utf-8') as f:
        return json.load(f)
```

---

## 📝 切换到真实模式

当您准备好使用真实模型时：

### 方法1: 取消环境变量

```bash
# Windows
$env:USE_MOCK=""  # 清空变量

# Linux/Mac
unset USE_MOCK

# 重新启动
python web_server.py
```

### 方法2: 明确设置为false

```bash
$env:USE_MOCK="false"
python web_server.py
```

### 方法3: 修改代码

```python
if __name__ == '__main__':
    start_server(use_mock=False)  # 使用真实模型
```

---

## 🐛 常见问题

### Q1: Mock模式的回答太简单怎么办？

**A**: 编辑 `mock_model.py`，添加更多、更详细的回答模板。

### Q2: 如何知道当前是Mock模式还是真实模式？

**A**: 查看启动日志：
- Mock模式: `🎭 模式: Mock调试模式`
- 真实模式: `🤖 模式: 真实模型模式`

### Q3: Mock模式会影响知识库检索吗？

**A**: **不会！** 知识库检索完全正常工作，只是最后的回答是模拟的。

### Q4: 可以同时测试多个会话吗？

**A**: **可以！** Mock模式完全支持多会话并发。

### Q5: Mock模式的性能如何？

**A**: 非常快！通常 <1秒 就能返回回答（真实模型需要2-5秒）。

---

## 🎓 最佳实践

### 1. 开发阶段

```bash
# 始终使用Mock模式进行开发
$env:USE_MOCK="true"
python web_server.py

# 快速迭代，即时看到效果
```

### 2. 测试阶段

```bash
# 先用Mock模式测试功能
$env:USE_MOCK="true"
pytest tests/

# 再用真实模式测试性能
$env:USE_MOCK="false"
pytest tests/performance/
```

### 3. 部署阶段

```bash
# 生产环境使用真实模型
python web_server.py  # 默认use_mock=False
```

---

## 📚 相关文档

- [快速启动指南](QUICKSTART.md)
- [API文档](README.md)
- [项目重构说明](REFACTORING.md)

---

## 💡 总结

**Mock模式让您：**
- ✅ 无需模型即可开发
- ✅ 快速测试所有功能
- ✅ 降低开发门槛
- ✅ 提高开发效率

**何时使用：**
- 🛠️ 本地开发调试
- 🧪 API接口测试
- 🎨 前端集成开发
- 📊 性能基准测试

**何时不用：**
- 🚀 生产环境部署
- 🎯 AI效果评估
- ⚡ 真实性能测试

---

**Happy Coding! 🎉**
