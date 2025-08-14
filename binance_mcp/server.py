"""
MCP服务器实现模块

基于FastMCP框架实现Binance MCP服务器，
将tools.py中的工具注册为MCP工具，供AI agents调用。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP

from .config import ConfigManager
from .tools import BinanceMCPTools

logger = logging.getLogger(__name__)


class BinanceMCPServer:
    """Binance MCP服务器"""
    
    def __init__(self, port: int = 9001, host: str = "127.0.0.1"):
        """
        初始化MCP服务器
        
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
        
        # 注册所有MCP工具
        self._register_trading_tools()
        self._register_query_tools()
        self._register_market_data_tools()
        self._register_setting_tools()
        
        logger.info(f"Binance MCP Server initialized on {host}:{port}")
    
    def _register_trading_tools(self):
        """注册交易操作工具"""
        
        @self.mcp.tool
        def create_spot_order(
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
                order_type: 订单类型 ("limit" | "market" | "stop_limit")
                price: 价格 (市价单可为None)
                **params: 其他参数
                
            Returns:
                订单信息字典
            """
            return self.tools.create_spot_order(
                account_id, symbol, side, amount, order_type, price, **params
            )
        
        @self.mcp.tool
        def create_futures_order(
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
            return self.tools.create_futures_order(
                account_id, symbol, side, amount, order_type, price, **params
            )
        
        @self.mcp.tool
        def cancel_order(
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
            return self.tools.cancel_order(account_id, order_id, symbol, **params)
        
        @self.mcp.tool
        def edit_order(
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
            return self.tools.edit_order(
                account_id, order_id, symbol, order_type, side, amount, price, **params
            )
    
    def _register_query_tools(self):
        """注册账户查询工具"""
        
        @self.mcp.tool
        def get_balance(
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
            return self.tools.get_balance(account_id, account_type, **params)
        
        @self.mcp.tool
        def get_positions(
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
            return self.tools.get_positions(account_id, symbols, **params)
        
        @self.mcp.tool
        def get_orders(
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
                symbol: 交易对（可选）
                since: 起始时间戳（可选）
                limit: 数量限制
                **params: 其他参数
                
            Returns:
                订单列表
            """
            return self.tools.get_orders(account_id, symbol, since, limit, **params)
        
        @self.mcp.tool
        def get_open_orders(
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
            return self.tools.get_open_orders(account_id, symbol, **params)
        
        @self.mcp.tool
        def get_trades(
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
            return self.tools.get_trades(account_id, symbol, since, limit, **params)
        
        @self.mcp.tool
        def get_trading_fees(
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
            return self.tools.get_trading_fees(account_id, **params)
    
    def _register_market_data_tools(self):
        """注册市场数据工具"""
        
        @self.mcp.tool
        def get_ticker(
            symbol: str,
            **params
        ) -> Dict[str, Any]:
            """
            获取实时价格数据
            
            Args:
                symbol: 交易对 (如 "BTC/USDT")
                **params: 其他参数
                
            Returns:
                价格数据字典
            """
            return self.tools.get_ticker(symbol, **params)
        
        @self.mcp.tool
        def get_order_book(
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
            return self.tools.get_order_book(symbol, limit, **params)
        
        @self.mcp.tool
        def get_klines(
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
                K线数据列表
            """
            return self.tools.get_klines(symbol, timeframe, since, limit, **params)
    
    def _register_setting_tools(self):
        """注册设置管理工具"""
        
        @self.mcp.tool
        def set_leverage(
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
            return self.tools.set_leverage(account_id, symbol, leverage, **params)
        
        @self.mcp.tool
        def set_margin_mode(
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
            return self.tools.set_margin_mode(account_id, symbol, margin_mode, **params)
        
        @self.mcp.tool
        def transfer_funds(
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
                from_account: 源账户类型
                to_account: 目标账户类型
                **params: 其他参数
                
            Returns:
                转账结果
            """
            return self.tools.transfer_funds(
                account_id, currency, amount, from_account, to_account, **params
            )
    
    def start(self):
        """启动MCP服务器"""
        logger.info(f"Starting Binance MCP Server on {self.host}:{self.port}")
        
        # 验证配置
        self._validate_setup()
        
        try:
            # 启动FastMCP服务器
            self.mcp.run(host=self.host, port=self.port)
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise RuntimeError(f"MCP服务器启动失败: {e}")
    
    def stop(self):
        """停止MCP服务器"""
        logger.info("Stopping Binance MCP Server")
        # FastMCP的停止逻辑
        # 清理资源
        self.tools.clear_exchange_cache()
    
    def _validate_setup(self):
        """验证服务器设置"""
        # 检查是否有配置的账户
        accounts = self.config_manager.list_accounts()
        if not accounts:
            logger.warning("No accounts configured. Please run 'binance-mcp config' first.")
        else:
            logger.info(f"Found {len(accounts)} configured account(s)")
            
            # 验证账户配置
            for account_id in accounts:
                if self.config_manager.validate_account(account_id):
                    logger.info(f"Account '{account_id}' configuration is valid")
                else:
                    logger.warning(f"Account '{account_id}' configuration may be invalid")
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        accounts = self.config_manager.list_accounts()
        
        return {
            "server_name": "binance-mcp",
            "version": "1.0.0",
            "host": self.host,
            "port": self.port,
            "accounts_configured": len(accounts),
            "available_tools": self.tools.get_available_tools(),
            "config_path": self.config_manager.get_config_path()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": self._get_current_timestamp(),
            "checks": {}
        }
        
        try:
            # 检查配置文件
            accounts = self.config_manager.list_accounts()
            health_status["checks"]["config"] = {
                "status": "ok",
                "accounts_count": len(accounts)
            }
            
            # 检查工具可用性
            tools_count = len(self.tools.get_available_tools())
            health_status["checks"]["tools"] = {
                "status": "ok",
                "tools_count": tools_count
            }
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 全局服务器实例（用于CLI）
_server_instance: Optional[BinanceMCPServer] = None


def create_server(port: int = 9001, host: str = "127.0.0.1") -> BinanceMCPServer:
    """创建服务器实例"""
    global _server_instance
    _server_instance = BinanceMCPServer(port=port, host=host)
    return _server_instance


def get_server() -> Optional[BinanceMCPServer]:
    """获取当前服务器实例"""
    return _server_instance