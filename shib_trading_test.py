#!/usr/bin/env python3
"""
SHIB交易测试脚本

测试现货和合约交易功能：
1. 现货买入10U的SHIB
2. 合约开多10U的SHIB
3. 等待一段时间观察
4. 平掉所有仓位

⚠️ 风险提醒：这是真实交易，会产生实际的盈亏！
"""

import asyncio
import time
from decimal import Decimal
from binance_mcp.simple_server import SimpleBinanceMCPServer
from binance_mcp.config import ConfigManager

class SHIBTradingTest:
    def __init__(self):
        self.server = SimpleBinanceMCPServer()
        self.config_manager = ConfigManager()
        self.symbol = "SHIBUSDT"
        self.trade_amount_usd = 10  # 10 USDT
        
    def get_account_info(self):
        """获取账户信息"""
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("❌ 未配置任何交易账户，请先运行: binance-mcp config")
        
        print(f"📱 已配置账户: {list(accounts.keys())}")
        
        # 查找合适的账户
        spot_account = None
        futures_account = None
        
        for account_id, account_info in accounts.items():
            if 'spot' in account_id.lower() or 'main' in account_id.lower():
                spot_account = account_id
            if 'future' in account_id.lower() or 'contract' in account_id.lower():
                futures_account = account_id
                
        # 如果没有明确的分类，使用第一个账户
        if not spot_account:
            spot_account = list(accounts.keys())[0]
        if not futures_account:
            futures_account = list(accounts.keys())[0]
            
        return spot_account, futures_account
    
    def get_shib_price(self):
        """获取SHIB当前价格"""
        try:
            ticker = self.server.tools.get_ticker(self.symbol)
            price = float(ticker['last'])
            print(f"📊 {self.symbol} 当前价格: ${price:.6f}")
            return price
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return None
    
    def calculate_shib_amount(self, price, usd_amount):
        """计算SHIB数量"""
        if not price:
            return None
        amount = usd_amount / price
        # SHIB通常需要整数数量，向下取整
        return int(amount)
    
    def check_balance(self, account_id, currency="USDT"):
        """检查余额"""
        try:
            balance = self.server.tools.get_balance(account_id)
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            print(f"💰 账户 {account_id} USDT余额: {usdt_balance}")
            return float(usdt_balance)
        except Exception as e:
            print(f"❌ 获取余额失败: {e}")
            return 0
    
    def spot_trade_test(self, account_id):
        """现货交易测试"""
        print("\n🏪 开始现货交易测试...")
        print("=" * 50)
        
        # 检查余额
        balance = self.check_balance(account_id)
        if balance < self.trade_amount_usd:
            print(f"❌ USDT余额不足: {balance} < {self.trade_amount_usd}")
            return None
        
        # 获取价格和计算数量
        price = self.get_shib_price()
        if not price:
            return None
            
        shib_amount = self.calculate_shib_amount(price, self.trade_amount_usd)
        print(f"💹 准备买入 {shib_amount:,} SHIB (约${self.trade_amount_usd})")
        
        try:
            # 市价买入SHIB
            order = self.server.tools.create_spot_order(
                account_id=account_id,
                symbol=self.symbol,
                side="buy",
                amount=shib_amount,
                order_type="market"
            )
            
            print(f"✅ 现货买单成功!")
            print(f"   订单ID: {order.get('id', 'N/A')}")
            print(f"   状态: {order.get('status', 'N/A')}")
            print(f"   数量: {order.get('amount', 'N/A')}")
            
            return order
            
        except Exception as e:
            print(f"❌ 现货买入失败: {e}")
            return None
    
    def futures_trade_test(self, account_id):
        """合约交易测试"""
        print("\n📈 开始合约交易测试...")
        print("=" * 50)
        
        # 检查余额
        balance = self.check_balance(account_id)
        if balance < self.trade_amount_usd:
            print(f"❌ USDT余额不足: {balance} < {self.trade_amount_usd}")
            return None
        
        # 获取价格和计算数量
        price = self.get_shib_price()
        if not price:
            return None
            
        shib_amount = self.calculate_shib_amount(price, self.trade_amount_usd)
        print(f"💹 准备开多 {shib_amount:,} SHIB (约${self.trade_amount_usd})")
        
        try:
            # 期货开多单
            order = self.server.tools.create_contract_order(
                account_id=account_id,
                symbol=self.symbol,
                side="buy",
                amount=shib_amount,
                order_type="market",
                contract_type="future"
            )
            
            print(f"✅ 合约开多成功!")
            print(f"   订单ID: {order.get('id', 'N/A')}")
            print(f"   状态: {order.get('status', 'N/A')}")
            print(f"   数量: {order.get('amount', 'N/A')}")
            
            return order
            
        except Exception as e:
            print(f"❌ 合约开多失败: {e}")
            return None
    
    def check_positions(self, account_id):
        """检查持仓"""
        try:
            positions = self.server.tools.get_futures_positions(account_id, [self.symbol])
            for pos in positions:
                if pos.get('contracts', 0) > 0:
                    print(f"📊 持仓: {pos.get('contracts')} SHIB")
                    print(f"   盈亏: ${pos.get('unrealizedPnl', 'N/A')}")
                    print(f"   开仓价: ${pos.get('markPrice', 'N/A')}")
        except Exception as e:
            print(f"⚠️  检查持仓失败: {e}")
    
    def close_all_positions(self, spot_account, futures_account):
        """平仓所有仓位"""
        print("\n🔄 开始平仓操作...")
        print("=" * 50)
        
        # 平掉现货（卖出SHIB）
        try:
            balance = self.server.tools.get_balance(spot_account)
            shib_balance = balance.get('SHIB', {}).get('free', 0)
            if float(shib_balance) > 0:
                print(f"💸 卖出现货SHIB: {shib_balance}")
                sell_order = self.server.tools.create_spot_order(
                    account_id=spot_account,
                    symbol=self.symbol,
                    side="sell",
                    amount=float(shib_balance),
                    order_type="market"
                )
                print(f"✅ 现货卖单成功: {sell_order.get('id', 'N/A')}")
            else:
                print("ℹ️  无现货SHIB需要卖出")
        except Exception as e:
            print(f"❌ 现货平仓失败: {e}")
        
        # 平掉合约仓位
        try:
            print("🔄 平掉合约仓位...")
            close_result = self.server.tools.close_position(
                account_id=futures_account,
                symbol=self.symbol
            )
            if close_result.get('closed_positions'):
                print(f"✅ 合约平仓成功: {len(close_result['closed_positions'])} 个仓位")
                for pos in close_result['closed_positions']:
                    print(f"   平仓订单: {pos.get('id', 'N/A')}")
            else:
                print("ℹ️  无合约仓位需要平仓")
        except Exception as e:
            print(f"❌ 合约平仓失败: {e}")
    
    def run_trading_test(self):
        """运行完整的交易测试"""
        print("🚀 开始SHIB交易测试")
        print("=" * 60)
        print("⚠️  警告：这将进行真实交易，请确认您已了解风险！")
        print("=" * 60)
        
        try:
            # 获取账户信息
            spot_account, futures_account = self.get_account_info()
            print(f"📱 现货账户: {spot_account}")
            print(f"📊 合约账户: {futures_account}")
            
            # 获取初始价格
            initial_price = self.get_shib_price()
            if not initial_price:
                print("❌ 无法获取SHIB价格，测试终止")
                return
            
            # 执行现货交易
            spot_order = self.spot_trade_test(spot_account)
            
            # 执行合约交易
            futures_order = self.futures_trade_test(futures_account)
            
            if not spot_order and not futures_order:
                print("❌ 所有交易都失败了，测试终止")
                return
            
            # 等待10秒观察价格变化
            print(f"\n⏰ 等待10秒观察价格变化...")
            time.sleep(10)
            
            # 检查最新价格
            current_price = self.get_shib_price()
            if current_price and initial_price:
                price_change = ((current_price - initial_price) / initial_price) * 100
                print(f"📊 价格变化: {price_change:.2f}%")
            
            # 检查持仓
            if futures_order:
                self.check_positions(futures_account)
            
            # 平仓所有仓位
            self.close_all_positions(spot_account, futures_account)
            
            print("\n🎉 SHIB交易测试完成!")
            
        except Exception as e:
            print(f"❌ 交易测试失败: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    test = SHIBTradingTest()
    
    # 显示交易测试信息
    print("🔔 开始SHIB交易测试!")
    print("   - 现货买入约10 USDT的SHIB")
    print("   - 合约开多约10 USDT的SHIB") 
    print("   - 等待10秒后全部平仓")
    print("   - ⚠️  这是真实交易，会产生实际盈亏！")
    
    test.run_trading_test()

if __name__ == "__main__":
    main()