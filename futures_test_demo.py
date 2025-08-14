#!/usr/bin/env python3
"""
期货交易功能演示脚本

由于API权限限制，这里演示期货交易的调用方式和参数格式，
以及如何正确使用合约交易工具。
"""

from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager
import json

def demonstrate_futures_trading():
    """演示期货交易功能"""
    print("📈 Binance期货交易功能演示")
    print("=" * 50)
    
    server = SimpleBinanceMCPServer()
    config_manager = ConfigManager()
    
    accounts = config_manager.list_accounts()
    if not accounts:
        print("❌ 未配置账户")
        return
        
    account_id = list(accounts.keys())[0]
    
    # 演示参数配置
    test_params = {
        "account_id": account_id,
        "symbol": "SHIBUSDT",  # 注意：期货使用这种格式
        "trade_amount_usd": 10,
        "leverage": 3
    }
    
    print(f"🎯 演示参数:")
    print(f"   账户ID: {test_params['account_id']}")
    print(f"   交易对: {test_params['symbol']} (期货格式)")
    print(f"   交易金额: ${test_params['trade_amount_usd']}")
    print(f"   杠杆倍数: {test_params['leverage']}x")
    
    # 1. 获取期货价格
    print("\n📊 1. 获取期货价格...")
    try:
        ticker = server.tools.get_ticker(test_params['symbol'])
        price = float(ticker['last'])
        print(f"   ✅ {test_params['symbol']} 期货价格: ${price:.6f}")
        
        # 计算交易数量
        amount = int(test_params['trade_amount_usd'] / price)
        print(f"   💹 计算交易数量: {amount:,} SHIB")
        
    except Exception as e:
        print(f"   ❌ 获取价格失败: {e}")
        return
    
    # 2. 演示期货开多单
    print("\n📈 2. 演示期货开多单调用...")
    futures_order_params = {
        "account_id": test_params['account_id'],
        "symbol": test_params['symbol'],
        "side": "buy",  # 开多
        "amount": amount,
        "order_type": "market",
        "contract_type": "future"
    }
    
    print("   🔧 调用参数:")
    for key, value in futures_order_params.items():
        print(f"     {key}: {value}")
        
    print("   📝 实际调用代码:")
    print(f"     server.tools.create_contract_order(**{json.dumps(futures_order_params, indent=6)})")
    
    # 由于权限限制，不实际执行
    print("   ⚠️  由于API权限限制，这里不执行真实交易")
    print("   💡 需要在Binance开启期货交易权限后才能实际执行")
    
    # 3. 演示杠杆设置
    print("\n⚙️  3. 演示杠杆设置...")
    leverage_params = {
        "account_id": test_params['account_id'],
        "symbol": test_params['symbol'],
        "leverage": test_params['leverage']
    }
    
    print("   🔧 调用参数:")
    for key, value in leverage_params.items():
        print(f"     {key}: {value}")
        
    print("   📝 实际调用代码:")
    print(f"     server.tools.set_leverage(**{json.dumps(leverage_params, indent=6)})")
    
    # 4. 演示一键平仓
    print("\n🔄 4. 演示一键平仓...")
    close_params = {
        "account_id": test_params['account_id'],
        "symbol": test_params['symbol'],
        "side": None  # 平所有方向的仓位
    }
    
    print("   🔧 调用参数:")
    for key, value in close_params.items():
        print(f"     {key}: {value}")
        
    print("   📝 实际调用代码:")
    print(f"     server.tools.close_position(**{json.dumps(close_params, indent=6)})")
    
    # 5. 期货与现货的区别总结
    print("\n📋 期货与现货交易区别:")
    print("=" * 30)
    
    comparison = {
        "Symbol格式": {
            "现货": "SHIB/USDT 或 SHIBUSDT",
            "期货": "SHIBUSDT (无斜杠)"
        },
        "API权限": {
            "现货": "现货与杠杆交易权限",
            "期货": "期货交易权限"
        },
        "交易方式": {
            "现货": "实物交割",
            "期货": "合约交易，支持杠杆"
        },
        "工具函数": {
            "现货": "create_spot_order()",
            "期货": "create_contract_order()"
        },
        "特有功能": {
            "现货": "无杠杆风险",
            "期货": "杠杆设置、一键平仓、持仓查询"
        }
    }
    
    for category, details in comparison.items():
        print(f"\n🔸 {category}:")
        for key, value in details.items():
            print(f"   {key}: {value}")
    
    # 6. 完整期货交易流程示例
    print("\n🎯 完整期货交易流程示例:")
    print("=" * 40)
    
    workflow = [
        "1️⃣  设置杠杆: set_leverage(account_id, symbol, leverage)",
        "2️⃣  获取价格: get_ticker(symbol)",  
        "3️⃣  开仓交易: create_contract_order(account_id, symbol, side, amount)",
        "4️⃣  查看持仓: get_futures_positions(account_id, [symbol])",
        "5️⃣  监控盈亏: 定期检查持仓状态",
        "6️⃣  平仓操作: close_position(account_id, symbol)"
    ]
    
    for step in workflow:
        print(f"   {step}")
    
    print("\n✅ 期货交易功能演示完成!")
    print("💡 要进行真实期货交易，请先开启相应的API权限")

if __name__ == "__main__":
    demonstrate_futures_trading()