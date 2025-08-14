"""
Binance MCP Server - 币安交易所MCP服务

基于ccxt库为Binance交易所提供MCP协议支持，
让AI agents能够直接进行数字货币交易操作。

主要功能：
- 现货交易、期货交易、期权交易
- 账户余额和持仓查询
- 市场数据获取
- 自动broker ID注入
"""

__version__ = "1.0.0"
__author__ = "Binance MCP Team"

from .server import BinanceMCPServer
from .config import ConfigManager
from .broker import BinanceExchangeFactory

__all__ = [
    "BinanceMCPServer",
    "ConfigManager", 
    "BinanceExchangeFactory",
]