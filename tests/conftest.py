"""
Pytest配置文件，定义测试fixtures和共享配置
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

import pytest
import ccxt

from binance_mcp.config import ConfigManager
from binance_mcp.broker import BinanceExchangeFactory
from binance_mcp.tools import BinanceMCPTools


@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_manager(temp_config_dir):
    """创建使用临时目录的配置管理器"""
    with patch.object(ConfigManager, '__init__') as mock_init:
        # 模拟初始化，使用临时目录
        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.config_dir = temp_config_dir / "binance-mcp"
        config_manager.config_file = config_manager.config_dir / "config.json"
        config_manager.key_file = config_manager.config_dir / ".key"
        
        # 确保目录存在
        config_manager.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化加密和配置
        from cryptography.fernet import Fernet
        config_manager._cipher = Fernet(Fernet.generate_key())
        config_manager._config = {
            "accounts": {},
            "server": {"port": 9001, "host": "127.0.0.1", "log_level": "INFO"},
            "mcp": {"server_name": "binance-mcp", "version": "1.0.0"}
        }
        
        yield config_manager


@pytest.fixture
def mock_binance_exchange():
    """创建mock的Binance exchange实例"""
    exchange = Mock(spec=ccxt.binance)
    
    # 基础属性
    exchange.id = 'binance'
    exchange.name = 'Binance'
    exchange.options = {
        'broker': {
            'spot': 'C96E9MGA',
            'future': 'eFC56vBf',
        },
        'defaultType': 'spot'
    }
    
    # 配置方法返回值
    exchange.load_markets.return_value = {
        'BTC/USDT': {
            'id': 'BTCUSDT',
            'symbol': 'BTC/USDT',
            'base': 'BTC',
            'quote': 'USDT',
            'active': True
        }
    }
    
    # 交易方法
    exchange.create_order.return_value = {
        'id': 'test_order_123',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 0.01,
        'price': 50000,
        'status': 'open',
        'timestamp': 1234567890000
    }
    
    exchange.cancel_order.return_value = {
        'id': 'test_order_123',
        'status': 'canceled'
    }
    
    # 查询方法
    exchange.fetch_balance.return_value = {
        'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
        'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}
    }
    
    exchange.fetch_positions.return_value = [
        {
            'symbol': 'BTC/USDT',
            'side': 'long',
            'size': 0.5,
            'unrealizedPnl': 100
        }
    ]
    
    exchange.fetch_orders.return_value = [
        {
            'id': 'test_order_123',
            'symbol': 'BTC/USDT',
            'status': 'closed'
        }
    ]
    
    # 市场数据方法
    exchange.fetch_ticker.return_value = {
        'symbol': 'BTC/USDT',
        'last': 50000,
        'bid': 49999,
        'ask': 50001,
        'volume': 12345.67
    }
    
    exchange.fetch_order_book.return_value = {
        'symbol': 'BTC/USDT',
        'bids': [[49999, 1.0], [49998, 2.0]],
        'asks': [[50001, 1.5], [50002, 2.5]]
    }
    
    exchange.fetch_ohlcv.return_value = [
        [1234567890000, 49000, 51000, 48000, 50000, 1000],
        [1234567890060, 50000, 52000, 49000, 51000, 1100]
    ]
    
    # 时间相关
    exchange.fetch_time.return_value = 1234567890000
    
    return exchange


@pytest.fixture
def test_account_config():
    """测试账户配置"""
    return {
        'api_key': 'test_api_key_123',
        'secret': 'test_secret_456', 
        'sandbox': True,
        'description': '测试账户'
    }


@pytest.fixture
def tools_with_mock_exchange(config_manager, mock_binance_exchange):
    """创建使用mock exchange的工具实例"""
    tools = BinanceMCPTools(config_manager)
    
    # 添加测试账户
    config_manager.add_account(
        'test_account',
        'test_api_key_123',
        'test_secret_456',
        True,
        '测试账户'
    )
    
    # Mock _get_exchange方法返回mock exchange
    with patch.object(tools, '_get_exchange', return_value=mock_binance_exchange):
        yield tools


@pytest.fixture
def mock_exchange_factory():
    """Mock的exchange工厂"""
    with patch.object(BinanceExchangeFactory, 'create_exchange') as mock_create:
        yield mock_create


# 测试数据fixtures
@pytest.fixture
def sample_order_data():
    """示例订单数据"""
    return {
        'id': 'test_order_123',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 0.01,
        'price': 50000,
        'status': 'open',
        'timestamp': 1234567890000,
        'clientOrderId': 'C96E9MGA1234567890'
    }


@pytest.fixture
def sample_balance_data():
    """示例余额数据"""
    return {
        'BTC': {'free': 1.0, 'used': 0.1, 'total': 1.1},
        'USDT': {'free': 9000.0, 'used': 1000.0, 'total': 10000.0},
        'free': {'BTC': 1.0, 'USDT': 9000.0},
        'used': {'BTC': 0.1, 'USDT': 1000.0},
        'total': {'BTC': 1.1, 'USDT': 10000.0}
    }


@pytest.fixture
def sample_ticker_data():
    """示例价格数据"""
    return {
        'symbol': 'BTC/USDT',
        'timestamp': 1234567890000,
        'last': 50000,
        'bid': 49999,
        'ask': 50001,
        'high': 52000,
        'low': 48000,
        'volume': 12345.67,
        'change': 1000,
        'percentage': 2.04
    }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )