"""
Cloud Synchronization Manager for GAS_STATION_POS_v2
Handles synchronization between local and cloud storage, manages caching, and resolves conflicts
"""
import os
import time
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple, Union
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.excel_manager import CloudExcelManager
from utils.common import DATA_PATH, REPORTS_PATH

# 設置日誌
logger = logging.getLogger(__name__)

class SyncManager:
    """
    管理本地和雲端數據同步的類
    處理網絡中斷、數據衝突和同步狀態
    """
    
    def __init__(self, 
                 drive_connector: GoogleDriveConnector = None,
                 excel_manager: CloudExcelManager = None,
                 sync_status_path: str = 'sync_status.json',
                 cache_dir: str = 'cache'):
        """
        初始化同步管理器
        
        參數:
            drive_connector: Google Drive連接器實例
            excel_manager: 雲端Excel管理器實例
            sync_status_path: 同步狀態文件的路徑
            cache_dir: 緩存目錄的路徑
        """
        self.drive_connector = drive_connector or GoogleDriveConnector()
        self.excel_manager = excel_manager or CloudExcelManager(self.drive_connector)
        
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
    
    def _load_sync_status(self) -> Dict[str, Any]:
        """
        加載同步狀態文件
        
        返回:
            Dict[str, Any]: 同步狀態數據
        """
        if os.path.exists(self.sync_status_path):
            try:
                with open(self.sync_status_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"讀取同步狀態文件時出錯: {str(e)}")
        
        # 返回默認狀態
        return {
            "last_sync": {},
            "pending_changes": [],
            "conflict_files": [],
            "last_connection_check": 0,
            "is_connected": False
        }
    
    def _save_sync_status(self) -> bool:
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
    
    def _check_connection(self) -> bool:
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
    
    def update_connection_status(self) -> bool:
        """
        更新網絡連接狀態
        
        返回:
            bool: 更新後的連接狀態
        """
        self.is_connected = self._check_connection()
        return self.is_connected
    
    def _get_local_modification_time(self, file_path: str) -> Optional[float]:
        """
        獲取本地文件的修改時間
        
        參數:
            file_path: 本地文件路徑
            
        返回:
            Optional[float]: 修改時間戳，如果文件不存在則為None
        """
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return None
    
    def _get_cached_cloud_modification_time(self, remote_path: str) -> Optional[str]:
        """
        從同步狀態獲取雲端文件的修改時間
        
        參數:
            remote_path: 雲端文件路徑
            
        返回:
            Optional[str]: 修改時間，如果不存在則為None
        """
        return self.sync_status.get("last_sync", {}).get(remote_path, {}).get("cloud_modified")
    
    def _update_sync_status(self, remote_path: str, local_path: str, 
                           cloud_modified: Optional[str] = None, 
                           local_modified: Optional[float] = None,
                           sync_direction: Optional[str] = None) -> None:
        """
        更新文件的同步狀態
        
        參數:
            remote_path: 雲端文件路徑
            local_path: 本地文件路徑
            cloud_modified: 雲端修改時間
            local_modified: 本地修改時間
            sync_direction: 同步方向 ('local_to_cloud', 'cloud_to_local', None)
        """
        if "last_sync" not in self.sync_status:
            self.sync_status["last_sync"] = {}
        
        # 獲取當前時間作為同步時間
        sync_time = time.time()
        
        # 如果未提供修改時間，則獲取當