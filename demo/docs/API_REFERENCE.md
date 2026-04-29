# API参考文档

> GLM-4智能问答系统完整API接口说明

## 📋 目录

- [认证接口](#认证接口)
- [聊天接口](#聊天接口)
- [知识库接口](#知识库接口)
- [会话管理](#会话管理)
- [系统接口](#系统接口)
- [错误码说明](#错误码说明)

---

## 基础信息

**Base URL:** `http://localhost:6006`

**Content-Type:** `application/json`

**认证方式:** JWT Token（部分接口需要）

---

## 认证接口

### POST /api/login

用户登录，获取Token

**请求:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应:**
```json
{
  "success": true,
  "token": "931a4aca-7601-4108-b97d-9a5600bbc375",
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

**错误响应:**
```json
{
  "success": false,
  "error": "用户名或密码错误"
}
```

---

### POST /api/logout

用户登出

**请求头:**
```
Authorization: Bearer {token}
```

**响应:**
```json
{
  "success": true,
  "message": "已登出"
}
```

---

## 聊天接口

### POST /api/chatbot

发送问题，获取AI回答

**请求:**
```json
{
  "infos": "你好，请介绍一下自己",
  "session_id": "session_001"
}
```

**参数说明:**
- `infos` (必填): 用户问题
- `session_id` (必填): 会话ID，用于保持上下文

**响应:**
```json
{
  "answer": "很高兴为您解答！我是GLM-4智能助手...",
  "sources": [
    {
      "title": "公司介绍.txt",
      "content": "...",
      "score": 0.85
    }
  ],
  "session_id": "session_001",
  "retrieved_count": 3,
  "history_length": 5,
  "from_cache": false,
  "response_time": 0.523
}
```

**参数说明:**
- `answer`: AI生成的回答
- `sources`: 引用的知识来源
- `retrieved_count`: 检索到的相关段落数
- `history_length`: 当前会话历史长度
- `from_cache`: 是否来自缓存
- `response_time`: 响应时间（秒）

**缓存命中响应:**
```json
{
  "answer": "...",
  "from_cache": true,
  "response_time": 0.012
}
```

---

## 知识库接口

### GET /api/kb/files

获取知识库文件列表（需要管理员权限）

**请求头:**
```
Authorization: Bearer {token}
```

**响应:**
```json
{
  "success": true,
  "files": [
    {
      "filename": "公司介绍.txt",
      "size": 15234,
      "modified": "2026-04-19T10:30:00",
      "format": "txt"
    },
    {
      "filename": "产品说明.pdf",
      "size": 524288,
      "modified": "2026-04-18T15:20:00",
      "format": "pdf"
    }
  ],
  "total_count": 2,
  "kb_dir": "/app/data/示例知识库"
}
```

---

### POST /api/kb/upload

上传文件到知识库（需要管理员权限）

**请求:**
```
Content-Type: multipart/form-data

file: <binary>
```

**cURL示例:**
```bash
curl -X POST http://localhost:6006/api/kb/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

**响应:**
```json
{
  "success": true,
  "message": "文件上传成功",
  "filename": "document.pdf",
  "size": 102400,
  "chunks_created": 25
}
```

**支持的文件格式:**
- `.txt` - 文本文件
- `.pdf` - PDF文档
- `.docx` - Word文档

---

### DELETE /api/kb/files

删除知识库文件（需要管理员权限）

**请求:**
```json
{
  "filename": "document.pdf"
}
```

**响应:**
```json
{
  "success": true,
  "message": "文件已删除，知识库已重载",
  "filename": "document.pdf"
}
```

---

### POST /api/kb/reload

重新加载知识库（需要管理员权限）

**用途:** 上传或删除文件后，手动触发知识库重建

**请求:**
```json
{
  "kb_dir": "/app/data/示例知识库"
}
```

**响应:**
```json
{
  "success": true,
  "message": "知识库重载成功",
  "documents_loaded": 10,
  "chunks_created": 250,
  "reload_time": 2.345
}
```

---

## 会话管理

### GET /api/session/list

获取会话列表

**请求头:**
```
Authorization: Bearer {token}
```

**响应:**
```json
{
  "success": true,
  "session_count": 5,
  "sessions": [
    {
      "session_id": "session_001",
      "title": "关于公司产品的咨询",
      "created_at": "2026-04-19T10:00:00",
      "last_access": "2026-04-19T10:30:00",
      "message_count": 12
    },
    {
      "session_id": "session_002",
      "title": "技术支持问题",
      "created_at": "2026-04-18T15:00:00",
      "last_access": "2026-04-18T16:00:00",
      "message_count": 8
    }
  ]
}
```

---

### GET /api/session/history

获取会话历史消息

**请求:**
```
GET /api/session/history?session_id=session_001
```

**请求头:**
```
Authorization: Bearer {token}
```

**响应:**
```json
{
  "success": true,
  "session_id": "session_001",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2026-04-19T10:00:00"
    },
    {
      "role": "assistant",
      "content": "您好！有什么可以帮助您的吗？",
      "timestamp": "2026-04-19T10:00:01"
    },
    {
      "role": "user",
      "content": "你们的产品有哪些功能？",
      "timestamp": "2026-04-19T10:01:00"
    },
    {
      "role": "assistant",
      "content": "我们的产品主要包含以下功能...",
      "timestamp": "2026-04-19T10:01:02"
    }
  ],
  "total_messages": 4
}
```

---

### GET /api/session/clear

清空会话历史

**请求:**
```
GET /api/session/clear?session_id=session_001
```

**请求头:**
```
Authorization: Bearer {token}
```

**响应:**
```json
{
  "success": true,
  "message": "会话已清空",
  "session_id": "session_001"
}
```

---

## 系统接口

### GET /health

健康检查端点

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-19T10:30:00",
  "version": "1.0.0",
  "checks": {
    "database": {
      "ok": true,
      "message": "Database connected"
    },
    "redis": {
      "ok": true,
      "message": "Redis connected"
    },
    "disk_space": {
      "ok": true,
      "message": "Disk usage: 45.2%"
    }
  },
  "uptime": 86400,
  "memory_usage": 134217728
}
```

**状态码:**
- `200` - 服务健康
- `503` - 服务不健康

---

### GET /api/session/list

获取会话列表（无需认证）

**响应:**
```json
{
  "success": true,
  "session_count": 0,
  "sessions": []
}
```

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token无效或过期） |
| 403 | 禁止访问（权限不足） |
| 404 | 资源不存在 |
| 429 | 请求过于频繁（限流） |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "请求参数错误",
    "details": {
      "field": "session_id",
      "reason": "不能为空"
    }
  }
}
```

### 常见错误

**1. Token无效**
```json
{
  "success": false,
  "error": "Token无效或已过期，请重新登录"
}
```

**2. 权限不足**
```json
{
  "success": false,
  "error": "需要管理员权限"
}
```

**3. 文件不存在**
```json
{
  "success": false,
  "error": "文件不存在: document.pdf"
}
```

**4. 请求限流**
```json
{
  "success": false,
  "error": "请求过于频繁，请稍后重试",
  "retry_after": 60
}
```

---

## 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:6006"

# 1. 登录
response = requests.post(f"{BASE_URL}/api/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. 发送问题
response = requests.post(f"{BASE_URL}/api/chatbot", json={
    "infos": "你好",
    "session_id": "test_session"
}, headers=headers)

print(response.json()["answer"])

# 3. 获取会话历史
response = requests.get(
    f"{BASE_URL}/api/session/history?session_id=test_session",
    headers=headers
)

print(response.json()["messages"])
```

### cURL示例

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:6006/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

# 发送问题
curl -X POST http://localhost:6006/api/chatbot \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"infos":"你好","session_id":"test"}'

# 获取文件列表
curl -X GET http://localhost:6006/api/kb/files \
  -H "Authorization: Bearer $TOKEN"
```

### JavaScript示例

```javascript
const BASE_URL = "http://localhost:6006";

// 登录
async function login() {
  const response = await fetch(`${BASE_URL}/api/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin',
      password: 'admin123'
    })
  });
  
  const data = await response.json();
  return data.token;
}

// 发送问题
async function askQuestion(token, question, sessionId) {
  const response = await fetch(`${BASE_URL}/api/chatbot`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      infos: question,
      session_id: sessionId
    })
  });
  
  const data = await response.json();
  return data.answer;
}

// 使用
const token = await login();
const answer = await askQuestion(token, "你好", "session_001");
console.log(answer);
```

---

## 最佳实践

### 1. Token管理

```python
# ✅ 推荐：缓存Token，避免频繁登录
class APIClient:
    def __init__(self):
        self.token = None
        self.token_expire = 0
    
    def get_token(self):
        if time.time() > self.token_expire:
            # Token过期，重新登录
            self.login()
        return self.token
```

### 2. 错误处理

```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
    
    if not result.get("success"):
        print(f"API错误: {result.get('error')}")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
```

### 3. 会话管理

```python
# ✅ 推荐：为每个用户创建独立的session_id
import uuid

session_id = str(uuid.uuid4())

# 在同一会话中连续提问
ask("第一个问题", session_id)
ask("第二个问题", session_id)  # 保持上下文
```

### 4. 限流处理

```python
import time

def rate_limited_request(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = 2 ** attempt  # 指数退避
            time.sleep(wait_time)
    raise Exception("超过最大重试次数")
```

---

## 相关文档

- [快速开始](QUICKSTART.md)
- [Mock模式指南](MOCK_MODE_GUIDE.md)
- [开发指南](DEVELOPMENT_GUIDE.md)
- [压力测试指南](LOAD_TESTING.md)

---

**API版本**: v1.0  
**最后更新**: 2026-04-19  
**维护者**: GLM-4 Chat Team
