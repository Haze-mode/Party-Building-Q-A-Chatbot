@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    GLM-4 问答服务 - Mock 调试模式启动脚本
echo ============================================================
echo.
echo 🎭 正在启动 Mock 模式（无需真实模型）...
echo.

set USE_MOCK=true
python web_server.py

pause
