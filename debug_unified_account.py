#!/usr/bin/env python3
"""
币安统一账户检测和配置工具

检测当前账户是否为统一账户模式，并提供相应的配置建议。
"""

from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager
import ccxt

def detect_unified_account():
    """检测统一账户模式"""
    print("🔍 检测币安统一账户模式")
    print("=" * 50)
    
    config_manager = ConfigManager()
    accounts = config_manager.list_accounts()
    
    if not accounts:
        print("❌ 未配置任何账户")
        return
    
    account_id = list(accounts.keys())[0]
    account_config = config_manager.get_account(account_id)
    
    print(f"📱 检测账户: {account_id}")
    print(f"🌐 环境: {'沙盒' if account_config.get('sandbox') else '生产'}")
    
    # 创建两种模式的exchange实例进行测试
    test_results = {
        "普通账户模式": False,
        "统一账户模式": False
    }
    
    # 1. 测试普通账户模式
    print(f"\n🔍 1. 测试普通账户模式...")
    try:
        normal_exchange = ccxt.binance({
            'apiKey': account_config['api_key'],
            'secret': account_config['secret'],
            'sandbox': account_config.get('sandbox', False),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'portfolioMargin': False
            }
        })
        
        # 尝试获取期货账户余额
        balance = normal_exchange.fetch_balance()
        print("   ✅ 普通期货账户可访问")
        test_results["普通账户模式"] = True
        
    except Exception as e:
        print(f"   ❌ 普通期货账户访问失败: {str(e)[:80]}")
        if "-2015" in str(e):
            print("   💡 可能原因: API权限不足或使用了统一账户模式")
    
    # 2. 测试统一账户模式
    print(f"\n🔍 2. 测试统一账户模式...")
    try:
        unified_exchange = ccxt.binance({
            'apiKey': account_config['api_key'],
            'secret': account_config['secret'],
            'sandbox': account_config.get('sandbox', False),
            'enableRateLimit': True,
            'options': {
                'portfolioMargin': True
            }
        })
        
        # 尝试使用统一账户API获取余额
        balance = unified_exchange.papi_get_balance()
        print("   ✅ 统一账户可访问")
        
        # 解析余额数据
        if isinstance(balance, dict):
            total_balance = balance.get('totalWalletBalance', 'N/A')
        elif isinstance(balance, list) and balance:
            # 如果是列表格式，查找USDT余额
            usdt_info = next((item for item in balance if item.get('asset') == 'USDT'), {})
            total_balance = usdt_info.get('balance', 'N/A')
        else:
            total_balance = 'N/A'
            
        print(f"   💰 账户总余额: {total_balance}")
        test_results["统一账户模式"] = True
        
    except Exception as e:
        print(f"   ❌ 统一账户访问失败: {str(e)[:80]}")
        if "does not exist" in str(e) or "-2015" in str(e):
            print("   💡 可能原因: 未启用统一账户或API权限不足")
    
    # 分析结果
    print(f"\n📊 检测结果:")
    print("=" * 30)
    for mode, success in test_results.items():
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"   {status} {mode}")
    
    # 提供配置建议
    print(f"\n💡 配置建议:")
    print("=" * 30)
    
    if test_results["统一账户模式"]:
        print("🎯 检测到统一账户模式!")
        print("建议配置:")
        print("1. 运行: binance-mcp config")
        print("2. 在配置时添加 portfolio_margin: true")
        print("3. 或者手动修改配置文件，添加:")
        print('   "portfolio_margin": true')
        print()
        print("💰 资金管理:")
        print("统一账户中，所有资产都在同一个账户中")
        print("无需在现货和期货之间转账")
        
        # 显示如何修改现有配置
        print(f"\n🔧 修改现有配置:")
        config_file = config_manager.get_config_path()
        print(f"编辑文件: {config_file}")
        print(f"在账户 '{account_id}' 配置中添加:")
        print(f'    "portfolio_margin": true')
        
    elif test_results["普通账户模式"]:
        print("📋 检测到普通账户模式")
        print("当前配置已正确，无需修改")
        print()
        print("💰 资金管理:")
        print("需要在现货账户和期货账户之间转账")
        print("使用 transfer_funds 工具进行转账")
        
    else:
        print("⚠️  两种模式都无法访问")
        print("可能的问题:")
        print("1. API权限未正确配置")
        print("2. 网络连接问题")
        print("3. API密钥已过期")
        print()
        print("建议操作:")
        print("1. 检查币安API管理页面")
        print("2. 确认权限设置")
        print("3. 检查IP白名单")
    
    # 交易符号说明
    print(f"\n📋 SHIB交易符号说明:")
    print("=" * 30)
    print("现货交易: SHIB/USDT 或 SHIBUSDT")
    print("永续合约: 1000SHIBUSDT (1000倍SHIB)")
    print("价格差异: 永续合约价格约为现货价格的1000倍")

if __name__ == "__main__":
    detect_unified_account()