"""
Cloud Configuration Manager for GAS_STATION_POS_v2
Handles cloud integration settings and configuration
"""
import os
import json
import logging
from typing import Dict, Any, Optional

# 設置日誌
logger = logging.getLogger(__name__)

class CloudConfigManager:
    """
    處理雲端整合配置的類
    """
    _instance = None
    DEFAULT_CONFIG_PATH = 'config/cloud_config.json'
    
    # 使用Singleton模式確保配置只被加載一次
    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(CloudConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path=None):
        # 避免重複初始化
        if getattr(self, '_initialized', False):
            return
        
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self._initialized = True
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加載雲端配置
        
        返回:
            Dict[str, Any]: 配置字典
        """
        default_config = {
            "use_cloud": False,
            "credentials_path": "config/credentials.json",
            "token_path": "config/token.pickle",
            "root_folder_name": "GAS_STATION_POS",
            "data_folder_name": "data",
            "reports_folder_name": "reports",
            "cache_enabled": True,
            "cache_max_age": 300,
            "sync_check_interval": 60,
            "conflict_resolution_strategy": "cloud_wins",
            "retry_attempts": 3,
            "retry_delay": 5
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合併默認配置和加載的配置
                    merged_config = {**default_config, **loaded_config}
                    logger.info(f"已加載雲端配置: {self.config_path}")
                    return merged_config
            else:
                # 創建默認配置文件
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                logger.info(f"已創建默認雲端配置: {self.config_path}")
                return default_config
        except Exception as e:
            logger.error(f"加載雲端配置時出錯: {str(e)}")
            return default_config
    
    def save_config(self) -> bool:
        """
        保存當前配置到配置文件
        
        返回:
            bool: 是否成功保存
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"已保存雲端配置: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存雲端配置時出錯: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取配置項的值
        
        參數:
            key (str): 配置項鍵名
            default (Any, optional): 默認值
            
        返回:
            Any: 配置項的值
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        設置配置項的值
        
        參數:
            key (str): 配置項鍵名
            value (Any): 新值
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        更新多個配置項
        
        參數:
            config_dict (Dict[str, Any]): 配置字典
        """
        self.config.update(config_dict)
    
    def toggle_cloud_mode(self, enabled: bool = None) -> bool:
        """
        切換雲端模式
        
        參數:
            enabled (bool, optional): 是否啟用雲端模式，如果為None則切換當前狀態
            
        返回:
            bool: 切換後的狀態
        """
        if enabled is None:
            enabled = not self.get("use_cloud", False)
        
        self.set("use_cloud", enabled)
        self.save_config()
        
        if enabled:
            logger.info("已啟用雲端模式")
        else:
            logger.info("已停用雲端模式")
        
        return enabled
    
    def is_cloud_mode(self) -> bool:
        """
        檢查是否處於雲端模式
        
        返回:
            bool: 是否啟用雲端模式
        """
        return self.get("use_cloud", False)
