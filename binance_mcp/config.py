"""
配置管理模块

提供API密钥的加密存储、多账户管理、配置文件操作等功能。
所有敏感信息都会加密存储在本地配置文件中。
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path.home() / ".config" / "binance-mcp"
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化加密密钥
        self._cipher = Fernet(self._get_encryption_key())
        
        # 加载配置
        self._config = self._load_config()
    
    def _get_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # 生成新的加密密钥
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # 设置文件权限，只有所有者可读写
            os.chmod(self.key_file, 0o600)
            logger.info(f"Created new encryption key at {self.key_file}")
            return key
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            # 创建默认配置
            default_config = {
                "accounts": {},
                "server": {
                    "port": 9001,
                    "host": "127.0.0.1",
                    "log_level": "INFO"
                },
                "mcp": {
                    "server_name": "binance-mcp",
                    "version": "1.0.0"
                }
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config file: {e}")
            raise RuntimeError(f"无法加载配置文件: {e}")
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """保存配置文件"""
        config_to_save = config or self._config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            # 设置文件权限
            os.chmod(self.config_file, 0o600)
            logger.info("Configuration saved successfully")
        except IOError as e:
            logger.error(f"Failed to save config file: {e}")
            raise RuntimeError(f"无法保存配置文件: {e}")
    
    def encrypt_value(self, value: str) -> str:
        """加密字符串值"""
        return self._cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """解密字符串值"""
        try:
            return self._cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            raise RuntimeError(f"解密失败: {e}")
    
    def add_account(
        self,
        account_id: str,
        api_key: str,
        secret: str,
        sandbox: bool = False,
        description: str = ""
    ) -> None:
        """添加新账户"""
        if account_id in self._config["accounts"]:
            raise ValueError(f"账户 {account_id} 已存在")
        
        # 加密敏感信息
        encrypted_account = {
            "api_key": self.encrypt_value(api_key),
            "secret": self.encrypt_value(secret),
            "sandbox": sandbox,
            "description": description,
            "created_at": self._get_current_timestamp()
        }
        
        self._config["accounts"][account_id] = encrypted_account
        self._save_config()
        
        logger.info(f"Added account: {account_id}")
    
    def remove_account(self, account_id: str) -> None:
        """删除账户"""
        if account_id not in self._config["accounts"]:
            raise ValueError(f"账户 {account_id} 不存在")
        
        del self._config["accounts"][account_id]
        self._save_config()
        
        logger.info(f"Removed account: {account_id}")
    
    def get_account(self, account_id: str) -> Dict[str, Any]:
        """获取账户配置（解密后）"""
        if account_id not in self._config["accounts"]:
            raise ValueError(f"账户 {account_id} 不存在")
        
        encrypted_account = self._config["accounts"][account_id]
        
        # 解密敏感信息，同时保留所有其他配置项
        decrypted_account = {
            "api_key": self.decrypt_value(encrypted_account["api_key"]),
            "secret": self.decrypt_value(encrypted_account["secret"]),
        }
        
        # 复制所有非敏感配置项
        for key, value in encrypted_account.items():
            if key not in ["api_key", "secret"]:
                decrypted_account[key] = value
        
        return decrypted_account
    
    def list_accounts(self) -> Dict[str, Dict[str, Any]]:
        """列出所有账户（不包含敏感信息）"""
        accounts = {}
        for account_id, account_data in self._config["accounts"].items():
            accounts[account_id] = {
                "description": account_data.get("description", ""),
                "sandbox": account_data["sandbox"],
                "created_at": account_data.get("created_at", "")
            }
        return accounts
    
    def update_account(
        self,
        account_id: str,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        sandbox: Optional[bool] = None,
        description: Optional[str] = None
    ) -> None:
        """更新账户信息"""
        if account_id not in self._config["accounts"]:
            raise ValueError(f"账户 {account_id} 不存在")
        
        account = self._config["accounts"][account_id]
        
        if api_key is not None:
            account["api_key"] = self.encrypt_value(api_key)
        if secret is not None:
            account["secret"] = self.encrypt_value(secret)
        if sandbox is not None:
            account["sandbox"] = sandbox
        if description is not None:
            account["description"] = description
        
        account["updated_at"] = self._get_current_timestamp()
        
        self._save_config()
        logger.info(f"Updated account: {account_id}")
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self._config["server"].copy()
    
    def update_server_config(self, **kwargs) -> None:
        """更新服务器配置"""
        self._config["server"].update(kwargs)
        self._save_config()
        logger.info("Updated server configuration")
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """获取MCP配置"""
        return self._config["mcp"].copy()
    
    def interactive_setup(self) -> None:
        """交互式配置设置"""
        print("=== Binance MCP 配置向导 ===")
        print("请按提示输入API密钥信息\n")
        
        while True:
            account_id = input("账户ID (例如: main_account): ").strip()
            if not account_id:
                print("账户ID不能为空")
                continue
            
            if account_id in self._config["accounts"]:
                override = input(f"账户 {account_id} 已存在，是否覆盖？(y/N): ").strip().lower()
                if override != 'y':
                    continue
            
            print(f"\n配置账户: {account_id}")
            
            # API密钥
            api_key = input("API Key: ").strip()
            if not api_key:
                print("API Key不能为空")
                continue
            
            # Secret
            secret = input("Secret: ").strip()
            if not secret:
                print("Secret不能为空")
                continue
            
            # 沙盒模式
            sandbox_input = input("是否为沙盒环境? (y/N): ").strip().lower()
            sandbox = sandbox_input == 'y'
            
            # 描述
            description = input("账户描述 (可选): ").strip()
            
            try:
                # 添加账户
                if account_id in self._config["accounts"]:
                    self.update_account(account_id, api_key, secret, sandbox, description)
                else:
                    self.add_account(account_id, api_key, secret, sandbox, description)
                
                print(f"✓ 账户 {account_id} 配置成功")
                
            except Exception as e:
                print(f"✗ 配置失败: {e}")
                continue
            
            # 询问是否继续添加
            add_more = input("\n是否添加更多账户? (y/N): ").strip().lower()
            if add_more != 'y':
                break
        
        print(f"\n配置完成！配置文件保存在: {self.config_file}")
        print("使用 'binance-mcp list' 查看已配置的账户")
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_account(self, account_id: str) -> bool:
        """验证账户配置是否有效"""
        try:
            account = self.get_account(account_id)
            # 检查必要字段
            return bool(account.get("api_key") and account.get("secret"))
        except Exception:
            return False
    
    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return str(self.config_file)
    
    def backup_config(self, backup_path: Optional[str] = None) -> str:
        """备份配置文件"""
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.config_dir / f"config_backup_{timestamp}.json")
        
        import shutil
        shutil.copy2(self.config_file, backup_path)
        logger.info(f"Config backed up to: {backup_path}")
        return backup_path