"""
CLI命令行接口模块

提供binance-mcp命令行工具，包括：
- config: 配置API密钥和账户
- start: 启动MCP服务
- stop: 停止MCP服务
- status: 查看服务状态
- list: 列出配置的账户
"""

import os
import sys
import json
import time
import signal
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import click

from . import __version__
from .config import ConfigManager
from .server import create_server, get_server
from .broker import exchange_factory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='启用详细日志')
def cli(verbose):
    """Binance MCP Server - 币安交易所MCP服务"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("启用详细日志模式")


@cli.command()
@click.option('--account-id', help='指定账户ID')
def config(account_id):
    """配置API密钥和账户"""
    try:
        config_manager = ConfigManager()
        
        if account_id:
            # 单个账户配置模式
            click.echo(f"配置账户: {account_id}")
            
            # 检查账户是否存在
            accounts = config_manager.list_accounts()
            if account_id in accounts:
                if not click.confirm(f"账户 {account_id} 已存在，是否覆盖？"):
                    click.echo("配置已取消")
                    return
            
            # 获取配置信息
            api_key = click.prompt("API Key", hide_input=False)
            secret = click.prompt("Secret", hide_input=True)
            sandbox = click.confirm("是否为沙盒环境？", default=False)
            description = click.prompt("账户描述 (可选)", default="", show_default=False)
            
            try:
                if account_id in accounts:
                    config_manager.update_account(account_id, api_key, secret, sandbox, description)
                    click.echo(f"✓ 账户 {account_id} 更新成功")
                else:
                    config_manager.add_account(account_id, api_key, secret, sandbox, description)
                    click.echo(f"✓ 账户 {account_id} 添加成功")
                
                # 测试连接
                if click.confirm("是否测试连接？", default=True):
                    test_connection(account_id)
                    
            except Exception as e:
                click.echo(f"✗ 配置失败: {e}", err=True)
                sys.exit(1)
        else:
            # 交互式配置模式
            config_manager.interactive_setup()
        
    except Exception as e:
        click.echo(f"配置失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', default=9001, help='服务端口', type=int)
@click.option('--host', default='127.0.0.1', help='服务地址')
@click.option('--daemon', '-d', is_flag=True, help='后台运行')
def start(port, host, daemon):
    """启动MCP服务"""
    try:
        # 检查服务是否已在运行
        if is_server_running(port):
            click.echo(f"MCP服务已在端口 {port} 上运行")
            return
        
        # 验证配置
        config_manager = ConfigManager()
        accounts = config_manager.list_accounts()
        if not accounts:
            click.echo("未配置任何账户，请先运行: binance-mcp config", err=True)
            sys.exit(1)
        
        click.echo(f"启动Binance MCP服务...")
        click.echo(f"地址: {host}:{port}")
        click.echo(f"已配置账户: {len(accounts)} 个")
        
        if daemon:
            # 后台运行模式
            start_daemon(host, port)
        else:
            # 前台运行模式
            server = create_server(port=port, host=host)
            
            # 设置信号处理
            def signal_handler(signum, frame):
                click.echo("\n正在停止服务...")
                server.stop()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # 启动服务器
            server.start()
        
    except Exception as e:
        click.echo(f"启动失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', default=9001, help='服务端口', type=int)
def stop(port):
    """停止MCP服务"""
    try:
        pid_file = get_pid_file_path(port)
        
        if not pid_file.exists():
            click.echo(f"端口 {port} 上没有运行的MCP服务")
            return
        
        # 读取PID
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
        except (IOError, ValueError):
            click.echo("无效的PID文件")
            pid_file.unlink(missing_ok=True)
            return
        
        # 终止进程
        try:
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程终止
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                    time.sleep(0.5)
                except ProcessLookupError:
                    break
            else:
                # 强制终止
                os.kill(pid, signal.SIGKILL)
            
            # 清理PID文件
            pid_file.unlink(missing_ok=True)
            click.echo("MCP服务已停止")
            
        except ProcessLookupError:
            click.echo("进程不存在，清理PID文件")
            pid_file.unlink(missing_ok=True)
        except PermissionError:
            click.echo("没有权限停止服务", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"停止失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', default=9001, help='服务端口', type=int)
@click.option('--json-output', is_flag=True, help='输出JSON格式')
def status(port, json_output):
    """查看服务状态"""
    try:
        config_manager = ConfigManager()
        
        # 基础状态信息
        status_info = {
            "service": "binance-mcp",
            "version": __version__,
            "port": port,
            "running": is_server_running(port),
            "config_path": config_manager.get_config_path(),
            "accounts": {}
        }
        
        # 账户信息
        accounts = config_manager.list_accounts()
        for account_id, account_info in accounts.items():
            status_info["accounts"][account_id] = {
                "description": account_info.get("description", ""),
                "sandbox": account_info.get("sandbox", False),
                "valid": config_manager.validate_account(account_id)
            }
        
        # 如果服务在运行，获取更多信息
        if status_info["running"]:
            try:
                server = get_server()
                if server:
                    server_info = server.get_server_info()
                    status_info.update(server_info)
            except Exception as e:
                status_info["server_error"] = str(e)
        
        if json_output:
            click.echo(json.dumps(status_info, indent=2, ensure_ascii=False))
        else:
            # 格式化输出
            click.echo("=== Binance MCP 服务状态 ===")
            click.echo(f"版本: {status_info['version']}")
            click.echo(f"端口: {status_info['port']}")
            click.echo(f"状态: {'运行中' if status_info['running'] else '已停止'}")
            click.echo(f"配置文件: {status_info['config_path']}")
            
            if status_info["accounts"]:
                click.echo(f"\n已配置账户 ({len(status_info['accounts'])} 个):")
                for account_id, info in status_info["accounts"].items():
                    status_icon = "✓" if info["valid"] else "✗"
                    sandbox_text = " [沙盒]" if info["sandbox"] else ""
                    click.echo(f"  {status_icon} {account_id}{sandbox_text} - {info['description']}")
            else:
                click.echo("\n⚠ 未配置任何账户")
            
            if "server_error" in status_info:
                click.echo(f"\n⚠ 服务器错误: {status_info['server_error']}")
        
    except Exception as e:
        click.echo(f"获取状态失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--json-output', is_flag=True, help='输出JSON格式')
def list(json_output):
    """列出配置的账户"""
    try:
        config_manager = ConfigManager()
        accounts = config_manager.list_accounts()
        
        if not accounts:
            click.echo("未配置任何账户")
            click.echo("使用 'binance-mcp config' 添加账户")
            return
        
        if json_output:
            click.echo(json.dumps(accounts, indent=2, ensure_ascii=False))
        else:
            click.echo(f"已配置账户 ({len(accounts)} 个):")
            for account_id, info in accounts.items():
                sandbox_text = " [沙盒]" if info["sandbox"] else ""
                click.echo(f"  • {account_id}{sandbox_text}")
                if info.get("description"):
                    click.echo(f"    描述: {info['description']}")
                if info.get("created_at"):
                    click.echo(f"    创建时间: {info['created_at']}")
        
    except Exception as e:
        click.echo(f"列出账户失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('account_id')
def test(account_id):
    """测试账户连接"""
    test_connection(account_id)


@cli.command()
@click.argument('account_id')
@click.option('--backup-path', help='备份文件路径')
def backup(account_id, backup_path):
    """备份账户配置"""
    try:
        config_manager = ConfigManager()
        
        if account_id == "all":
            # 备份所有配置
            backup_file = config_manager.backup_config(backup_path)
            click.echo(f"配置已备份到: {backup_file}")
        else:
            # 备份单个账户（需要实现）
            click.echo("单个账户备份功能开发中...")
        
    except Exception as e:
        click.echo(f"备份失败: {e}", err=True)
        sys.exit(1)


# ==================== 辅助函数 ====================

def test_connection(account_id: str):
    """测试账户连接"""
    try:
        config_manager = ConfigManager()
        account_config = config_manager.get_account(account_id)
        
        click.echo(f"测试账户连接: {account_id}")
        click.echo("正在连接...")
        
        # 使用exchange工厂测试连接
        test_result = exchange_factory.test_exchange_connection(account_config)
        
        if test_result["success"]:
            click.echo("✓ 连接成功")
            if test_result["server_time"]:
                click.echo(f"  服务器时间: {test_result['server_time']}")
            if test_result["account_info"]:
                info = test_result["account_info"]
                click.echo(f"  账户币种数: {info['total_currencies']}")
            if test_result["broker_injected"]:
                click.echo("  ✓ Broker ID已注入")
        else:
            click.echo(f"✗ 连接失败: {test_result['error']}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ 测试失败: {e}", err=True)
        sys.exit(1)


def is_server_running(port: int) -> bool:
    """检查服务器是否在指定端口运行"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_pid_file_path(port: int) -> Path:
    """获取PID文件路径"""
    return Path.home() / ".config" / "binance-mcp" / f"mcp_{port}.pid"


def start_daemon(host: str, port: int):
    """以守护进程模式启动服务"""
    import subprocess
    
    # 创建PID文件目录
    pid_file = get_pid_file_path(port)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 启动子进程
    cmd = [sys.executable, "-m", "binance_mcp.cli", "start", 
           "--host", host, "--port", str(port)]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )
    
    # 保存PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    # 等待一下确保启动成功
    time.sleep(2)
    if is_server_running(port):
        click.echo(f"MCP服务已在后台启动 (PID: {process.pid})")
    else:
        click.echo("服务启动失败", err=True)
        pid_file.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()