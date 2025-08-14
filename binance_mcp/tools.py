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
            symbol: 交易对 (如 "BTC/USDT")
            side: 买卖方向 ("buy" | "sell")
            amount: 数量
            order_type: 订单类型
            price: 价格
            **params: 其他参数
            
        Returns:
            订单信息字典
        """
        exchange = self._get_exchange(account_id)
        
        # 切换到期货市场
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
        
        # 根据账户类型设置
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
        
        return exchange.fetch_option_positions(params)
    
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
            symbol: 交易对 (注意：期货使用不同命名格式，如 "BTCUSDT" 而非 "BTC/USDT")
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
        
        # 设置合约类型
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
        exchange = self._get_exchange(account_id)
        return exchange.transfer(currency, amount, from_account, to_account, params)
    
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