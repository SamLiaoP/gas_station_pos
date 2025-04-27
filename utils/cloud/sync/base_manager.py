"""
Base Sync Manager for GAS_STATION_POS_v2
基本的同步管理功能
"""
import os
import time
import json
import logging
from utils.common import DATA_PATH
from utils.cloud.google_drive_connector import GoogleDriveConnector

# 設置日誌
logger = logging.getLogger(__name__)

class BaseSyncManager:
    """
    基本的同步管理類
    提供同步狀態管理和網絡連接檢查功能
    """
    
    def __init__(self, 
                 drive_connector: GoogleDriveConnector = None,
                 sync_status_path: str = 'sync_status.json',
                 cache_dir: str = 'cache'):
        """
        初始化基本同步管理器
        
        參數:
            drive_connector: Google Drive連接器實例
            sync_status_path: 同步狀態文件的路徑
            cache_dir: 緩存目錄的路徑
        """
        self.drive_connector = drive_connector or GoogleDriveConnector()
        
        # 同步狀態文件路徑
        self.sync_status_path = os.path.join(DATA_PATH, sync_status_path)
        
        # 創建緩存目錄
        self.cache_dir = os.path.join(DATA_PATH, cache_dir)
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加載同步狀態
        self.sync_status = self._load_sync_status()
        
        # 網絡連接狀態
        self.is_connected = self._check_connection()
        
        # 本地資料庫路徑
        self.db_path = os.path.join(DATA_PATH, 'gas_station.db')
    
    def _load_sync_status(self):
        """
        加載同步狀態文件
        
        返回:
            dict: 同步狀態數據
        """
        if os.path.exists(self.sync_status_path):
            try:
                with open(self.sync_status_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"讀取同步狀態文件時出錯: {str(e)}")
        
        # 返回默認狀態
        return {
            "last_sync_time": 0,
            "last_sync_direction": None,
            "last_sync_status": "none",
            "pending_changes": False,
            "conflict_detected": False,
            "last_connection_check": 0,
            "is_connected": False,
            "last_backup_time": 0,
            "backup_count": 0
        }
    
    def _save_sync_status(self):
        """
        保存同步狀態文件
        
        返回:
            bool: 是否成功保存
        """
        try:
            with open(self.sync_status_path, 'w', encoding='utf-8') as f:
                json.dump(self.sync_status, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存同步狀態文件時出錯: {str(e)}")
            return False
    
    def _check_connection(self):
        """
        檢查網絡連接狀態
        
        返回:
            bool: 是否連接正常
        """
        # 檢查上次連接檢查時間，避免頻繁檢查
        current_time = time.time()
        last_check = self.sync_status.get("last_connection_check", 0)
        
        # 如果距離上次檢查不足30秒，使用上次的結果
        if current_time - last_check < 30:
            return self.sync_status.get("is_connected", False)
        
        # 否則進行新的檢查
        is_connected = self.drive_connector.check_connection()
        
        # 更新狀態
        self.sync_status["last_connection_check"] = current_time
        self.sync_status["is_connected"] = is_connected
        self._save_sync_status()
        
        return is_connected
    
    def update_connection_status(self):
        """
        更新網絡連接狀態
        
        返回:
            bool: 更新後的連接狀態
        """
        self.is_connected = self._check_connection()
        return self.is_connected
    
    def get_sync_status(self):
        """
        獲取同步狀態
        
        返回:
            dict: 同步狀態
        """
        # 更新網絡連接狀態
        self.update_connection_status()
        
        # 檢查本地資料庫是否已修改
        if os.path.exists(self.db_path):
            last_modified = os.path.getmtime(self.db_path)
            last_sync = self.sync_status.get("last_sync_time", 0)
            
            # 如果最後修改時間晚於最後同步時間，標記有未同步的變更
            if last_modified > last_sync:
                self.sync_status["pending_changes"] = True
                self._save_sync_status()
        
        return self.sync_status
    
    def mark_pending_changes(self):
        """
        標記有未同步的變更
        """
        self.sync_status["pending_changes"] = True
        self._save_sync_status()
    
    def _format_size(self, size_bytes):
        """
        格式化文件大小
        
        參數:
            size_bytes (int): 文件大小（字節）
            
        返回:
            str: 格式化後的大小
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
