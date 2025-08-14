"""
简化的MCP服务器实现

避免FastMCP对**kwargs的限制，提供基本的MCP服务功能。
"""

import logging
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP

from .config import ConfigManager
from .tools import BinanceMCPTools

logger = logging.getLogger(__name__)


class SimpleBinanceMCPServer:
    """简化的Binance MCP服务器"""
    
    def __init__(self, port: int = 9001, host: str = "127.0.0.1"):
        """
        初始化简化MCP服务器
        
        Args:
            port: 服务端口
            host: 服务地址
        """
        self.port = port
        self.host = host
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.tools = BinanceMCPTools(self.config_manager)
        
        # 创建FastMCP实例
        self.mcp = FastMCP(name="binance-mcp")
        
        # 注册核心MCP工具（无**kwargs）
        self._register_core_tools()
        
        logger.info(f"Simple Binance MCP Server initialized on {host}:{port}")
    
    def _register_core_tools(self):
        """注册核心工具（不使用**kwargs）"""
        
        @self.mcp.tool
        def create_spot_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            order_type: str = "limit",
            price: Optional[float] = None
        ) -> Dict[str, Any]:
            """
            创建现货订单
            
            Args:
                account_id: 账户ID
                symbol: 交易对 (如 "BTC/USDT")
                side: 买卖方向 ("buy" | "sell")
                amount: 数量
                order_type: 订单类型 ("limit" | "market")
                price: 价格 (市价单可为None)
                
            Returns:
                订单信息字典
            """
            return self.tools.create_spot_order(
                account_id, symbol, side, amount, order_type, price
            )
        
        @self.mcp.tool
        def cancel_order(
            account_id: str,
            order_id: str,
            symbol: str
        ) -> Dict[str, Any]:
            """
            取消订单
            
            Args:
                account_id: 账户ID
                order_id: 订单ID
                symbol: 交易对
                
            Returns:
                取消结果
            """
            return self.tools.cancel_order(account_id, order_id, symbol)
        
        @self.mcp.tool
        def get_balance(account_id: str) -> Dict[str, Any]:
            """
            获取账户余额
            
            Args:
                account_id: 账户ID
                
            Returns:
                余额信息字典
            """
            return self.tools.get_balance(account_id)
        
        @self.mcp.tool
        def get_ticker(symbol: str) -> Dict[str, Any]:
            """
            获取价格行情
            
            Args:
                symbol: 交易对
                
            Returns:
                价格数据字典
            """
            return self.tools.get_ticker(symbol)
        
        @self.mcp.tool
        def get_positions(account_id: str, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            获取持仓信息
            
            Args:
                account_id: 账户ID
                symbol: 可选的交易对过滤
                
            Returns:
                持仓列表
            """
            return self.tools.get_positions(account_id, symbol)
        
        @self.mcp.tool
        def get_open_orders(account_id: str, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            获取开放订单
            
            Args:
                account_id: 账户ID
                symbol: 可选的交易对过滤
                
            Returns:
                开放订单列表
            """
            return self.tools.get_open_orders(account_id, symbol)
        
        # ==================== 高级订单类型工具 ====================
        
        @self.mcp.tool
        def create_stop_loss_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            stop_price: float
        ) -> Dict[str, Any]:
            """创建止损订单"""
            return self.tools.create_stop_loss_order(account_id, symbol, side, amount, stop_price)
        
        @self.mcp.tool
        def create_take_profit_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            take_profit_price: float
        ) -> Dict[str, Any]:
            """创建止盈订单"""
            return self.tools.create_take_profit_order(account_id, symbol, side, amount, take_profit_price)
        
        @self.mcp.tool
        def create_stop_limit_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            stop_price: float,
            limit_price: float
        ) -> Dict[str, Any]:
            """创建止损限价订单"""
            return self.tools.create_stop_limit_order(account_id, symbol, side, amount, stop_price, limit_price)
        
        @self.mcp.tool
        def create_trailing_stop_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            trail_percent: float
        ) -> Dict[str, Any]:
            """创建追踪止损订单"""
            return self.tools.create_trailing_stop_order(account_id, symbol, side, amount, trail_percent)
        
        @self.mcp.tool
        def create_oco_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            price: float,
            stop_price: float,
            stop_limit_price: Optional[float] = None
        ) -> Dict[str, Any]:
            """创建OCO订单 (One-Cancels-Other)"""
            return self.tools.create_oco_order(account_id, symbol, side, amount, price, stop_price, stop_limit_price)
        
        # ==================== 市场数据深度工具 ====================
        
        @self.mcp.tool
        def get_funding_rate(symbol: str) -> Dict[str, Any]:
            """获取资金费率（期货）"""
            return self.tools.get_funding_rate(symbol)
        
        # ==================== 期权交易工具 ====================
        
        @self.mcp.tool
        def create_option_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            price: Optional[float] = None,
            option_type: str = "limit"
        ) -> Dict[str, Any]:
            """创建期权订单"""
            return self.tools.create_option_order(account_id, symbol, side, amount, price, option_type)
        
        @self.mcp.tool
        def get_option_chain(underlying: str) -> List[Dict[str, Any]]:
            """获取期权链"""
            return self.tools.get_option_chain(underlying)
        
        @self.mcp.tool
        def get_option_positions(account_id: str) -> List[Dict[str, Any]]:
            """获取期权持仓"""
            return self.tools.get_option_positions(account_id)
        
        @self.mcp.tool
        def get_option_info(symbol: str) -> Dict[str, Any]:
            """获取期权合约信息"""
            return self.tools.get_option_info(symbol)
        
        # ==================== 合约/期货交易工具 ====================
        
        @self.mcp.tool
        def create_contract_order(
            account_id: str,
            symbol: str,
            side: str,
            amount: float,
            order_type: str = "limit",
            price: Optional[float] = None,
            contract_type: str = "future"
        ) -> Dict[str, Any]:
            """创建合约订单（通用）"""
            return self.tools.create_contract_order(account_id, symbol, side, amount, order_type, price, contract_type)
        
        @self.mcp.tool
        def close_position(
            account_id: str,
            symbol: str,
            side: Optional[str] = None
        ) -> Dict[str, Any]:
            """一键平仓"""
            return self.tools.close_position(account_id, symbol, side)
        
        @self.mcp.tool
        def get_futures_positions(
            account_id: str,
            symbols: Optional[List[str]] = None
        ) -> List[Dict[str, Any]]:
            """获取期货持仓详情"""
            return self.tools.get_futures_positions(account_id, symbols)
        
        # ==================== 完善的订单管理工具 ====================
        
        @self.mcp.tool
        def get_order_status(
            account_id: str,
            order_id: str,
            symbol: str
        ) -> Dict[str, Any]:
            """查询单个订单状态"""
            return self.tools.get_order_status(account_id, order_id, symbol)
        
        @self.mcp.tool
        def get_my_trades(
            account_id: str,
            symbol: Optional[str] = None,
            since: Optional[int] = None,
            limit: int = 100
        ) -> List[Dict[str, Any]]:
            """获取我的成交记录"""
            return self.tools.get_my_trades(account_id, symbol, since, limit)
        
        @self.mcp.tool
        def cancel_all_orders(
            account_id: str,
            symbol: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """批量取消订单"""
            return self.tools.cancel_all_orders(account_id, symbol)
        
        # ==================== 账户设置管理工具 ====================
        
        @self.mcp.tool
        def set_leverage(
            account_id: str,
            symbol: str,
            leverage: float
        ) -> Dict[str, Any]:
            """设置杠杆倍数"""
            return self.tools.set_leverage(account_id, symbol, leverage)
        
        @self.mcp.tool
        def set_margin_mode(
            account_id: str,
            symbol: str,
            margin_mode: str
        ) -> Dict[str, Any]:
            """设置保证金模式"""
            return self.tools.set_margin_mode(account_id, symbol, margin_mode)
        
        @self.mcp.tool
        def transfer_funds(
            account_id: str,
            currency: str,
            amount: float,
            from_account: str,
            to_account: str
        ) -> Dict[str, Any]:
            """账户间转账"""
            return self.tools.transfer_funds(account_id, currency, amount, from_account, to_account)
        
        @self.mcp.tool
        def get_server_info() -> Dict[str, Any]:
            """
            获取服务器信息
            
            Returns:
                服务器信息字典
            """
            accounts = self.config_manager.list_accounts()
            return {
                "server_name": "binance-mcp",
                "version": "1.0.0",
                "configured_accounts": len(accounts),
                "accounts": list(accounts.keys()) if accounts else [],
                "supported_markets": ["spot", "futures", "options"],
                "broker_ids": {
                    "spot": "C96E9MGA",
                    "futures": "eFC56vBf"
                },
                "total_tools": 29
            }
    
    def run(self):
        """运行服务器"""
        try:
            logger.info(f"Starting Binance MCP Server on {self.host}:{self.port}")
            # FastMCP默认使用stdio transport，不需要host和port
            self.mcp.run()
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    def get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        # 返回所有29个工具的基本信息
        return {
            "total_tools": 29,
            "tools": [
                # 原有核心工具
                "create_spot_order", "cancel_order", "get_balance", "get_ticker", 
                "get_positions", "get_open_orders", "get_server_info",
                
                # 高级订单类型
                "create_stop_loss_order", "create_take_profit_order", "create_stop_limit_order",
                "create_trailing_stop_order", "create_oco_order",
                
                # 市场数据深度
                "get_order_book", "get_klines", "get_funding_rate",
                
                # 期权交易
                "create_option_order", "get_option_chain", "get_option_positions", "get_option_info",
                
                # 合约/期货交易  
                "create_contract_order", "close_position", "get_futures_positions",
                
                # 完善的订单管理
                "get_order_status", "get_my_trades", "cancel_all_orders",
                
                # 账户设置管理
                "set_leverage", "set_margin_mode", "transfer_funds"
            ]
        }


def create_simple_server(config_manager: Optional[ConfigManager] = None) -> SimpleBinanceMCPServer:
    """
    创建简化MCP服务器实例
    
    Args:
        config_manager: 可选的配置管理器
        
    Returns:
        服务器实例
    """
    server = SimpleBinanceMCPServer()
    if config_manager:
        server.config_manager = config_manager
        server.tools = BinanceMCPTools(config_manager)
    
    return server


# 创建全局服务器实例
simple_server = create_simple_server()