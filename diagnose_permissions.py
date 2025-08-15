#!/usr/bin/env python3
"""
Binance API权限诊断工具

基于具体的错误码和API端点，准确诊断权限问题
"""

from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager

def diagnose_api_permissions():
    """诊断API权限问题"""
    print("🔍 Binance API权限诊断")
    print("=" * 50)
    
    server = SimpleBinanceMCPServer()
    config_manager = ConfigManager()
    
    accounts = config_manager.list_accounts()
    if not accounts:
        print("❌ 未配置任何账户")
        return
        
    account_id = list(accounts.keys())[0]
    account_info = accounts[account_id]
    
    print(f"📱 诊断账户: {account_id}")
    print(f"🌐 环境: {'🧪 沙盒' if account_info.get('sandbox') else '🏭 生产'}")
    
    # 权限测试结果
    results = {}
    
    # 1. 现货权限测试
    print(f"\n🏪 现货权限测试:")
    print("-" * 30)
    try:
        balance = server.tools.get_balance(account_id, account_type="spot")
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        results['现货'] = {'status': '✅ 正常', 'details': f'USDT余额: {usdt_balance}'}
        print(f"   ✅ 现货权限正常")
        print(f"   💰 USDT余额: {usdt_balance}")
    except Exception as e:
        error_msg = str(e)
        if "-2015" in error_msg:
            results['现货'] = {'status': '❌ 权限缺失', 'details': '需要开启现货交易权限'}
            print(f"   ❌ 现货权限缺失：需要开启现货交易权限")
        elif "-1021" in error_msg:
            results['现货'] = {'status': '❌ 时间同步', 'details': '服务器时间不同步'}
            print(f"   ❌ 时间同步问题：请检查服务器时间")
        else:
            results['现货'] = {'status': '❌ 其他错误', 'details': error_msg[:100]}
            print(f"   ❌ 其他错误: {error_msg}")
    
    # 2. 期货权限测试
    print(f"\n📈 期货权限测试:")
    print("-" * 30)
    try:
        futures_balance = server.tools.get_balance(account_id, account_type="future")
        usdt_balance = futures_balance.get('USDT', {}).get('free', 0)
        results['期货'] = {'status': '✅ 正常', 'details': f'期货USDT余额: {usdt_balance}'}
        print(f"   ✅ 期货权限正常")
        print(f"   💰 期货USDT余额: {usdt_balance}")
    except Exception as e:
        error_msg = str(e)
        if "-2015" in error_msg:
            results['期货'] = {'status': '❌ 权限缺失', 'details': 'API密钥未开启期货交易权限'}
            print(f"   ❌ 期货权限缺失")
            print(f"   💡 解决方案: 在Binance API管理中勾选'期货交易'权限")
        elif "fapi.binance.com" in error_msg:
            results['期货'] = {'status': '❌ 端点访问', 'details': '无法访问期货API端点'}
            print(f"   ❌ 期货API端点访问失败")
        else:
            results['期货'] = {'status': '❌ 其他错误', 'details': error_msg[:100]}
            print(f"   ❌ 其他错误: {error_msg}")
    
    # 3. 期权权限测试（修复后）
    print(f"\n🎯 期权权限测试:")
    print("-" * 30)
    try:
        # 先检查期权市场是否可用
        exchange = server.tools._get_exchange(account_id)
        exchange.options['defaultType'] = 'option'
        
        # 测试期权持仓查询
        option_positions = exchange.fetch_option_positions(None, {})
        results['期权'] = {'status': '✅ 正常', 'details': f'期权持仓: {len(option_positions)}'}
        print(f"   ✅ 期权权限正常")
        print(f"   📊 期权持仓数量: {len(option_positions)}")
    except Exception as e:
        error_msg = str(e)
        if "-2015" in error_msg:
            results['期权'] = {'status': '❌ 权限缺失', 'details': 'API密钥未开启期权交易权限'}
            print(f"   ❌ 期权权限缺失")
            print(f"   💡 解决方案: 在Binance API管理中勾选'期权交易'权限")
        elif "does not support" in error_msg.lower():
            results['期权'] = {'status': '❌ 不支持', 'details': 'Binance可能不支持期权或地区限制'}
            print(f"   ❌ 期权交易不支持")
            print(f"   💡 说明: 可能是地区限制或Binance不提供期权服务")
        else:
            results['期权'] = {'status': '❌ 其他错误', 'details': error_msg[:100]}
            print(f"   ❌ 其他错误: {error_msg}")
    
    # 4. IP白名单检查
    print(f"\n🌐 网络连接测试:")
    print("-" * 30)
    try:
        # 通过公开API检查网络连接
        ticker = server.tools.get_ticker("BTCUSDT")
        print(f"   ✅ 网络连接正常")
        print(f"   💰 BTC价格: ${float(ticker['last']):,.2f}")
        
        # 检查是否有IP限制相关的错误
        current_ip_issues = any('-2015' in str(result.get('details', '')) for result in results.values())
        if current_ip_issues:
            print(f"   ⚠️  检测到-2015错误，可能的原因：")
            print(f"      1. API权限未正确配置")
            print(f"      2. IP白名单限制（如果设置了的话）")
            print(f"      3. API密钥过期或无效")
    except Exception as e:
        print(f"   ❌ 网络连接有问题: {e}")
    
    # 权限诊断总结
    print(f"\n📊 权限诊断总结:")
    print("=" * 40)
    for service, result in results.items():
        print(f"   {result['status']} {service}: {result['details']}")
    
    # 具体的修复建议
    print(f"\n🔧 修复建议:")
    print("=" * 40)
    
    failed_services = [name for name, result in results.items() if '❌' in result['status']]
    
    if failed_services:
        print(f"📋 需要处理的服务: {', '.join(failed_services)}")
        print(f"\n步骤1: 检查API权限配置")
        print(f"   1. 登录 Binance 账户")
        print(f"   2. 进入 [API管理] -> [编辑API]")
        print(f"   3. 确认以下权限已勾选：")
        if '现货' in failed_services:
            print(f"      ☑️  启用现货与杠杆交易")
        if '期货' in failed_services:
            print(f"      ☑️  启用期货交易")
        if '期权' in failed_services:
            print(f"      ☑️  启用期权交易（如果可用）")
        
        print(f"\n步骤2: 检查IP限制")
        print(f"   - 如果设置了IP白名单，确认当前IP在列表中")
        print(f"   - 或者临时移除IP限制进行测试")
        
        print(f"\n步骤3: 重新配置API密钥")
        print(f"   - 如果权限已正确设置但仍然失败，可能需要重新配置：")
        print(f"   - 运行: binance-mcp config")
        
    else:
        print(f"🎉 所有权限检查通过！您的API配置正确。")
    
    # 错误码参考
    print(f"\n📚 Binance错误码参考:")
    print("=" * 40)
    print(f"   -2015: API权限不足或IP限制")
    print(f"   -1021: 时间戳不在允许范围内")  
    print(f"   -1022: 签名无效")
    print(f"   -2010: 账户余额不足")
    print(f"   -1007: 超时等待服务器响应")

if __name__ == "__main__":
    diagnose_api_permissions()