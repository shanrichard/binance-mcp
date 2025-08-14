#!/usr/bin/env python3
"""
列出所有MCP工具的详细信息
"""

import json
from binance_mcp.simple_server import SimpleBinanceMCPServer

def list_all_tools():
    print("🔧 Binance MCP 工具列表\n")
    
    # 创建服务器实例
    server = SimpleBinanceMCPServer()
    
    # 获取工具信息
    tools_info = server.get_tools_info()
    
    print(f"📊 总计: {tools_info['total_tools']} 个工具\n")
    
    # 定义工具的详细信息
    tool_details = {
        # 原有核心工具
        'create_spot_order': {
            'description': '创建现货订单',
            'category': '🏪 现货交易',
            'params': ['account_id', 'symbol', 'side', 'amount', 'order_type?', 'price?'],
            'example': 'create_spot_order("main", "BTC/USDT", "buy", 0.001, "limit", 50000)',
        },
        'cancel_order': {
            'description': '取消订单',
            'category': '📋 订单管理',
            'params': ['account_id', 'order_id', 'symbol'],
            'example': 'cancel_order("main", "12345", "BTC/USDT")',
        },
        'get_balance': {
            'description': '获取账户余额',
            'category': '💰 账户查询',
            'params': ['account_id'],
            'example': 'get_balance("main")',
        },
        'get_ticker': {
            'description': '获取价格行情',
            'category': '📊 市场数据',
            'params': ['symbol'],
            'example': 'get_ticker("BTC/USDT")',
        },
        'get_positions': {
            'description': '获取持仓信息',
            'category': '📋 持仓管理',
            'params': ['account_id', 'symbol?'],
            'example': 'get_positions("futures", "BTC/USDT")',
        },
        'get_open_orders': {
            'description': '获取开放订单',
            'category': '📋 订单管理',
            'params': ['account_id', 'symbol?'],
            'example': 'get_open_orders("main", "BTC/USDT")',
        },
        
        # 高级订单类型
        'create_stop_loss_order': {
            'description': '创建止损订单',
            'category': '🛡️ 风险控制',
            'params': ['account_id', 'symbol', 'side', 'amount', 'stop_price'],
            'example': 'create_stop_loss_order("main", "BTC/USDT", "sell", 0.001, 48000)',
        },
        'create_take_profit_order': {
            'description': '创建止盈订单',
            'category': '🛡️ 风险控制',
            'params': ['account_id', 'symbol', 'side', 'amount', 'take_profit_price'],
            'example': 'create_take_profit_order("main", "BTC/USDT", "sell", 0.001, 52000)',
        },
        'create_stop_limit_order': {
            'description': '创建止损限价订单',
            'category': '🛡️ 风险控制',
            'params': ['account_id', 'symbol', 'side', 'amount', 'stop_price', 'limit_price'],
            'example': 'create_stop_limit_order("main", "BTC/USDT", "sell", 0.001, 48000, 47500)',
        },
        'create_trailing_stop_order': {
            'description': '创建追踪止损订单',
            'category': '🛡️ 风险控制',
            'params': ['account_id', 'symbol', 'side', 'amount', 'trail_percent'],
            'example': 'create_trailing_stop_order("main", "BTC/USDT", "sell", 0.001, 0.05)',
        },
        'create_oco_order': {
            'description': '创建OCO订单',
            'category': '🛡️ 风险控制',
            'params': ['account_id', 'symbol', 'side', 'amount', 'price', 'stop_price', 'stop_limit_price?'],
            'example': 'create_oco_order("main", "BTC/USDT", "sell", 0.001, 52000, 48000)',
        },
        
        # 市场数据
        'get_order_book': {
            'description': '获取订单簿深度',
            'category': '📊 市场数据',
            'params': ['symbol', 'limit?'],
            'example': 'get_order_book("BTC/USDT", 100)',
        },
        'get_klines': {
            'description': '获取K线数据',
            'category': '📊 市场数据',
            'params': ['symbol', 'timeframe?', 'since?', 'limit?'],
            'example': 'get_klines("BTC/USDT", "1h", None, 100)',
        },
        'get_funding_rate': {
            'description': '获取资金费率',
            'category': '📊 市场数据',
            'params': ['symbol'],
            'example': 'get_funding_rate("BTC/USDT")',
        },
        
        # 期权交易
        'create_option_order': {
            'description': '创建期权订单',
            'category': '🎯 期权交易',
            'params': ['account_id', 'symbol', 'side', 'amount', 'price?', 'option_type?'],
            'example': 'create_option_order("option", "BTC-240315-45000-C", "buy", 1)',
        },
        'get_option_chain': {
            'description': '获取期权链',
            'category': '🎯 期权交易',
            'params': ['underlying'],
            'example': 'get_option_chain("BTC")',
        },
        'get_option_positions': {
            'description': '获取期权持仓',
            'category': '🎯 期权交易',
            'params': ['account_id'],
            'example': 'get_option_positions("option")',
        },
        'get_option_info': {
            'description': '获取期权合约信息',
            'category': '🎯 期权交易',
            'params': ['symbol'],
            'example': 'get_option_info("BTC-240315-45000-C")',
        },
        
        # 合约/期货交易
        'create_contract_order': {
            'description': '创建合约订单',
            'category': '📈 合约交易',
            'params': ['account_id', 'symbol', 'side', 'amount', 'order_type?', 'price?', 'contract_type?'],
            'example': 'create_contract_order("futures", "BTC/USDT", "buy", 0.01)',
        },
        'close_position': {
            'description': '一键平仓',
            'category': '📈 合约交易',
            'params': ['account_id', 'symbol', 'side?'],
            'example': 'close_position("futures", "BTC/USDT")',
        },
        'get_futures_positions': {
            'description': '获取期货持仓详情',
            'category': '📈 合约交易',
            'params': ['account_id', 'symbols?'],
            'example': 'get_futures_positions("futures")',
        },
        
        # 订单管理
        'get_order_status': {
            'description': '查询单个订单状态',
            'category': '📋 订单管理',
            'params': ['account_id', 'order_id', 'symbol'],
            'example': 'get_order_status("main", "12345", "BTC/USDT")',
        },
        'get_my_trades': {
            'description': '获取成交记录',
            'category': '📋 订单管理',
            'params': ['account_id', 'symbol?', 'since?', 'limit?'],
            'example': 'get_my_trades("main", "BTC/USDT")',
        },
        'cancel_all_orders': {
            'description': '批量取消订单',
            'category': '📋 订单管理',
            'params': ['account_id', 'symbol?'],
            'example': 'cancel_all_orders("main", "BTC/USDT")',
        },
        
        # 账户设置
        'set_leverage': {
            'description': '设置杠杆倍数',
            'category': '⚙️ 账户设置',
            'params': ['account_id', 'symbol', 'leverage'],
            'example': 'set_leverage("futures", "BTC/USDT", 10)',
        },
        'set_margin_mode': {
            'description': '设置保证金模式',
            'category': '⚙️ 账户设置',
            'params': ['account_id', 'symbol', 'margin_mode'],
            'example': 'set_margin_mode("futures", "BTC/USDT", "cross")',
        },
        'transfer_funds': {
            'description': '账户间转账',
            'category': '⚙️ 账户设置',
            'params': ['account_id', 'currency', 'amount', 'from_account', 'to_account'],
            'example': 'transfer_funds("main", "USDT", 1000, "spot", "future")',
        },
        
        # 系统工具
        'get_server_info': {
            'description': '获取服务器信息',
            'category': 'ℹ️ 系统信息',
            'params': [],
            'example': 'get_server_info()',
        }
    }
    
    # 按类别分组打印工具
    categories = {}
    for tool_name in tools_info['tools']:
        if tool_name in tool_details:
            detail = tool_details[tool_name]
            category = detail['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((tool_name, detail))
    
    # 打印每个类别的工具
    for category, tools in categories.items():
        print(f"\n{category}")
        print("=" * 50)
        for i, (tool_name, detail) in enumerate(tools, 1):
            print(f"{i}. 🛠️  {tool_name}")
            print(f"   描述: {detail['description']}")
            print(f"   参数: {', '.join(detail['params'])}")
            print(f"   示例: {detail['example']}")
            print()
    
    # 统计信息
    print("=" * 50)
    print(f"📊 功能统计:")
    for category, tools in categories.items():
        print(f"   {category}: {len(tools)}个工具")
    print(f"\n🎯 总计: {len(tools_info['tools'])} 个交易工具，覆盖现货、期货、期权全链路交易！")

if __name__ == "__main__":
    list_all_tools()