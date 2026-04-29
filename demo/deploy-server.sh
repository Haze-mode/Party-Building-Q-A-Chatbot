#!/bin/bash
# AutoDL服务器一键部署脚本

set -e

echo "=========================================="
echo "  GLM-4 问答系统 - 服务器部署脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在正确目录
if [ ! -f "docker/docker-compose.yml" ] && [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录或docker目录下运行此脚本${NC}"
    exit 1
fi

# 进入docker目录
cd docker 2>/dev/null || true

echo -e "${YELLOW}📋 部署方式选择:${NC}"
echo "1. Docker部署（推荐）"
echo "2. 直接运行Python"
read -p "请选择 (1/2): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🐳 开始Docker部署...${NC}"
        echo ""
        
        # 检查Docker
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}❌ Docker未安装${NC}"
            exit 1
        fi
        
        # 配置.env文件
        if [ ! -f ".env" ]; then
            echo "📝 创建配置文件..."
            cp .env.example .env
            
            echo ""
            echo "请输入模型路径（例如: /root/autodl-tmp/models/glm-4-9b-chat）:"
            read -p "> " MODEL_PATH
            
            if [ -z "$MODEL_PATH" ]; then
                MODEL_PATH="/root/autodl-tmp/models/glm-4-9b-chat"
            fi
            
            sed -i "s|MODEL_LOCAL_PATH=.*|MODEL_LOCAL_PATH=$MODEL_PATH|" .env
            sed -i "s/USE_MOCK=.*/USE_MOCK=false/" .env
            
            echo -e "${GREEN}✓ 配置文件已创建${NC}"
        fi
        
        # 显示配置
        echo ""
        echo "当前配置:"
        cat .env | grep -E "USE_MOCK|MODEL_LOCAL_PATH|WEB_PORT"
        echo ""
        
        # 询问是否构建
        read -p "是否重新构建镜像? (y/n): " rebuild
        if [[ $rebuild =~ ^[Yy]$ ]]; then
            echo ""
            echo "🔨 构建镜像..."
            docker compose build
        fi
        
        # 启动服务
        echo ""
        echo "🚀 启动服务..."
        docker compose up -d
        
        # 等待服务启动
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 5
        
        # 检查服务状态
        if docker compose ps | grep -q "Up"; then
            echo -e "${GREEN}✓ 服务启动成功!${NC}"
            echo ""
            echo "查看日志: docker compose logs -f web"
            echo "停止服务: docker compose down"
            echo ""
            echo "在AutoDL控制台配置端口6006后即可访问"
        else
            echo -e "${RED}❌ 服务启动失败，请查看日志:${NC}"
            docker compose logs web
            exit 1
        fi
        ;;
        
    2)
        echo ""
        echo -e "${GREEN}🐍 开始直接运行部署...${NC}"
        echo ""
        
        # 检查Python
        if ! command -v python &> /dev/null; then
            echo -e "${RED}❌ Python未安装${NC}"
            exit 1
        fi
        
        # 检查Conda环境
        if command -v conda &> /dev/null; then
            echo "📦 检查Conda环境..."
            
            if conda env list | grep -q "glm4-chat"; then
                echo -e "${GREEN}✓ Conda环境已存在${NC}"
            else
                echo "创建Conda环境..."
                conda create -n glm4-chat python=3.9 -y
            fi
            
            echo "激活环境..."
            source $(conda info --base)/etc/profile.d/conda.sh
            conda activate glm4-chat
        fi
        
        # 安装依赖
        echo ""
        echo "📦 安装依赖..."
        cd ..
        pip install -r requirements.txt
        
        # 配置环境变量
        echo ""
        echo "请输入模型路径:"
        read -p "> " MODEL_PATH
        
        if [ -z "$MODEL_PATH" ]; then
            MODEL_PATH="/root/autodl-tmp/models/glm-4-9b-chat"
        fi
        
        export MODEL_PATH=$MODEL_PATH
        export KB_DIR=./data/示例知识库
        export USE_MOCK=false
        export WEB_PORT=6006
        
        echo ""
        echo "配置:"
        echo "  MODEL_PATH=$MODEL_PATH"
        echo "  KB_DIR=./data/示例知识库"
        echo "  WEB_PORT=6006"
        echo ""
        
        # 询问运行方式
        echo "选择运行方式:"
        echo "1. 前台运行（可以看到日志）"
        echo "2. 后台运行（使用tmux）"
        read -p "请选择 (1/2): " run_choice
        
        case $run_choice in
            1)
                echo ""
                echo "🚀 启动服务..."
                cd src
                python web_server.py
                ;;
            2)
                echo ""
                
                # 检查tmux
                if ! command -v tmux &> /dev/null; then
                    echo "安装tmux..."
                    apt-get update && apt-get install -y tmux
                fi
                
                # 创建tmux会话
                tmux new -d -s glm4 "cd $(pwd)/src && MODEL_PATH=$MODEL_PATH KB_DIR=./data/示例知识库 USE_MOCK=false WEB_PORT=6006 python web_server.py"
                
                echo -e "${GREEN}✓ 服务已在后台启动${NC}"
                echo ""
                echo "查看日志: tmux attach -t glm4"
                echo "停止服务: tmux kill-session -t glm4"
                echo ""
                echo "在AutoDL控制台配置端口6006后即可访问"
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                exit 1
                ;;
        esac
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo -e "${GREEN}  部署完成！${NC}"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 在AutoDL控制台添加自定义服务（端口6006）"
echo "2. 访问生成的URL"
echo "3. 使用默认账号登录: admin / admin123"
echo ""
