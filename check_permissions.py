#!/usr/bin/env python3
"""
Binance API权限检查工具

检查当前配置的API密钥具有哪些权限，并提供权限配置指导。
"""

from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager

def check_api_permissions():
    """检查API权限"""
    print("🔐 Binance API权限检查")
    print("=" * 50)
    
    try:
        server = SimpleBinanceMCPServer()
        config_manager = ConfigManager()
        
        # 获取账户列表
        accounts = config_manager.list_accounts()
        if not accounts:
            print("❌ 未配置任何账户，请先运行: binance-mcp config")
            return
            
        account_id = list(accounts.keys())[0]
        account_info = accounts[account_id]
        
        print(f"📱 检查账户: {account_id}")
        print(f"🌐 环境: {'沙盒' if account_info.get('sandbox') else '生产'}")
        print()
        
        # 权限检查结果
        permissions = {
            "现货交易": False,
            "期货交易": False,
            "期权交易": False,
            "资金划转": False,
            "账户查询": False
        }
        
        # 1. 检查基础账户查询权限
        print("🔍 1. 检查基础账户权限...")
        try:
            balance = server.tools.get_balance(account_id, account_type="spot")
            print("   ✅ 现货账户查询 - 正常")
            permissions["账户查询"] = True
            permissions["现货交易"] = True
        except Exception as e:
            print(f"   ❌ 现货账户查询失败: {str(e)[:80]}")
        
        # 2. 检查期货权限
        print("🔍 2. 检查期货交易权限...")
        try:
            futures_balance = server.tools.get_balance(account_id, account_type="future")
            print("   ✅ 期货账户查询 - 正常")
            permissions["期货交易"] = True
        except Exception as e:
            print(f"   ❌ 期货账户查询失败: {str(e)[:80]}")
            if "-2015" in str(e):
                print("   💡 建议：需要在Binance开启期货交易权限")
        
        # 3. 检查期权权限
        print("🔍 3. 检查期权交易权限...")
        try:
            option_positions = server.tools.get_option_positions(account_id)
            print("   ✅ 期权账户查询 - 正常")
            permissions["期权交易"] = True
        except Exception as e:
            print(f"   ❌ 期权账户查询失败: {str(e)[:80]}")
            if "-2015" in str(e):
                print("   💡 建议：需要在Binance开启期权交易权限")
        
        # 4. 检查市场数据权限（公开数据）
        print("🔍 4. 检查市场数据权限...")
        try:
            ticker = server.tools.get_ticker("BTCUSDT")
            print("   ✅ 市场数据查询 - 正常")
        except Exception as e:
            print(f"   ❌ 市场数据查询失败: {str(e)[:80]}")
        
        # 权限总结
        print("\n📊 权限检查总结:")
        print("=" * 30)
        for perm, status in permissions.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {perm}")
        
        # 提供权限配置指导
        if not all(permissions.values()):
            print("\n💡 权限配置指导:")
            print("=" * 30)
            print("1. 登录 Binance 账户")
            print("2. 进入 [API管理] 页面")
            print("3. 编辑现有API密钥或创建新的API密钥")
            print("4. 确保勾选以下权限：")
            if not permissions["现货交易"]:
                print("   - 🟡 启用现货与杠杆交易")
            if not permissions["期货交易"]:  
                print("   - 🟡 启用期货交易")
            if not permissions["期权交易"]:
                print("   - 🟡 启用期权交易")
            print("5. 保存并重新配置API密钥")
            print("6. 重新运行测试")
            
        print("\n🔒 安全提醒:")
        print("   - 只授予必要的权限")
        print("   - 定期轮换API密钥")
        print("   - 设置IP白名单限制")
        print("   - 不要分享API密钥")
            
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_api_permissions()