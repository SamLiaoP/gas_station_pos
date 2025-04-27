"""
Sync Manager for GAS_STATION_POS_v2
Entry point for synchronization operations
"""
import time
from typing import Tuple
from utils.cloud.sync.base_manager import BaseSyncManager
from utils.cloud.sync.database_manager import DatabaseSyncManager
from utils.cloud.sync.report_manager import ReportSyncManager

class SyncManager(DatabaseSyncManager, ReportSyncManager):
    """
    同步管理類
    整合資料庫和報表同步功能
    """
    
    def auto_backup(self, interval_hours: int = 24) -> bool:
        """
        自動備份（如果距離上次備份超過指定時間）
        
        參數:
            interval_hours (int): 備份間隔時間（小時）
            
        返回:
            bool: 是否執行了備份
        """
        current_time = time.time()
        last_backup = self.sync_status.get("last_backup_time", 0)
        
        # 檢查是否需要備份
        if current_time - last_backup > interval_hours * 3600:
            # 執行備份
            success = self.backup_database()
            return success
        
        return False
    
    def auto_sync(self, schedule: str = 'immediate') -> bool:
        """
        根據同步計劃自動同步資料庫
        
        參數:
            schedule (str): 同步計劃 ('immediate', 'hourly', 'daily', 'weekly', 'manual')
            
        返回:
            bool: 是否執行了同步
        """
        # 如果是手動同步，直接返回
        if schedule == 'manual':
            return False
        
        # 檢查是否有未同步的變更
        has_changes = self.sync_status.get("pending_changes", False)
        if not has_changes:
            return False
        
        current_time = time.time()
        last_sync = self.sync_status.get("last_sync_time", 0)
        
        # 根據同步計劃檢查是否需要同步
        if schedule == 'immediate':
            # 立即同步
            return self.sync_database()
        elif schedule == 'hourly' and current_time - last_sync > 3600:
            # 每小時同步
            return self.sync_database()
        elif schedule == 'daily' and current_time - last_sync > 86400:
            # 每天同步
            return self.sync_database()
        elif schedule == 'weekly' and current_time - last_sync > 604800:
            # 每週同步
            return self.sync_database()
        
        return False
    
    def sync_all(self) -> Tuple[bool, Tuple[int, int]]:
        """
        同步所有數據（資料庫和報表）
        
        返回:
            Tuple[bool, Tuple[int, int]]: (資料庫同步結果, (報表成功數, 報表失敗數))
        """
        # 先同步資料庫
        db_success = self.sync_database()
        
        # 再同步報表
        report_success, report_fail = self.sync_reports()
        
        return (db_success, (report_success, report_fail))
