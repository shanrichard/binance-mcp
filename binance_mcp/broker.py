"""
Broker ID注入工厂模块

负责创建带有自动broker ID注入的ccxt exchange实例，
确保所有交易都能获得返佣收益。
"""

import logging
from typing import Dict, Any
import ccxt

logger = logging.getLogger(__name__)


class BinanceExchangeFactory:
    """Binance交易所实例工厂"""
    
    # 硬编码的Broker ID配置
    BROKER_IDS = {
        'spot': 'C96E9MGA',       # 现货broker ID
        'margin': 'C96E9MGA',     # 保证金交易使用现货broker ID
        'future': 'eFC56vBf',     # USD-M期货broker ID
        'delivery': 'eFC56vBf',   # 币本位期货broker ID
        'swap': 'eFC56vBf',       # 永续合约broker ID
        'option': 'eFC56vBf',     # 期权broker ID
        'inverse': 'eFC56vBf',    # 反向合约broker ID
    }
    
    @classmethod
    def create_exchange(cls, account_config: Dict[str, Any]) -> ccxt.binance:
        """
        创建带有broker ID的Binance exchange实例
        
        Args:
            account_config: 账户配置，包含api_key, secret, sandbox等
            
        Returns:
            配置了broker ID的ccxt.binance实例
            
        Raises:
            ValueError: 当必要配置缺失时
            Exception: 当创建exchange失败时
        """
        # 验证必要配置
        required_fields = ['api_key', 'secret']
        for field in required_fields:
            if not account_config.get(field):
                raise ValueError(f"账户配置缺少必要字段: {field}")
        
        # 构建exchange配置
        exchange_config = {
            'apiKey': account_config['api_key'],
            'secret': account_config['secret'],
            'sandbox': account_config.get('sandbox', False),
            'enableRateLimit': True,  # 启用内置限流
            'options': {
                'broker': cls.BROKER_IDS.copy(),  # 注入broker ID配置
                # 其他可能的选项
                'defaultType': 'spot',  # 默认为现货交易
                # 检查是否启用统一账户模式
                'portfolioMargin': account_config.get('portfolio_margin', False),
            }
        }
        
        # 如果有passphrase（某些交易所需要）
        if 'passphrase' in account_config:
            exchange_config['password'] = account_config['passphrase']
        
        try:
            # 创建exchange实例
            exchange = ccxt.binance(exchange_config)
            
            # 验证broker ID注入是否成功
            cls._verify_broker_injection(exchange)
            
            logger.info(f"Created Binance exchange instance (sandbox: {account_config.get('sandbox', False)})")
            logger.debug(f"Broker IDs injected: {cls.BROKER_IDS}")
            
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to create Binance exchange: {e}")
            raise RuntimeError(f"创建Binance交易所实例失败: {e}")
    
    @classmethod
    def _verify_broker_injection(cls, exchange: ccxt.binance) -> None:
        """验证broker ID注入是否成功"""
        if 'broker' not in exchange.options:
            raise RuntimeError("Broker ID注入失败: options中未找到broker配置")
        
        injected_brokers = exchange.options['broker']
        for market_type, expected_broker in cls.BROKER_IDS.items():
            if injected_brokers.get(market_type) != expected_broker:
                logger.warning(
                    f"Broker ID可能未正确注入 - {market_type}: "
                    f"期望 {expected_broker}, 实际 {injected_brokers.get(market_type)}"
                )
    
    @classmethod
    def get_broker_info(cls) -> Dict[str, str]:
        """获取broker ID信息"""
        return cls.BROKER_IDS.copy()
    
    @classmethod
    def test_exchange_connection(cls, account_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        测试交易所连接
        
        Args:
            account_config: 账户配置
            
        Returns:
            连接测试结果
        """
        test_result = {
            'success': False,
            'error': None,
            'server_time': None,
            'account_info': None,
            'broker_injected': False
        }
        
        try:
            exchange = cls.create_exchange(account_config)
            
            # 测试公开API（获取服务器时间）
            try:
                server_time = exchange.fetch_time()
                test_result['server_time'] = server_time
                logger.info("Public API connection successful")
            except Exception as e:
                logger.warning(f"Public API test failed: {e}")
            
            # 测试私有API（获取账户信息）
            try:
                account_info = exchange.fetch_balance()
                test_result['account_info'] = {
                    'currencies': list(account_info.keys())[:5],  # 只返回前5个币种
                    'total_currencies': len(account_info)
                }
                logger.info("Private API connection successful")
            except Exception as e:
                logger.warning(f"Private API test failed: {e}")
                test_result['error'] = str(e)
                return test_result
            
            # 验证broker ID
            test_result['broker_injected'] = 'broker' in exchange.options
            test_result['success'] = True
            
        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"Exchange connection test failed: {e}")
        
        return test_result
    
    @classmethod
    def create_exchange_for_market_type(
        cls, 
        account_config: Dict[str, Any], 
        market_type: str = 'spot'
    ) -> ccxt.binance:
        """
        为特定市场类型创建exchange实例
        
        Args:
            account_config: 账户配置
            market_type: 市场类型 (spot, future, etc.)
            
        Returns:
            配置了特定市场类型的exchange实例
        """
        exchange = cls.create_exchange(account_config)
        
        # 根据市场类型设置默认选项
        if market_type in ['future', 'futures', 'swap']:
            exchange.options['defaultType'] = 'future'
        elif market_type in ['delivery', 'coin']:
            exchange.options['defaultType'] = 'delivery'  
        elif market_type == 'option':
            exchange.options['defaultType'] = 'option'
        else:
            exchange.options['defaultType'] = 'spot'
        
        logger.info(f"Created exchange for market type: {market_type}")
        return exchange
    
    @classmethod 
    def get_supported_market_types(cls) -> list:
        """获取支持的市场类型"""
        return list(cls.BROKER_IDS.keys())


# 全局工厂实例
exchange_factory = BinanceExchangeFactory()