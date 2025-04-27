"""
SQLite Base Manager for cloud integrations
基本的SQLite資料庫管理功能
"""
import os
import time
import sqlite3
import shutil
import logging
from typing import Optional
from utils.cloud.google_drive_connector import GoogleDriveConnector

# 設置日誌
logger = logging.getLogger(__name__)

class BaseSQLiteManager:
    """
    基本的SQLite資料庫管理類
    提供本地資料庫操作的基礎功能
    """
    
    def __init__(self, drive_connector: GoogleDriveConnector = None):
        """
        初始化基本SQLite管理器
        
        參數:
            drive_connector (GoogleDriveConnector, optional): Google Drive連接器實例
        """
        self.drive_connector = drive_connector or GoogleDriveConnector()
        # 確保連接器已經認證
        if not self.drive_connector.authorized:
            self.drive_connector.authenticate()
        
        # 本地資料庫路徑
        self.local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                                         'data', 'gas_station.db')
        
        # 雲端資料庫路徑
        self.remote_db_path = 'data/gas_station.db'
        
        # 備份目錄
        self.backup_dir = os.path.join(os.path.dirname(self.local_db_path), 'backup')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def backup_local_database(self, backup_name: Optional[str] = None) -> str:
        """
        備份本地資料庫
        
        參數:
            backup_name (str, optional): 備份檔案名稱，預設使用時間戳
            
        返回:
            str: 備份檔案路徑，如果失敗則為空字串
        """
        try:
            if not os.path.exists(self.local_db_path):
                logger.warning(f"本地資料庫不存在，無法備份: {self.local_db_path}")
                return ""
            
            # 生成備份文件名
            if backup_name is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"gas_station_backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 建立備份目錄
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 使用shutil複製文件
            shutil.copy2(self.local_db_path, backup_path)
            logger.info(f"已備份本地資料庫到: {backup_path}")
            
            # 保留最近20個備份，刪除舊的
            self._cleanup_old_backups(20)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"備份本地資料庫時出錯: {str(e)}")
            return ""
    
    def _cleanup_old_backups(self, keep_count: int = 20) -> None:
        """
        清理舊的備份，只保留最近的指定數量
        
        參數:
            keep_count (int): 要保留的備份數量
        """
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # 獲取所有備份
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("gas_station_backup_") and file.endswith(".db"):
                    backups.append(file)
            
            # 如果備份數量未超過保留數量，直接返回
            if len(backups) <= keep_count:
                return
            
            # 按修改時間排序（最舊的在前）
            backups.sort(key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)))
            
            # 刪除多餘的舊備份
            for i in range(len(backups) - keep_count):
                try:
                    os.remove(os.path.join(self.backup_dir, backups[i]))
                    logger.info(f"已刪除舊備份: {backups[i]}")
                except Exception as e:
                    logger.error(f"刪除舊備份時出錯: {backups[i]}, {str(e)}")
            
        except Exception as e:
            logger.error(f"清理舊備份時出錯: {str(e)}")
    
    def _close_all_connections(self) -> None:
        """
        關閉所有到資料庫的連接（用於備份還原時）
        """
        try:
            # 嘗試連接資料庫並使用PRAGMA命令獲取連接信息
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # 使用WAL模式的資料庫可以使用以下命令來確保所有連接都已關閉
            cursor.execute("PRAGMA wal_checkpoint(FULL);")
            
            # 關閉連接
            cursor.close()
            conn.close()
            
            # 等待一小段時間確保連接正確關閉
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"關閉資料庫連接時出錯: {str(e)}")
