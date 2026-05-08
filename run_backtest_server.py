#!/usr/bin/env python3
"""
BTC 回测系统服务器启动脚本
快速启动 FastAPI 服务器和 Web UI
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

# 添加项目路径到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    required = ['fastapi', 'uvicorn', 'pandas', 'numpy', 'mysql.connector']
    missing = []
    
    for module in required:
        try:
            if module == 'mysql.connector':
                __import__('mysql.connector')
            else:
                __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print("pip install fastapi uvicorn pandas numpy mysql-connector-python pyyaml")
        return False
    
    print("✅ 依赖检查通过")
    return True

def check_database():
    """检查数据库连接"""
    print("🔍 检查数据库连接...")
    
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='btc_assistant',
            connect_timeout=5
        )
        conn.close()
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. MySQL 是否运行: mysql.server status")
        print("  2. 数据库配置: config/backtest.yaml")
        return False

def check_api_file():
    """检查 API 文件是否存在"""
    api_file = project_root / "backend" / "backtest" / "api.py"
    
    if not api_file.exists():
        print(f"❌ API 文件不存在: {api_file}")
        print("\n提示: 回测系统代码可能还未创建")
        print("\n请先创建以下文件:")
        print("  - backend/backtest/api.py (FastAPI 应用)")
        print("  - web/backtest.html (Web UI)")
        return False
    
    return True

def start_server():
    """启动 FastAPI 服务器"""
    print("\n" + "="*50)
    print("🚀 启动 BTC 回测系统")
    print("="*50 + "\n")
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 检查数据库
    if not check_database():
        return False
    
    # 检查 API 文件
    if not check_api_file():
        return False
    
    print("\n📡 启动 API 服务器...")
    print("="*50)
    print("📊 Web UI:      http://127.0.0.1:8001/backtest.html")
    print("📖 API 文档:    http://127.0.0.1:8001/docs")
    print("🛑 停止服务:    Ctrl+C")
    print("="*50 + "\n")
    
    # 等待一下再打开浏览器
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open('http://127.0.0.1:8001/backtest.html')
            print("🌐 已打开浏览器")
        except:
            pass
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 启动 uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "backend.backtest.api:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
        return True
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        return False

if __name__ == "__main__":
    try:
        success = start_server()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
        sys.exit(0)
