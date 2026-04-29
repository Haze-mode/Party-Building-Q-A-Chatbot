# AutoDL部署完全指南

> 在AutoDL平台上部署GLM-4问答系统的完整步骤

## 📋 目录

- [AutoDL简介](#autodl简介)
- [方法1: 使用Git克隆（推荐）](#方法1-使用git克隆推荐)
- [方法2: 直接上传压缩包](#方法2-直接上传压缩包)
- [环境配置](#环境配置)
- [模型准备](#模型准备)
- [启动服务](#启动服务)
- [常见问题](#常见问题)

---

## 🎓 AutoDL简介

**AutoDL是什么？**
- 一个提供GPU云服务器的平台
- 按小时计费，便宜实惠
- 预装常用深度学习环境
- 适合模型训练和部署

**为什么选择AutoDL？**
- ✅ 价格便宜（最低0.5元/小时）
- ✅ GPU资源丰富（A100、V100等）
- ✅ 开箱即用（预装CUDA、PyTorch）
- ✅ 网络稳定（国内服务器）

---

## 🔧 方法1: 使用Git克隆（推荐）

### **什么是Git？**

Git是一个版本控制工具，可以：
- 管理代码的历史版本
- 在多台电脑之间同步代码
- 多人协作开发

**类比理解：**
```
Git就像是一个"云盘"，但专门用于代码
- GitHub/Gitee = 云盘服务器
- git push = 上传文件
- git pull = 下载文件
- git clone = 首次下载整个项目
```

---

### **步骤1: 在本地推送代码到Git仓库**

#### **1.1 注册账号**

**选项A: GitHub（国际通用）**
- 网址: https://github.com
- 注册免费账号

**选项B: Gitee（推荐，国内速度快）**
- 网址: https://gitee.com
- 注册免费账号
- **优势**: 国内访问速度快

---

#### **1.2 创建远程仓库**

以Gitee为例：

1. 登录Gitee
2. 点击右上角 "+" → "新建仓库"
3. 填写信息：
   - 仓库名称: `glm4-chat`
   - 是否开源: 公开（或私有）
   - 初始化README: 不勾选
4. 点击"创建"

创建成功后，你会看到类似这样的地址：
```
https://gitee.com/你的用户名/glm4-chat.git
```

---

#### **1.3 在本地配置Git**

打开PowerShell或CMD：

```powershell
# 1. 配置Git用户信息（只需做一次）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 2. 进入项目目录
cd c:\Users\liduo\Downloads\project\demo

# 3. 初始化Git仓库
git init

# 4. 添加所有文件
git add .

# 5. 提交更改
git commit -m "初始提交：GLM-4问答系统"

# 6. 关联远程仓库（替换为你的仓库地址）
git remote add origin https://gitee.com/你的用户名/glm4-chat.git

# 7. 推送到远程
git push -u origin master
```

**首次推送可能需要登录：**
- 会弹出浏览器让你授权
- 或输入Gitee的用户名和密码

---

#### **1.4 验证推送成功**

刷新Gitee仓库页面，应该能看到所有文件。

---

### **步骤2: 在AutoDL上克隆代码**

#### **2.1 登录AutoDL**

1. 访问 https://www.autodl.com
2. 登录账号
3. 进入"控制台"
4. 找到你的实例，点击"进入实例"

---

#### **2.2 打开JupyterLab或SSH**

**方式A: JupyterLab（推荐新手）**
1. 点击"JupyterLab"
2. 在左侧文件浏览器中右键 → "New Terminal"

**方式B: SSH连接（推荐高级用户）**
```bash
# Windows使用PowerShell
ssh root@connect.xxx.autodl.com -p 端口号

# 密码在AutoDL控制台查看
```

---

#### **2.3 克隆代码**

在AutoDL终端中执行：

```bash
# 1. 进入工作目录
cd /root/autodl-tmp

# 2. 克隆仓库（替换为你的仓库地址）
git clone https://gitee.com/你的用户名/glm4-chat.git

# 3. 进入项目目录
cd glm4-chat

# 4. 查看文件
ls -la
```

**✅ 成功标志：**
```
drwxr-xr-x docker/
drwxr-xr-x src/
drwxr-xr-x docs/
-rw-r--r-- README.md
...
```

---

#### **2.4 后续更新代码**

当你在本地修改了代码并推送到Git后，在AutoDL上更新：

```bash
cd /root/autodl-tmp/glm4-chat
git pull
```

就这么简单！

---

## 📦 方法2: 直接上传压缩包

如果你不想使用Git，可以用这个方法。

### **步骤1: 在本地打包**

```powershell
# Windows PowerShell
cd c:\Users\liduo\Downloads\project
Compress-Archive -Path demo -DestinationPath demo.zip
```

或使用压缩软件（如7-Zip、WinRAR）右键压缩。

---

### **步骤2: 上传到AutoDL**

#### **方式A: 通过AutoDL网页（最简单）**

1. 登录AutoDL控制台
2. 进入实例
3. 点击顶部的"上传文件"按钮
4. 选择 `demo.zip`
5. 等待上传完成（大文件可能需要几分钟）

---

#### **方式B: 使用WinSCP（Windows推荐）**

1. 下载WinSCP: https://winscp.net
2. 安装并打开
3. 填写连接信息：
   - 主机名: `connect.xxx.autodl.com`
   - 用户名: `root`
   - 密码: （在AutoDL控制台查看）
   - 端口: （在AutoDL控制台查看）
4. 点击"登录"
5. 左侧是本地文件，右侧是服务器文件
6. 拖拽 `demo.zip` 到右侧 `/root/autodl-tmp/`

---

#### **方式C: 使用SCP命令（Linux/Mac）**

```bash
scp demo.zip root@connect.xxx.autodl.com:/root/autodl-tmp/
```

---

### **步骤3: 在AutoDL上解压**

```bash
cd /root/autodl-tmp
unzip demo.zip
cd demo
```

---

## ⚙️ 环境配置

### **检查Python环境**

AutoDL通常预装了Python和Conda：

```bash
# 检查Python版本
python --version

# 检查Conda
conda --version

# 查看已有的环境
conda env list
```

---

### **创建虚拟环境（推荐）**

```bash
# 创建新环境
conda create -n glm4-chat python=3.9 -y

# 激活环境
conda activate glm4-chat

# 安装依赖
cd /root/autodl-tmp/glm4-chat  # 或 demo
pip install -r requirements.txt
```

---

### **检查GPU环境**

```bash
# 查看GPU信息
nvidia-smi

# 应该看到类似输出：
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.85.12    Driver Version: 525.85.12    CUDA Version: 12.0     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA A100-SXM...  Off  | 00000000:00:04.0 Off |                    0 |
# | N/A   35C    P0    50W / 400W |      0MiB / 40960MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

---

## 🤖 模型准备

### **方案1: 使用HuggingFace自动下载**

修改 `src/config.py`，使用在线模型：

```python
path: str = field(
    default_factory=lambda: os.environ.get(
        'MODEL_PATH', 
        'THUDM/glm-4-9b-chat'  # HuggingFace模型ID
    )
)
```

首次运行时会自动下载模型（需要联网）。

---

### **方案2: 手动上传模型（推荐）**

#### **2.1 在本地下载模型**

```bash
# 使用huggingface-cli下载
pip install huggingface_hub
huggingface-cli download THUDM/glm-4-9b-chat --local-dir ./glm-4-9b-chat
```

或从ModelScope下载（国内更快）：
```bash
pip install modelscope
modelscope download --model ZhipuAI/glm-4-9b-chat --local_dir ./glm-4-9b-chat
```

---

#### **2.2 上传模型到AutoDL**

**方式A: 使用AutoDL网盘功能**
1. AutoDL提供免费的网盘空间
2. 上传模型到网盘
3. 在实例中挂载网盘

**方式B: 直接上传（大文件较慢）**
```bash
# 打包模型
tar -czf glm-4-9b-chat.tar.gz glm-4-9b-chat/

# 上传（使用WinSCP或SCP）
scp glm-4-9b-chat.tar.gz root@connect.xxx.autodl.com:/root/autodl-tmp/
```

**方式C: 使用rsync（断点续传）**
```bash
rsync -avz --progress glm-4-9b-chat/ root@connect.xxx.autodl.com:/root/autodl-tmp/models/glm-4-9b-chat/
```

---

#### **2.3 在AutoDL上解压模型**

```bash
cd /root/autodl-tmp
tar -xzf glm-4-9b-chat.tar.gz
```

---

#### **2.4 配置模型路径**

编辑 `.env` 文件：

```bash
cd /root/autodl-tmp/glm4-chat/docker
nano .env
```

修改：
```env
USE_MOCK=false
MODEL_LOCAL_PATH=/root/autodl-tmp/glm-4-9b-chat
```

---

## 🚀 启动服务

### **方式1: 直接运行（推荐）**

```bash
cd /root/autodl-tmp/glm4-chat

# 激活环境
conda activate glm4-chat

# 设置环境变量
export MODEL_PATH=/root/autodl-tmp/glm-4-9b-chat
export KB_DIR=./data/示例知识库
export USE_MOCK=false

# 启动服务
python src/web_server.py
```

**后台运行（使用tmux）：**

```bash
# 安装tmux
apt-get install tmux -y

# 创建会话
tmux new -s glm4

# 在tmux中启动服务
python src/web_server.py

# 按 Ctrl+B, 然后按 D 退出（服务继续运行）

# 重新连接
tmux attach -t glm4
```

---

### **访问服务**

AutoDL提供了公网访问地址：

1. 在AutoDL控制台找到"自定义服务"
2. 点击"添加服务"
3. 填写：
   - 服务名称: GLM-4 Chat
   - 端口: 6006
4. 点击"确定"

系统会生成一个URL，例如：
```
http://xxx.autodl.pro:6006
```

在浏览器中打开即可使用！

---

## ❓ 常见问题

### **问题1: Git克隆速度慢**

**解决：**
```bash
# 使用Gitee代替GitHub
git clone https://gitee.com/你的用户名/glm4-chat.git

# 或配置Git代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

---

### **问题2: 模型文件太大，上传很慢**

**解决：**

**方案A: 使用AutoDL网盘**
1. 在AutoDL控制台开通网盘
2. 上传模型到网盘
3. 在实例中挂载网盘（速度快）

**方案B: 使用量化模型**
```bash
# 下载4-bit量化版本（更小）
huggingface-cli download THUDM/glm-4-9b-chat-int4 --local-dir ./glm-4-int4
```

**方案C: 使用在线模型**
```python
# config.py中直接使用HuggingFace ID
path: str = 'THUDM/glm-4-9b-chat'
```

---

### **问题3: 端口无法访问**

**解决：**

1. **检查服务是否启动**
   ```bash
   docker compose ps
   # 或
   ps aux | grep web_server
   ```

2. **检查防火墙**
   ```bash
   # AutoDL需要在控制台开放端口
   # 进入控制台 → 实例 → 自定义服务 → 添加端口6006
   ```

3. **测试本地访问**
   ```bash
   curl http://localhost:6006/api/session/list
   ```

---

### **问题4: GPU内存不足**

**解决：**

**方案A: 使用量化模型**
```bash
# 下载4-bit量化版本（更小）
huggingface-cli download THUDM/glm-4-9b-chat-int4 --local-dir ./glm-4-int4
```

**方案B: 限制显存使用**
```python
# 在 model_loader.py 中已使用FP16精度
torch_dtype=torch.float16  # 减少50%显存占用
```

**方案C: 使用CPU推理**
```env
# 修改 config.py 或在代码中指定
device_map='cpu'
```

---

### **问题5: 如何保持后台运行**

**使用tmux或screen：**

```bash
# 安装tmux
apt-get install tmux

# 创建会话
tmux new -s glm4

# 在tmux中启动服务
python src/web_server.py

# 按 Ctrl+B, 然后按 D 退出（服务继续运行）

# 重新连接
tmux attach -t glm4
```

---

## 💰 成本估算

### **AutoDL费用**

| 配置 | 价格/小时 | 适用场景 |
|------|----------|---------|
| RTX 3090 (24GB) | 1.5元 | 开发和测试 |
| A100 (40GB) | 4元 | 生产环境 |
| V100 (32GB) | 2.5元 | 中等负载 |

**示例：**
- 每天运行8小时 × 30天 × 1.5元 = 360元/月
- 比自建服务器便宜很多！

---

### **存储费用**

- 系统盘: 免费（50GB）
- 数据盘: 0.3元/GB/月
- 网盘: 免费（100GB）

**建议：**
- 代码放在系统盘
- 模型放在数据盘或网盘
- 定期清理不需要的文件

---

## 📊 Git vs 直接上传对比

| 特性 | Git克隆 | 直接上传 |
|------|--------|---------|
| **学习成本** | 需要学Git | 无需学习 |
| **更新便利性** | ✅ 简单（git pull） | ❌ 麻烦（重新上传） |
| **版本管理** | ✅ 有历史记录 | ❌ 无版本控制 |
| **大文件支持** | ⚠️ 需要Git LFS | ✅ 直接上传 |
| **速度** | ✅ 增量更新快 | ❌ 每次都全量 |
| **适用场景** | 长期项目 | 一次性部署 |

**推荐：**
- 长期使用 → 使用Git
- 临时测试 → 直接上传

---

## 🎯 最佳实践

### **推荐的AutoDL工作流程**

```
1. 本地开发
   ↓
2. Git推送到Gitee
   ↓
3. AutoDL上git pull更新
   ↓
4. 测试运行
   ↓
5. 有问题？回到步骤1
```

### **文件组织建议**

```
/root/autodl-tmp/
├── glm4-chat/              # 代码（从Git克隆）
├── models/                 # 模型文件
│   └── glm-4-9b-chat/
├── data/                   # 数据文件
│   └── knowledge-base/
└── logs/                   # 日志文件
```

### **备份策略**

```bash
# 每天备份重要数据
0 2 * * * tar -czf /backup/data-$(date +\%Y\%m\%d).tar.gz /root/autodl-tmp/data/
```

---

## 📞 获取帮助

### **AutoDL官方资源**

- 文档中心: https://www.autodl.com/docs
- 社区论坛: https://forum.autodl.com
- 客服QQ群: 在官网查看

### **本项目资源**

- [路径配置指南](PATH_CONFIGURATION.md)
- [真实模型配置](REAL_MODEL_SETUP.md)
- [Docker部署指南](DOCKER_DEPLOYMENT.md)

---

## ✨ 总结

### **Git上传的含义**

```
Git上传 = 把代码推到云端仓库(GitHub/Gitee)
        = 然后在AutoDL上拉取下来
```

### **在AutoDL上使用Git**

**✅ 可以！** 而且非常推荐：

```bash
# 在AutoDL上执行
git clone https://gitee.com/你的用户名/glm4-chat.git
cd glm4-chat
```

### **两种方法对比**

| 方法 | 难度 | 灵活性 | 推荐度 |
|------|------|--------|--------|
| Git克隆 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 直接上传 | ⭐ | ⭐⭐ | ⭐⭐⭐ |

### **快速开始**

1. **注册Gitee账号**
2. **创建仓库并推送代码**
3. **在AutoDL上git clone**
4. **配置环境和模型**
5. **启动服务**

就这么简单！🎉

---

**最后更新**: 2026-04-19  
**适用平台**: AutoDL  
**维护者**: GLM-4 Chat Team
