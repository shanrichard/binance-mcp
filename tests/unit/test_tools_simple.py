"""
简化的MCP工具模块单元测试
"""

import pytest
from unittest.mock import Mock, patch
import ccxt

from binance_mcp.tools import BinanceMCPTools, handle_ccxt_error


@pytest.mark.unit
class TestBinanceMCPTools:
    """BinanceMCPTools单元测试"""
    
    def test_init_with_config_manager(self, config_manager):
        """测试使用配置管理器初始化"""
        tools = BinanceMCPTools(config_manager)
        assert tools.config_manager == config_manager
    
    def test_get_exchange_invalid_account(self, config_manager):
        """测试获取不存在账户的exchange"""
        tools = BinanceMCPTools(config_manager)
        
        with pytest.raises(ValueError, match="账户 .* 不存在"):
            tools._get_exchange('nonexistent_account')
    
    @patch('binance_mcp.tools.exchange_factory.create_exchange')
    def test_get_exchange_success(self, mock_create_exchange, config_manager):
        """测试成功获取exchange实例"""
        # 添加测试账户
        config_manager.add_account(
            'test_account',
            'test_api_key_123',
            'test_secret_456',
            True,
            '测试账户'
        )
        
        # 模拟exchange创建
        mock_exchange = Mock()
        mock_create_exchange.return_value = mock_exchange
        
        tools = BinanceMCPTools(config_manager)
        result = tools._get_exchange('test_account')
        
        assert result == mock_exchange
        mock_create_exchange.assert_called_once()
    
    def test_create_spot_order_success(self, tools_with_mock_exchange):
        """测试成功创建现货订单"""
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.create_order.return_value = {
            'id': 'test_order_123',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 0.01,
            'price': 50000,
            'status': 'open'
        }
        
        result = tools_with_mock_exchange.create_spot_order(
            account_id='test_account',
            symbol='BTC/USDT',
            side='buy',
            amount=0.01,
            price=50000,
            order_type='limit'
        )
        
        assert result['id'] == 'test_order_123'
        assert result['symbol'] == 'BTC/USDT'
        assert result['side'] == 'buy'
        
        mock_exchange.create_order.assert_called_once_with(
            'BTC/USDT', 'limit', 'buy', 0.01, 50000, {}
        )
    
    def test_cancel_order_success(self, tools_with_mock_exchange):
        """测试成功取消订单"""
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.cancel_order.return_value = {
            'id': 'test_order_123',
            'status': 'canceled'
        }
        
        result = tools_with_mock_exchange.cancel_order(
            account_id='test_account',
            order_id='test_order_123',
            symbol='BTC/USDT'
        )
        
        assert result['id'] == 'test_order_123'
        assert result['status'] == 'canceled'
        
        mock_exchange.cancel_order.assert_called_once_with(
            'test_order_123', 'BTC/USDT', {}
        )
    
    def test_get_balance_success(self, tools_with_mock_exchange):
        """测试成功获取余额"""
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.fetch_balance.return_value = {
            'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}
        }
        
        result = tools_with_mock_exchange.get_balance('test_account')
        
        assert 'BTC' in result
        assert 'USDT' in result
        assert result['BTC']['free'] == 1.0
        assert result['USDT']['free'] == 10000.0
        
        mock_exchange.fetch_balance.assert_called_once()
    
    def test_get_ticker_success(self, tools_with_mock_exchange):
        """测试成功获取价格行情"""
        # get_ticker会自动使用第一个配置的账户
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 50000,
            'bid': 49999,
            'ask': 50001,
            'volume': 12345.67
        }
        
        result = tools_with_mock_exchange.get_ticker(symbol='BTC/USDT')
        
        assert result['symbol'] == 'BTC/USDT'
        assert result['last'] == 50000
        assert result['bid'] == 49999
        assert result['ask'] == 50001
        
        mock_exchange.fetch_ticker.assert_called_once_with('BTC/USDT', {})


@pytest.mark.unit
class TestHandleCcxtError:
    """测试ccxt错误处理装饰器"""
    
    def test_handle_ccxt_error_decorator_success(self):
        """测试装饰器在正常情况下的行为"""
        @handle_ccxt_error
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_handle_ccxt_error_decorator_network_error(self):
        """测试网络错误处理"""
        @handle_ccxt_error
        def test_function():
            raise ccxt.NetworkError("网络连接失败")
        
        with pytest.raises(Exception) as exc_info:
            test_function()
        
        # 验证错误信息包含网络错误提示
        assert "网络连接失败" in str(exc_info.value)
    
    def test_handle_ccxt_error_decorator_auth_error(self):
        """测试认证错误处理"""
        @handle_ccxt_error 
        def test_function():
            raise ccxt.AuthenticationError("API密钥无效")
        
        with pytest.raises(Exception) as exc_info:
            test_function()
        
        assert "API密钥无效" in str(exc_info.value)
    
    def test_handle_ccxt_error_decorator_generic_error(self):
        """测试通用错误处理"""
        @handle_ccxt_error
        def test_function():
            raise ValueError("普通错误")
        
        # 非ccxt错误会被包装成RuntimeError
        with pytest.raises(RuntimeError, match="工具执行失败"):
            test_function()


@pytest.mark.unit
class TestToolsErrorHandling:
    """测试工具类的错误处理"""
    
    def test_create_order_with_ccxt_error(self, tools_with_mock_exchange):
        """测试订单创建时的ccxt错误处理"""
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.create_order.side_effect = ccxt.InsufficientFunds("余额不足")
        
        with pytest.raises(Exception) as exc_info:
            tools_with_mock_exchange.create_spot_order(
                'test_account', 'BTC/USDT', 'buy', 0.01, 50000
            )
        
        assert "余额不足" in str(exc_info.value)
    
    def test_get_balance_with_auth_error(self, tools_with_mock_exchange):
        """测试获取余额时的认证错误"""
        mock_exchange = tools_with_mock_exchange._get_exchange('test_account')
        mock_exchange.fetch_balance.side_effect = ccxt.AuthenticationError("API密钥无效")
        
        with pytest.raises(Exception) as exc_info:
            tools_with_mock_exchange.get_balance('test_account')
        
        assert "API密钥无效" in str(exc_info.value)