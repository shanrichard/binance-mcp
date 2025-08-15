"""
MCP工具实现模块

定义了所有可供AI agents调用的MCP工具，包括：
- 交易操作工具（创建、取消、编辑订单）
- 账户查询工具（余额、持仓、订单、交易记录）
- 市场数据工具（价格、深度、K线）
- 设置管理工具（杠杆、保证金模式、转账）

所有工具都直接基于ccxt进行封装，保持原始功能和错误信息。
"""

import logging
from typing import Dict, Any, Optional, List
from functools import wraps
import ccxt

from .config import ConfigManager
from .broker import exchange_factory

logger = logging.getLogger(__name__)


def handle_ccxt_error(func):
    """
    装饰器：统一处理ccxt错误
    
    保持原始错误类型和消息，添加MCP上下文信息用于调试
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ccxt.BaseError as e:
            # 记录错误上下文用于调试
            error_context = {
                'tool_name': func.__name__,
                'account_id': kwargs.get('account_id'),
                'symbol': kwargs.get('symbol'),
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            logger.error(f"CCXT error in {func.__name__}: {error_context}")
            
            # 直接重新抛出原始异常，保持ccxt的错误处理逻辑
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise RuntimeError(f"工具执行失败: {e}")
    
    return wrapper


class BinanceMCPTools:
    """Binance MCP工具集合"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化MCP工具
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self._exchange_cache = {}  # 缓存exchange实例
    
    def _get_exchange(self, account_id: str) -> ccxt.binance:
        """
        获取指定账户的exchange实例（带缓存）
        
        Args:
            account_id: 账户ID
            
        Returns:
            ccxt.binance实例
            
        Raises:
            ValueError: 账户不存在时
        """
        if account_id not in self._exchange_cache:
            account_config = self.config_manager.get_account(account_id)
            exchange = exchange_factory.create_exchange(account_config)
            self._exchange_cache[account_id] = exchange
        
        return self._exchange_cache[account_id]
    
    def _create_spot_only_exchange(self, account_config: Dict[str, Any]) -> ccxt.binance:
        """
        创建专门用于现货的exchange实例（不使用portfolioMargin配置）
        
        Args:
            account_config: 账户配置
            
        Returns:
            专门用于现货的ccxt.binance实例
        """
        return ccxt.binance({
            'apiKey': account_config['api_key'],
            'secret': account_config['secret'],
            'sandbox': account_config.get('sandbox', False),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'broker': {
                    'spot': 'C96E9MGA',  # 现货broker ID
                },
                # 重要：不设置portfolioMargin，让现货使用标准API
            }
        })
    
    # ==================== 交易操作工具 ====================
    
    @handle_ccxt_error
    def create_spot_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "limit",
        price: Optional[float] = None,
        **params
    ) -> Dict[str, Any]:
        """
        创建现货订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对 (如 "BTC/USDT")
            side: 买卖方向 ("buy" | "sell")
            amount: 数量
            order_type: 订单类型 ("limit" | "market" | "stop_limit" 等)
            price: 价格 (市价单可为None)
            **params: 其他参数透传给ccxt
            
        Returns:
            订单信息字典
        """
        exchange = self._get_exchange(account_id)
        
        # 确保在现货市场
        exchange.options['defaultType'] = 'spot'
        
        return exchange.create_order(symbol, order_type, side, amount, price, params)
    
    @handle_ccxt_error 
    def create_futures_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "limit",
        price: Optional[float] = None,
        **params
    ) -> Dict[str, Any]:
        """
        创建期货订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对 (如 "1000SHIBUSDT" 永续合约)
            side: 买卖方向 ("buy" | "sell")
            amount: 数量
            order_type: 订单类型
            price: 价格
            **params: 其他参数
            
        Returns:
            订单信息字典
        """
        exchange = self._get_exchange(account_id)
        
        # 检查是否为统一账户模式
        account_config = self.config_manager.get_account(account_id)
        is_portfolio_margin = account_config.get('portfolio_margin', False)
        
        if is_portfolio_margin:
            # 统一账户模式：使用Portfolio Margin API
            # 双向持仓模式需要指定positionSide
            position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'
            
            order_params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': amount,
                'positionSide': position_side  # 双向持仓模式必需
            }
            
            if order_type != "market" and price is not None:
                order_params['price'] = price
                
            order_params.update(params)
            
            return exchange.papiPostUmOrder(order_params)
        else:
            # 普通账户模式：使用原有逻辑
            exchange.options['defaultType'] = 'future'
            return exchange.create_order(symbol, order_type, side, amount, price, params)
    
    @handle_ccxt_error
    def cancel_order(
        self,
        account_id: str,
        order_id: str,
        symbol: str,
        **params
    ) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            symbol: 交易对
            **params: 其他参数
            
        Returns:
            取消结果
        """
        exchange = self._get_exchange(account_id)
        return exchange.cancel_order(order_id, symbol, params)
    
    @handle_ccxt_error
    def edit_order(
        self,
        account_id: str,
        order_id: str,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        **params
    ) -> Dict[str, Any]:
        """
        修改订单
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            symbol: 交易对
            order_type: 订单类型
            side: 买卖方向
            amount: 数量
            price: 价格
            **params: 其他参数
            
        Returns:
            修改后的订单信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.edit_order(order_id, symbol, order_type, side, amount, price, params)
    
    # ==================== 账户查询工具 ====================
    
    @handle_ccxt_error
    def get_balance(
        self,
        account_id: str,
        account_type: str = "spot",
        **params
    ) -> Dict[str, Any]:
        """
        查询账户余额
        
        Args:
            account_id: 账户ID
            account_type: 账户类型 ("spot" | "future" | "option")
            **params: 其他参数
            
        Returns:
            余额信息字典
        """
        exchange = self._get_exchange(account_id)
        
        # 检查是否为统一账户模式
        account_config = self.config_manager.get_account(account_id)
        is_portfolio_margin = account_config.get('portfolio_margin', False)
        
        if is_portfolio_margin:
            # 统一账户模式下的逻辑
            if account_type in ["future", "option", "margin"]:
                # 衍生品账户：使用Portfolio Margin API
                balance_data = exchange.papi_get_balance(params)
                
                # 将Portfolio Margin API格式转换为ccxt标准格式
                if isinstance(balance_data, list):
                    result = {}
                    for asset in balance_data:
                        currency = asset.get('asset')
                        if currency:
                            # 统一账户的总可用余额 = 杠杆可用 + 期货余额
                            cross_margin_free = float(asset.get('crossMarginFree', 0))
                            um_wallet_balance = float(asset.get('umWalletBalance', 0)) 
                            cm_wallet_balance = float(asset.get('cmWalletBalance', 0))
                            
                            total_available = cross_margin_free + um_wallet_balance + cm_wallet_balance
                            total_wallet_balance = float(asset.get('totalWalletBalance', 0))
                            
                            result[currency] = {
                                'free': total_available,
                                'used': max(0, total_wallet_balance - total_available),
                                'total': total_wallet_balance,
                                # 额外信息用于调试
                                'crossMarginFree': cross_margin_free,
                                'umWalletBalance': um_wallet_balance,
                                'cmWalletBalance': cm_wallet_balance
                            }
                    return result
                else:
                    return balance_data
            else:
                # 现货账户：即使在统一账户模式下，现货账户仍然是独立的
                # 创建一个专门的现货exchange（不使用portfolioMargin配置）
                account_config = self.config_manager.get_account(account_id)
                spot_exchange = self._create_spot_only_exchange(account_config)
                return spot_exchange.fetch_balance(params)
        else:
            # 普通账户模式：使用原有逻辑
            if account_type == "future":
                exchange.options['defaultType'] = 'future'
            elif account_type == "option":
                exchange.options['defaultType'] = 'option'
            else:
                exchange.options['defaultType'] = 'spot'
            
            return exchange.fetch_balance(params)
    
    @handle_ccxt_error
    def get_positions(
        self,
        account_id: str,
        symbols: Optional[List[str]] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        查询持仓信息
        
        Args:
            account_id: 账户ID
            symbols: 指定交易对列表（可选）
            **params: 其他参数
            
        Returns:
            持仓信息列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_positions(symbols, params)
    
    @handle_ccxt_error
    def get_orders(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 50,
        **params
    ) -> List[Dict[str, Any]]:
        """
        查询订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对（可选，不指定则查询所有）
            since: 起始时间戳（可选）
            limit: 数量限制
            **params: 其他参数
            
        Returns:
            订单列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_orders(symbol, since, limit, params)
    
    @handle_ccxt_error
    def get_open_orders(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        查询开放订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对（可选）
            **params: 其他参数
            
        Returns:
            开放订单列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_open_orders(symbol, params)
    
    @handle_ccxt_error
    def get_trades(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 50,
        **params
    ) -> List[Dict[str, Any]]:
        """
        查询交易记录
        
        Args:
            account_id: 账户ID
            symbol: 交易对（可选）
            since: 起始时间戳（可选）
            limit: 数量限制
            **params: 其他参数
            
        Returns:
            交易记录列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_my_trades(symbol, since, limit, params)
    
    # ==================== 市场数据工具 ====================
    
    @handle_ccxt_error
    def get_ticker(
        self,
        symbol: str,
        **params
    ) -> Dict[str, Any]:
        """
        获取实时价格数据
        
        Args:
            symbol: 交易对
            **params: 其他参数
            
        Returns:
            价格数据字典
        """
        # 市场数据不需要特定账户，使用任意配置的账户
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_ticker(symbol, params)
    
    @handle_ccxt_error
    def get_order_book(
        self,
        symbol: str,
        limit: int = 100,
        **params
    ) -> Dict[str, Any]:
        """
        获取订单簿深度
        
        Args:
            symbol: 交易对
            limit: 深度数量限制
            **params: 其他参数
            
        Returns:
            订单簿数据
        """
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_order_book(symbol, limit, params)
    
    @handle_ccxt_error
    def get_klines(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: int = 100,
        **params
    ) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            timeframe: 时间周期 ("1m", "5m", "1h", "1d" 等)
            since: 起始时间戳（可选）
            limit: 数量限制
            **params: 其他参数
            
        Returns:
            K线数据列表 [[timestamp, open, high, low, close, volume], ...]
        """
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_ohlcv(symbol, timeframe, since, limit, params)
    
    @handle_ccxt_error
    def get_trading_fees(
        self,
        account_id: str,
        **params
    ) -> Dict[str, Any]:
        """
        查询交易手续费
        
        Args:
            account_id: 账户ID
            **params: 其他参数
            
        Returns:
            手续费信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_trading_fees(params)
    
    # ==================== 高级订单类型工具 ====================
    
    @handle_ccxt_error
    def create_stop_loss_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        **params
    ) -> Dict[str, Any]:
        """
        创建止损订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 买卖方向 ("buy" | "sell")
            amount: 数量
            stop_price: 触发价格
            **params: 其他参数
            
        Returns:
            订单信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.create_stop_loss_order(symbol, amount, stop_price, side, params)
    
    @handle_ccxt_error
    def create_take_profit_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        take_profit_price: float,
        **params
    ) -> Dict[str, Any]:
        """
        创建止盈订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            take_profit_price: 止盈价格
            **params: 其他参数
            
        Returns:
            订单信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.create_take_profit_order(symbol, amount, take_profit_price, side, params)
    
    @handle_ccxt_error
    def create_stop_limit_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        limit_price: float,
        **params
    ) -> Dict[str, Any]:
        """
        创建止损限价订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            stop_price: 触发价格
            limit_price: 限价价格
            **params: 其他参数
            
        Returns:
            订单信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.create_stop_limit_order(symbol, amount, stop_price, limit_price, side, params)
    
    @handle_ccxt_error
    def create_trailing_stop_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        trail_percent: float,
        **params
    ) -> Dict[str, Any]:
        """
        创建追踪止损订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            trail_percent: 追踪百分比
            **params: 其他参数
            
        Returns:
            订单信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.create_trailing_percent_order(symbol, 'stop', side, amount, None, trail_percent, params)
    
    @handle_ccxt_error
    def create_oco_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        stop_price: float,
        stop_limit_price: Optional[float] = None,
        **params
    ) -> Dict[str, Any]:
        """
        创建OCO订单 (One-Cancels-Other)
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            price: 限价价格
            stop_price: 止损触发价格
            stop_limit_price: 止损限价价格（可选）
            **params: 其他参数
            
        Returns:
            OCO订单信息
        """
        exchange = self._get_exchange(account_id)
        
        # Binance OCO订单参数
        oco_params = {
            'quantity': amount,
            'price': price,
            'stopPrice': stop_price,
            'side': side.upper()
        }
        
        if stop_limit_price:
            oco_params['stopLimitPrice'] = stop_limit_price
            
        oco_params.update(params)
        
        # 调用Binance专用OCO接口
        return exchange.sapi_post_order_oco({
            'symbol': symbol.replace('/', ''),
            **oco_params
        })
    
    # ==================== 市场数据深度工具 ====================
    
    @handle_ccxt_error
    def get_funding_rate(
        self,
        symbol: str,
        **params
    ) -> Dict[str, Any]:
        """
        获取资金费率（期货）
        
        Args:
            symbol: 交易对
            **params: 其他参数
            
        Returns:
            资金费率信息
        """
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_funding_rate(symbol, params)
    
    # ==================== 期权交易工具 ====================
    
    @handle_ccxt_error
    def create_option_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        option_type: str = "limit",
        **params
    ) -> Dict[str, Any]:
        """
        创建期权订单
        
        Args:
            account_id: 账户ID
            symbol: 期权合约符号
            side: 买卖方向 ("buy" | "sell")
            amount: 数量
            price: 价格（市价单可为None）
            option_type: 订单类型 ("limit" | "market")
            **params: 其他参数
            
        Returns:
            期权订单信息
        """
        exchange = self._get_exchange(account_id)
        
        # 切换到期权市场
        exchange.options['defaultType'] = 'option'
        
        return exchange.create_order(symbol, option_type, side, amount, price, params)
    
    @handle_ccxt_error
    def get_option_chain(
        self,
        underlying: str,
        **params
    ) -> List[Dict[str, Any]]:
        """
        获取期权链
        
        Args:
            underlying: 标的资产 (如 "BTC")
            **params: 其他参数
            
        Returns:
            期权链数据
        """
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_option_chain(underlying, params)
    
    @handle_ccxt_error
    def get_option_positions(
        self,
        account_id: str,
        **params
    ) -> List[Dict[str, Any]]:
        """
        获取期权持仓
        
        Args:
            account_id: 账户ID
            **params: 其他参数
            
        Returns:
            期权持仓列表
        """
        exchange = self._get_exchange(account_id)
        exchange.options['defaultType'] = 'option'
        
        # ccxt的fetch_option_positions不需要symbol参数
        return exchange.fetch_option_positions(None, params)
    
    @handle_ccxt_error
    def get_option_info(
        self,
        symbol: str,
        **params
    ) -> Dict[str, Any]:
        """
        获取期权合约信息
        
        Args:
            symbol: 期权合约符号
            **params: 其他参数
            
        Returns:
            期权合约详情
        """
        accounts = self.config_manager.list_accounts()
        if not accounts:
            raise ValueError("未配置任何账户")
        
        account_id = next(iter(accounts.keys()))
        exchange = self._get_exchange(account_id)
        
        return exchange.fetch_option(symbol, params)
    
    # ==================== 合约/期货交易工具 ====================
    
    @handle_ccxt_error
    def create_contract_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "limit",
        price: Optional[float] = None,
        contract_type: str = "future",
        **params
    ) -> Dict[str, Any]:
        """
        创建合约订单（通用）
        
        Args:
            account_id: 账户ID
            symbol: 交易对 (注意：期货使用不同命名格式，如 "1000SHIBUSDT" 而非 "SHIB/USDT")
            side: 买卖方向
            amount: 数量
            order_type: 订单类型
            price: 价格
            contract_type: 合约类型 ("future" | "delivery")
            **params: 其他参数
            
        Returns:
            合约订单信息
        """
        exchange = self._get_exchange(account_id)
        
        # 检查是否为统一账户模式
        account_config = self.config_manager.get_account(account_id)
        is_portfolio_margin = account_config.get('portfolio_margin', False)
        
        if is_portfolio_margin:
            # 统一账户模式：使用Portfolio Margin API下单
            # 双向持仓模式需要指定positionSide
            position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'
            
            order_params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': amount,
                'positionSide': position_side  # 双向持仓模式必需
            }
            
            if order_type != "market" and price is not None:
                order_params['price'] = price
            
            order_params.update(params)
            
            # 使用正确的CCXT Portfolio Margin API方法
            return exchange.papiPostUmOrder(order_params)
        else:
            # 普通账户模式：使用原有逻辑
            if contract_type == "delivery":
                exchange.options['defaultType'] = 'delivery'
            else:
                exchange.options['defaultType'] = 'future'
            
            return exchange.create_order(symbol, order_type, side, amount, price, params)
    
    @handle_ccxt_error
    def close_position(
        self,
        account_id: str,
        symbol: str,
        side: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        一键平仓
        
        Args:
            account_id: 账户ID
            symbol: 交易对 (期货格式，如 "BTCUSDT")
            side: 平仓方向（可选，不指定则平所有）
            **params: 其他参数
            
        Returns:
            平仓结果
        """
        exchange = self._get_exchange(account_id)
        
        # 获取当前持仓
        positions = exchange.fetch_positions([symbol])
        
        results = []
        for position in positions:
            if position['contracts'] > 0:  # 有持仓
                position_side = position['side']
                if side is None or position_side == side:
                    # 平仓（反向开单）
                    close_side = 'sell' if position_side == 'long' else 'buy'
                    close_amount = position['contracts']
                    
                    result = exchange.create_market_order(
                        symbol, close_side, close_amount, None, params
                    )
                    results.append(result)
        
        return {"closed_positions": results}
    
    @handle_ccxt_error
    def get_futures_positions(
        self,
        account_id: str,
        symbols: Optional[List[str]] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        获取期货持仓详情
        
        Args:
            account_id: 账户ID
            symbols: 指定交易对（可选）
            **params: 其他参数
            
        Returns:
            期货持仓列表
        """
        exchange = self._get_exchange(account_id)
        exchange.options['defaultType'] = 'future'
        
        return exchange.fetch_positions(symbols, params)
    
    # ==================== 完善的订单管理工具 ====================
    
    @handle_ccxt_error
    def get_order_status(
        self,
        account_id: str,
        order_id: str,
        symbol: str,
        **params
    ) -> Dict[str, Any]:
        """
        查询单个订单状态
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            symbol: 交易对
            **params: 其他参数
            
        Returns:
            订单详细信息
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_order(order_id, symbol, params)
    
    @handle_ccxt_error
    def get_my_trades(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 100,
        **params
    ) -> List[Dict[str, Any]]:
        """
        获取我的成交记录
        
        Args:
            account_id: 账户ID
            symbol: 交易对（可选）
            since: 起始时间戳（可选）
            limit: 数量限制
            **params: 其他参数
            
        Returns:
            成交记录列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.fetch_my_trades(symbol, since, limit, params)
    
    @handle_ccxt_error
    def cancel_all_orders(
        self,
        account_id: str,
        symbol: Optional[str] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        批量取消订单
        
        Args:
            account_id: 账户ID
            symbol: 交易对（可选，不指定则取消所有）
            **params: 其他参数
            
        Returns:
            取消结果列表
        """
        exchange = self._get_exchange(account_id)
        return exchange.cancel_all_orders(symbol, params)
    
    # ==================== 账户设置管理工具 ====================
    
    @handle_ccxt_error
    def set_leverage(
        self,
        account_id: str,
        symbol: str,
        leverage: float,
        **params
    ) -> Dict[str, Any]:
        """
        设置杠杆倍数
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            leverage: 杠杆倍数
            **params: 其他参数
            
        Returns:
            设置结果
        """
        exchange = self._get_exchange(account_id)
        return exchange.set_leverage(leverage, symbol, params)
    
    @handle_ccxt_error
    def set_margin_mode(
        self,
        account_id: str,
        symbol: str,
        margin_mode: str,
        **params
    ) -> Dict[str, Any]:
        """
        设置保证金模式
        
        Args:
            account_id: 账户ID
            symbol: 交易对
            margin_mode: 保证金模式 ("isolated" | "cross")
            **params: 其他参数
            
        Returns:
            设置结果
        """
        exchange = self._get_exchange(account_id)
        return exchange.set_margin_mode(margin_mode, symbol, params)
    
    @handle_ccxt_error
    def transfer_funds(
        self,
        account_id: str,
        currency: str,
        amount: float,
        from_account: str,
        to_account: str,
        **params
    ) -> Dict[str, Any]:
        """
        账户间转账
        
        Args:
            account_id: 账户ID
            currency: 币种
            amount: 转账金额
            from_account: 源账户类型 ("spot" | "future" | "option")
            to_account: 目标账户类型 ("spot" | "future" | "option")
            **params: 其他参数
            
        Returns:
            转账结果
        """
        # 对于转账功能，需要使用不带portfolioMargin配置的exchange
        # 因为universal transfer API不支持portfolioMargin模式
        account_config = self.config_manager.get_account(account_id)
        
        # 创建专门用于转账的exchange实例
        transfer_exchange = ccxt.binance({
            'apiKey': account_config['api_key'],
            'secret': account_config['secret'],
            'sandbox': account_config.get('sandbox', False),
            'enableRateLimit': True,
            'options': {
                'broker': {
                    'spot': 'C96E9MGA',
                    'future': 'eFC56vBf',
                    'option': 'eFC56vBf',
                },
                # 重要: 不设置portfolioMargin，让转账使用universal transfer API
            }
        })
        
        # 统一账户模式下，直接调用universal transfer API
        account_config = self.config_manager.get_account(account_id)
        is_portfolio_margin = account_config.get('portfolio_margin', False)
        
        if is_portfolio_margin:
            # 统一账户模式：根据币安的限制，需要特殊处理转账路径
            # 现货 ↔ 期货 必须通过全仓杠杆账户中转
            transfer_exchange.load_markets()
            
            if from_account == 'spot' and to_account == 'future':
                # 现货 → 期货：统一账户模式的特殊处理
                # 步骤1：现货 → 全仓杠杆（杠杆余额可直接用于期货交易）
                step1_result = transfer_exchange.sapi_post_asset_transfer({
                    'type': 'MAIN_MARGIN',
                    'asset': currency,
                    'amount': amount,
                    **params
                })
                
                # 等待1秒确保转账完成
                import time
                time.sleep(1)
                
                return {
                    'tranId': step1_result.get('tranId'),
                    'status': 'completed',
                    'message': f'转账成功：{amount} {currency} 已转入统一账户杠杆余额，可用于期货交易'
                }
                
            elif from_account == 'future' and to_account == 'spot':
                # 期货 → 现货：分两步
                # 步骤1：期货 → 全仓杠杆  
                step1_result = transfer_exchange.sapi_post_asset_transfer({
                    'type': 'UMFUTURE_MARGIN',
                    'asset': currency, 
                    'amount': amount,
                    **params
                })
                
                # 等待1秒确保转账完成
                import time
                time.sleep(1)
                
                # 步骤2：全仓杠杆 → 现货
                step2_result = transfer_exchange.sapi_post_asset_transfer({
                    'type': 'MARGIN_MAIN',
                    'asset': currency,
                    'amount': amount, 
                    **params
                })
                
                return {
                    'step1': step1_result,
                    'step2': step2_result,
                    'tranId': step2_result.get('tranId'),
                    'status': 'completed',
                    'message': f'两步转账完成：期货 → 杠杆 → 现货'
                }
            else:
                # 其他支持的直接转账
                transfer_type_map = {
                    ('spot', 'margin'): 'MAIN_MARGIN',     # 现货到全仓杠杆
                    ('margin', 'spot'): 'MARGIN_MAIN',     # 全仓杠杆到现货
                    ('margin', 'future'): 'MARGIN_UMFUTURE', # 杠杆到期货
                    ('future', 'margin'): 'UMFUTURE_MARGIN', # 期货到杠杆
                }
                
                transfer_type = transfer_type_map.get((from_account, to_account))
                if not transfer_type:
                    raise ValueError(f"统一账户模式下不支持的转账类型: {from_account} -> {to_account}")
                
                return transfer_exchange.sapi_post_asset_transfer({
                    'type': transfer_type,
                    'asset': currency,
                    'amount': amount,
                    **params
                })
        else:
            # 普通账户模式：使用ccxt的transfer方法
            return transfer_exchange.transfer(currency, amount, from_account, to_account, params)
    
    # ==================== 工具辅助方法 ====================
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        tools = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and callable(getattr(self, attr_name)):
                if attr_name not in ['get_available_tools']:
                    tools.append(attr_name)
        return tools
    
    def clear_exchange_cache(self) -> None:
        """清除exchange实例缓存"""
        self._exchange_cache.clear()
        logger.info("Exchange cache cleared")