"""
简化的Broker ID注入工厂单元测试
"""

import pytest
from unittest.mock import Mock, patch
import ccxt

from binance_mcp.broker import BinanceExchangeFactory


@pytest.mark.unit
class TestBinanceExchangeFactory:
    """BinanceExchangeFactory单元测试"""
    
    def test_broker_ids_configuration(self):
        """测试broker ID配置"""
        expected_broker_ids = {
            'spot': 'C96E9MGA',
            'margin': 'C96E9MGA', 
            'future': 'eFC56vBf',
            'delivery': 'eFC56vBf',
            'swap': 'eFC56vBf',
            'option': 'eFC56vBf',
            'inverse': 'eFC56vBf'
        }
        
        assert BinanceExchangeFactory.BROKER_IDS == expected_broker_ids
    
    @patch('ccxt.binance')
    def test_create_exchange_success(self, mock_binance_class):
        """测试成功创建exchange"""
        # 设置mock对象
        mock_exchange = Mock()
        mock_exchange.options = {
            'broker': BinanceExchangeFactory.BROKER_IDS.copy(),
            'defaultType': 'spot'
        }
        mock_binance_class.return_value = mock_exchange
        
        config = {
            'api_key': 'test_key',
            'secret': 'test_secret',
            'sandbox': True
        }
        
        result = BinanceExchangeFactory.create_exchange(config)
        
        # 验证调用参数
        call_args = mock_binance_class.call_args[0][0]
        assert call_args['apiKey'] == 'test_key'
        assert call_args['secret'] == 'test_secret'
        assert call_args['sandbox'] is True
        assert call_args['enableRateLimit'] is True
        assert 'broker' in call_args['options']
        assert call_args['options']['defaultType'] == 'spot'
        
        assert result == mock_exchange
    
    def test_missing_api_key_raises_error(self):
        """测试缺少API key时抛出错误"""
        config = {
            'secret': 'test_secret'
        }
        
        with pytest.raises(ValueError, match="账户配置缺少必要字段: api_key"):
            BinanceExchangeFactory.create_exchange(config)
    
    def test_missing_secret_raises_error(self):
        """测试缺少secret时抛出错误"""
        config = {
            'api_key': 'test_key'
        }
        
        with pytest.raises(ValueError, match="账户配置缺少必要字段: secret"):
            BinanceExchangeFactory.create_exchange(config)
    
    @patch('ccxt.binance')
    def test_create_exchange_error_handling(self, mock_binance_class):
        """测试exchange创建时的错误处理"""
        mock_binance_class.side_effect = ccxt.BaseError("API创建失败")
        
        config = {
            'api_key': 'invalid_key',
            'secret': 'invalid_secret'
        }
        
        with pytest.raises(RuntimeError, match="创建Binance交易所实例失败"):
            BinanceExchangeFactory.create_exchange(config)
    
    def test_get_broker_info(self):
        """测试获取broker信息"""
        broker_info = BinanceExchangeFactory.get_broker_info()
        
        assert isinstance(broker_info, dict)
        assert broker_info['spot'] == 'C96E9MGA'
        assert broker_info['future'] == 'eFC56vBf'
        
        # 验证返回的是副本
        broker_info['spot'] = 'modified'
        assert BinanceExchangeFactory.BROKER_IDS['spot'] == 'C96E9MGA'
    
    def test_get_supported_market_types(self):
        """测试获取支持的市场类型"""
        market_types = BinanceExchangeFactory.get_supported_market_types()
        
        expected_types = ['spot', 'margin', 'future', 'delivery', 'swap', 'option', 'inverse']
        assert set(market_types) == set(expected_types)
    
    @patch('ccxt.binance')
    def test_create_exchange_for_market_type_spot(self, mock_binance_class):
        """测试为现货市场创建exchange"""
        mock_exchange = Mock()
        mock_exchange.options = {'broker': BinanceExchangeFactory.BROKER_IDS.copy()}
        mock_binance_class.return_value = mock_exchange
        
        config = {'api_key': 'key', 'secret': 'secret'}
        
        result = BinanceExchangeFactory.create_exchange_for_market_type(config, 'spot')
        
        assert result == mock_exchange
        assert result.options['defaultType'] == 'spot'
    
    @patch('ccxt.binance')
    def test_create_exchange_for_market_type_future(self, mock_binance_class):
        """测试为期货市场创建exchange"""
        mock_exchange = Mock()
        mock_exchange.options = {'broker': BinanceExchangeFactory.BROKER_IDS.copy()}
        mock_binance_class.return_value = mock_exchange
        
        config = {'api_key': 'key', 'secret': 'secret'}
        
        result = BinanceExchangeFactory.create_exchange_for_market_type(config, 'future')
        
        assert result == mock_exchange
        assert result.options['defaultType'] == 'future'