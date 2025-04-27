"""
Database Sync Manager for GAS_STATION_POS_v2
資料庫同步管理功能
"""
import os
import time
import logging
from typing import Tuple
from utils.cloud.sync.base_manager import BaseSyncManager
from utils.cloud.sqlite_manager import CloudSQLiteManager

# 設置日誌
logger = logging.getLogger(__name__)

class DatabaseSyncManager(BaseSyncManager):
    """
    資料庫同步管理類
    專門用於SQLite資料庫的同步管理
    """
    
    def __init__(self, *args, **kwargs):
        """初始化資料庫同步管理器"""
        super().__init__(*args, **kwargs)
        self.sqlite_manager = CloudSQLiteManager(self.drive_connector)
    
    def sync_database(self, force_direction=None) -> bool:
        """
        同步資料庫
        
        參數:
            force_direction (str, optional): 
                - 'upload': 強制上傳本地到雲端
                - 'download': 強制下載雲端到本地
                - None: 自動選擇同步方向
        
        返回:
            bool: 同步是否成功
        """
        # 檢查網絡連接
        if not self.update_connection_status():
            logger.warning("網絡連接不可用，無法同步資料庫")
            return False
        
        # 執行同步
        try:
            success = self.sqlite_manager.synchronize_database(force_direction)
            
            if success:
                # 更新同步狀態
                self.sync_status["last_sync_time"] = time.time()
                self.sync_status["last_sync_direction"] = force_direction or "auto"
                self.sync_status["last_sync_status"] = "success"
                self.sync_status["pending_changes"] = False
                self.sync_status["conflict_detected"] = False
                self._save_sync_status()
                
                logger.info("資料庫同步成功")
                return True
            else:
                # 更新同步狀態
                self.sync_status["last_sync_status"] = "failed"
                self._save_sync_status()
                
                logger.error("資料庫同步失敗")
                return False
                
        except Exception as e:
            logger.error(f"同步資料庫時出錯: {str(e)}")
            self.sync_status["last_sync_status"] = "error"
            self._save_sync_status()
            return False
    
    def backup_database(self) -> bool:
        """
        備份資料庫到雲端
        
        返回:
            bool: 備份是否成功
        """
        # 檢查網絡連接
        if not self.update_connection_status():
            logger.warning("網絡連接不可用，無法備份資料庫")
            return False
        
        # 執行備份
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"gas_station_backup_{timestamp}.db"
            
            success = self.sqlite_manager.backup_to_cloud(backup_name)
            
            if success:
                # 更新備份狀態
                self.sync_status["last_backup_time"] = time.time()
                self.sync_status["backup_count"] = self.sync_status.get("backup_count", 0) + 1
                self._save_sync_status()
                
                logger.info(f"資料庫備份成功: {backup_name}")
                return True
            else:
                logger.error("資料庫備份失敗")
                return False
                
        except Exception as e:
            logger.error(f"備份資料庫時出錯: {str(e)}")
            return False
    
    def restore_database(self, backup_name: str, is_cloud_backup: bool = False) -> bool:
        """
        從備份還原資料庫
        
        參數:
            backup_name (str): 備份檔案名稱
            is_cloud_backup (bool): 是否為雲端備份
            
        返回:
            bool: 還原是否成功
        """
        # 如果是雲端備份，需要檢查網絡連接
        if is_cloud_backup and not self.update_connection_status():
            logger.warning("網絡連接不可用，無法從雲端還原資料庫")
            return False
        
        # 執行還原
        try:
            # 從備份還原
            success = self.sqlite_manager.restore_from_backup(backup_name, is_cloud_backup)
            
            if success:
                # 同步本地數據到雲端
                if self.is_connected:
                    self.sync_database('upload')
                
                logger.info(f"從備份還原資料庫成功: {backup_name}")
                return True
            else:
                logger.error(f"從備份還原資料庫失敗: {backup_name}")
                return False
                
        except Exception as e:
            logger.error(f"還原資料庫時出錯: {str(e)}")
            return False
    
    def get_available_backups(self):
        """
        獲取可用的備份列表
        
        返回:
            dict: 備份列表 {'local': [...], 'cloud': [...]}
        """
        return self.sqlite_manager.list_backups(include_cloud=self.is_connected)
