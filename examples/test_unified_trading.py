#!/usr/bin/env python3
"""
统一账户交易测试

测试统一账户模式下的SHIB永续合约交易功能
"""

from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager
import ccxt

def test_unified_trading():
    """测试统一账户交易功能"""
    print("🎯 统一账户交易测试")
    print("=" * 50)
    
    config_manager = ConfigManager()
    accounts = config_manager.list_accounts()
    
    if not accounts:
        print("❌ 未配置账户")
        return
    
    account_id = list(accounts.keys())[0]
    account_config = config_manager.get_account(account_id)
    
    print(f"📱 测试账户: {account_id}")
    print(f"🎛️  统一账户: {'✅ 已启用' if account_config.get('portfolio_margin') else '❌ 未启用'}")
    
    # 创建统一账户exchange
    exchange = ccxt.binance({
        'apiKey': account_config['api_key'],
        'secret': account_config['secret'],
        'sandbox': account_config.get('sandbox', False),
        'enableRateLimit': True,
        'options': {
            'portfolioMargin': True,
            'broker': {
                'spot': 'C96E9MGA',
                'future': 'eFC56vBf',
                'delivery': 'eFC56vBf',
                'option': 'eFC56vBf',
                'swap': 'eFC56vBf',
            }
        }
    })
    
    # 1. 测试统一账户余额查询
    print(f"\n💰 1. 查询统一账户余额...")
    try:
        # 使用Portfolio Margin API
        balance = exchange.papi_get_balance()
        
        print(f"   ✅ 余额查询成功")
        if isinstance(balance, list):
            for asset in balance:
                if asset.get('asset') == 'USDT' and float(asset.get('balance', 0)) > 0:
                    print(f"   💵 USDT余额: {asset.get('balance')}")
                    print(f"   🔓 可用余额: {asset.get('availableBalance', 'N/A')}")
                    break
        else:
            print(f"   📊 总钱包余额: {balance.get('totalWalletBalance', 'N/A')}")
            
    except Exception as e:
        print(f"   ❌ 余额查询失败: {e}")
        return
    
    # 2. 测试SHIB永续合约价格获取
    print(f"\n📈 2. 获取SHIB永续合约价格...")
    try:
        # 测试1000SHIB合约
        ticker = exchange.fetch_ticker('1000SHIBUSDT')
        price = float(ticker['last'])
        print(f"   ✅ 1000SHIBUSDT 价格: ${price:.6f}")
        
        # 计算10U能买多少合约
        trade_amount_usd = 10
        contracts = int(trade_amount_usd / price)
        print(f"   💹 ${trade_amount_usd} 可买 {contracts:,} 张合约")
        
        return price, contracts
        
    except Exception as e:
        print(f"   ❌ 价格获取失败: {e}")
        return None, None
    
def test_portfolio_margin_order():
    """测试统一账户下单功能"""
    print(f"\n📋 3. 测试统一账户下单功能...")
    
    # 使用MCP工具测试
    server = SimpleBinanceMCPServer()
    config_manager = ConfigManager()
    
    accounts = config_manager.list_accounts()
    account_id = list(accounts.keys())[0]
    
    try:
        # 测试获取1000SHIB价格
        ticker = server.tools.get_ticker('1000SHIBUSDT')
        price = float(ticker['last'])
        print(f"   📊 通过MCP获取价格: ${price:.6f}")
        
        # 测试获取账户余额（应该使用统一账户API）
        balance = server.tools.get_balance(account_id, account_type="future")
        print(f"   💰 期货账户余额查询: {'成功' if balance else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MCP工具测试失败: {str(e)[:100]}")
        if "-2015" in str(e):
            print(f"   💡 仍然遇到-2015错误，说明MCP工具还没有使用统一账户API")
        return False

def main():
    """主测试函数"""
    print("🚀 开始统一账户交易系统测试")
    print("=" * 60)
    
    # 测试直接API调用
    price, contracts = test_unified_trading()
    
    if price and contracts:
        # 测试MCP工具
        mcp_success = test_portfolio_margin_order()
        
        print(f"\n📊 测试结果汇总:")
        print("=" * 40)
        print(f"   ✅ 统一账户API: 可正常使用")
        print(f"   📈 1000SHIBUSDT价格: ${price:.6f}")
        print(f"   💹 10U可买合约数: {contracts:,}张")
        print(f"   {'✅' if mcp_success else '❌'} MCP工具兼容: {'正常' if mcp_success else '需要更新'}")
        
        if not mcp_success:
            print(f"\n🔧 下一步行动:")
            print(f"   1. 更新MCP工具以支持统一账户API")
            print(f"   2. 修改get_balance工具使用papi接口")
            print(f"   3. 更新create_contract_order工具")
    else:
        print(f"\n❌ 基础测试失败，无法继续")

if __name__ == "__main__":
    main()