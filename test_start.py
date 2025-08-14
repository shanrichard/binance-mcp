#!/usr/bin/env python3
"""
测试CLI start命令
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def test_cli_start():
    print("🧪 测试CLI start命令...")
    
    # 使用subprocess在真实环境中测试
    cmd = [sys.executable, "-m", "binance_mcp.cli", "start", "--port", "9003"]
    
    print(f"运行命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待3秒看输出
        try:
            stdout, stderr = process.communicate(timeout=3)
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            print(f"返回码: {process.returncode}")
        except subprocess.TimeoutExpired:
            # 3秒后强制结束
            process.terminate()
            stdout, stderr = process.communicate()
            print("✅ 服务器启动成功（3秒后自动终止）")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_cli_start()