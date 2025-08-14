#!/usr/bin/env python3
"""
演示所有MCP工具的实际调用
"""

import json
from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager

def demo_mcp_tools():
    print("🎮 Binance MCP 工具演示\n")
    
    # 创建配置管理器和服务器
    config_manager = ConfigManager()
    server = SimpleBinanceMCPServer()
    
    # 获取已配置的账户
    accounts = config_manager.list_accounts()
    if not accounts:
        print("❌ 没有配置的账户，请先运行: binance-mcp config")
        return
    
    account_id = list(accounts.keys())[0]
    print(f"📱 使用账户: {account_id} ({accounts[account_id].get('description', '无描述')})")
    print(f"🏖️  沙盒模式: {'是' if accounts[account_id].get('sandbox') else '否'}")
    print()
    
    # 演示每个工具
    tools_demo = [
        {
            'name': 'get_server_info',
            'description': '📊 获取服务器信息',
            'call': lambda: server.mcp.list_tools() if hasattr(server.mcp, 'list_tools') else server.get_tools_info(),
            'safe': True
        },
        {
            'name': 'get_ticker',
            'description': '💰 获取BTC价格',
            'call': lambda: server.tools.get_ticker('BTC/USDT'),
            'safe': True
        },
        {
            'name': 'get_balance',
            'description': '💳 查看账户余额',
            'call': lambda: server.tools.get_balance(account_id),
            'safe': True
        },
        {
            'name': 'get_open_orders', 
            'description': '📋 查看待成交订单',
            'call': lambda: server.tools.get_open_orders(account_id),
            'safe': True
        },
        {
            'name': 'get_positions',
            'description': '📊 查看持仓信息',
            'call': lambda: server.tools.get_positions(account_id),
            'safe': True
        }
    ]
    
    # 只演示安全的查询工具
    for tool in tools_demo:
        if tool['safe']:
            print(f"\n{tool['description']}")
            print("="*50)
            try:
                result = tool['call']()
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"❌ 调用失败: {e}")
    
    print("\n" + "="*60)
    print("🚨 交易工具演示（仅显示参数，不实际执行）:")
    print("="*60)
    
    trading_tools = [
        {
            'name': 'create_spot_order',
            'description': '💸 创建现货买单',
            'example': f'create_spot_order("{account_id}", "BTC/USDT", "buy", 0.001, "limit", 50000)'
        },
        {
            'name': 'cancel_order',
            'description': '❌ 取消订单',
            'example': f'cancel_order("{account_id}", "order_id_12345", "BTC/USDT")'
        }
    ]
    
    for tool in trading_tools:
        print(f"\n{tool['description']}")
        print(f"示例调用: {tool['example']}")
    
    print(f"\n\n🎯 Claude Code使用示例:")
    print("="*60)
    print('> "帮我查看BTC的当前价格"')
    print('> "查看我的账户余额"') 
    print('> "用0.001个BTC买入ETH"')
    print('> "取消我所有的BTC待成交订单"')
    print(f'> "查看我的持仓情况"')

if __name__ == "__main__":
    demo_mcp_tools()