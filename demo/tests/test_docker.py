"""Docker部署测试脚本"""
import subprocess
import time
import requests
import sys

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("错误:", result.stderr)
    
    return result.returncode == 0

def test_docker():
    """测试Docker部署"""
    print("🐳 Docker部署测试开始\n")
    
    # 1. 检查Docker
    if not run_command("docker --version", "检查Docker版本"):
        print("❌ Docker未安装")
        return False
    
    # 2. 检查Docker Compose
    if not run_command("docker-compose --version", "检查Docker Compose版本"):
        print("❌ Docker Compose未安装")
        return False
    
    # 3. 构建镜像
    print("\n⚠️  是否要构建Docker镜像？(这可能需要几分钟)")
    choice = input("继续? (y/n): ").strip().lower()
    
    if choice != 'y':
        print("⏭️  跳过构建")
        return True
    
    if not run_command("docker-compose build", "构建Docker镜像"):
        print("❌ 构建失败")
        return False
    
    print("\n✅ 构建成功！")
    print("\n📝 下一步操作：")
    print("  1. 启动服务: docker-compose up -d")
    print("  2. 查看日志: docker-compose logs -f")
    print("  3. 访问服务: http://localhost:6006")
    print("  4. 停止服务: docker-compose down")
    
    return True

if __name__ == "__main__":
    success = test_docker()
    sys.exit(0 if success else 1)
