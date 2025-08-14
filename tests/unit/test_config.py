"""
配置管理模块单元测试
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from binance_mcp.config import ConfigManager


@pytest.mark.unit
class TestConfigManager:
    """ConfigManager单元测试"""
    
    def test_encrypt_decrypt_value(self, config_manager):
        """测试值加密解密"""
        original_value = "test_api_key_123456"
        
        # 加密
        encrypted = config_manager.encrypt_value(original_value)
        assert encrypted != original_value
        assert isinstance(encrypted, str)
        
        # 解密
        decrypted = config_manager.decrypt_value(encrypted)
        assert decrypted == original_value
    
    def test_add_account(self, config_manager):
        """测试添加账户"""
        account_id = "test_account"
        api_key = "test_api_key"
        secret = "test_secret"
        
        # 添加账户
        config_manager.add_account(
            account_id=account_id,
            api_key=api_key,
            secret=secret,
            sandbox=True,
            description="测试账户"
        )
        
        # 验证账户已添加
        accounts = config_manager.list_accounts()
        assert account_id in accounts
        assert accounts[account_id]["sandbox"] is True
        assert accounts[account_id]["description"] == "测试账户"
    
    def test_add_duplicate_account_raises_error(self, config_manager):
        """测试添加重复账户抛出错误"""
        account_id = "test_account"
        
        # 先添加一个账户
        config_manager.add_account(account_id, "key1", "secret1")
        
        # 再次添加相同账户应该抛出错误
        with pytest.raises(ValueError, match="账户 .* 已存在"):
            config_manager.add_account(account_id, "key2", "secret2")
    
    def test_get_account(self, config_manager):
        """测试获取账户配置"""
        account_id = "test_account"
        api_key = "test_api_key"
        secret = "test_secret"
        
        # 添加账户
        config_manager.add_account(account_id, api_key, secret, sandbox=False)
        
        # 获取账户配置
        account_config = config_manager.get_account(account_id)
        
        assert account_config["api_key"] == api_key
        assert account_config["secret"] == secret
        assert account_config["sandbox"] is False
    
    def test_get_nonexistent_account_raises_error(self, config_manager):
        """测试获取不存在账户抛出错误"""
        with pytest.raises(ValueError, match="账户 .* 不存在"):
            config_manager.get_account("nonexistent_account")
    
    def test_remove_account(self, config_manager):
        """测试删除账户"""
        account_id = "test_account"
        
        # 添加账户
        config_manager.add_account(account_id, "key", "secret")
        assert account_id in config_manager.list_accounts()
        
        # 删除账户
        config_manager.remove_account(account_id)
        assert account_id not in config_manager.list_accounts()
    
    def test_remove_nonexistent_account_raises_error(self, config_manager):
        """测试删除不存在账户抛出错误"""
        with pytest.raises(ValueError, match="账户 .* 不存在"):
            config_manager.remove_account("nonexistent_account")
    
    def test_update_account(self, config_manager):
        """测试更新账户配置"""
        account_id = "test_account"
        
        # 添加账户
        config_manager.add_account(account_id, "old_key", "old_secret", False, "旧描述")
        
        # 更新账户
        new_api_key = "new_api_key"
        new_description = "新描述"
        config_manager.update_account(
            account_id, 
            api_key=new_api_key,
            description=new_description
        )
        
        # 验证更新
        account_config = config_manager.get_account(account_id)
        assert account_config["api_key"] == new_api_key
        assert account_config["secret"] == "old_secret"  # 未更新
        assert account_config["description"] == new_description
    
    def test_validate_account(self, config_manager):
        """测试账户配置验证"""
        account_id = "test_account"
        
        # 有效配置
        config_manager.add_account(account_id, "valid_key", "valid_secret")
        assert config_manager.validate_account(account_id) is True
        
        # 无效配置（空key）
        config_manager._config["accounts"][account_id]["api_key"] = config_manager.encrypt_value("")
        assert config_manager.validate_account(account_id) is False
        
        # 不存在的账户
        assert config_manager.validate_account("nonexistent") is False
    
    def test_server_config(self, config_manager):
        """测试服务器配置管理"""
        # 获取默认配置
        server_config = config_manager.get_server_config()
        assert server_config["port"] == 9001
        assert server_config["host"] == "127.0.0.1"
        
        # 更新配置
        config_manager.update_server_config(port=8080, host="0.0.0.0")
        
        updated_config = config_manager.get_server_config()
        assert updated_config["port"] == 8080
        assert updated_config["host"] == "0.0.0.0"
    
    def test_config_persistence(self, temp_config_dir):
        """测试配置持久化"""
        # 创建第一个配置管理器实例
        with patch('binance_mcp.config.Path.home', return_value=temp_config_dir):
            config1 = ConfigManager()
            config1.add_account("test_account", "test_key", "test_secret")
            account_config1 = config1.get_account("test_account")
        
        # 创建第二个实例，应该能读取到相同的配置
        with patch('binance_mcp.config.Path.home', return_value=temp_config_dir):
            config2 = ConfigManager()
            account_config2 = config2.get_account("test_account")
            
            assert account_config2["api_key"] == account_config1["api_key"]
            assert account_config2["secret"] == account_config1["secret"]
    
    def test_backup_config(self, config_manager, temp_config_dir):
        """测试配置备份"""
        # 添加一些配置
        config_manager.add_account("test_account", "key", "secret")
        
        # 备份配置
        backup_path = config_manager.backup_config(str(temp_config_dir / "backup.json"))
        
        # 验证备份文件存在
        assert Path(backup_path).exists()
        
        # 验证备份内容
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert "accounts" in backup_data
        assert "test_account" in backup_data["accounts"]
    
    def test_encryption_key_generation(self, temp_config_dir):
        """测试加密密钥生成和持久化"""
        with patch('binance_mcp.config.Path.home', return_value=temp_config_dir):
            # 第一次创建应该生成新密钥
            config1 = ConfigManager()
            key_file = config1.key_file
            assert key_file.exists()
            
            # 第二次创建应该使用现有密钥
            config2 = ConfigManager()
            
            # 两个实例应该能够相互解密数据
            test_value = "test_encryption"
            encrypted1 = config1.encrypt_value(test_value)
            decrypted2 = config2.decrypt_value(encrypted1)
            assert decrypted2 == test_value