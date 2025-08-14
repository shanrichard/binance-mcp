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
                "supported_markets": ["spot", "futures", "margin"],
                "broker_ids": {
                    "spot": "C96E9MGA",
                    "futures": "eFC56vBf"
                }
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
        # 返回基本信息，避免异步API问题
        return {
            "total_tools": 7,  # 我们注册的工具数量
            "tools": [
                "create_spot_order", 
                "cancel_order", 
                "get_balance",
                "get_ticker",
                "get_positions", 
                "get_open_orders",
                "get_server_info"
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