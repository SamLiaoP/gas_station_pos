"""
SQLite Cloud Manager for cloud integrations
雲端同步相關的SQLite資料庫管理功能
"""
import os
import time
import logging
from typing import Optional, Dict, List, Any
from utils.cloud.sqlite.base_manager import BaseSQLiteManager

# 設置日誌
logger = logging.getLogger(__name__)

class CloudSQLiteManager(BaseSQLiteManager):
    """
    雲端SQLite資料庫管理類
    提供同步、雲端備份和還原等功能
    """
    
    def upload_database(self, local_path: Optional[str] = None, remote_path: Optional[str] = None) -> bool:
        """
        上傳本地資料庫到雲端
        
        參數:
            local_path (str, optional): 本地資料庫路徑，預設為self.local_db_path
            remote_path (str, optional): 雲端保存路徑，預設為self.remote_db_path
            
        返回:
            bool: 是否成功上傳
        """
        try:
            local_path = local_path or self.local_db_path
            remote_path = remote_path or self.remote_db_path
            
            # 確保本地資料庫存在
            if not os.path.exists(local_path):
                logger.error(f"本地資料庫不存在: {local_path}")
                return False
            
            # 創建資料庫備份
            self.backup_local_database()
            
            # 上傳資料庫文件
            file_id = self.drive_connector.upload_file(local_path, None, remote_path)
            
            if file_id:
                logger.info(f"已成功上傳資料庫到雲端: {remote_path}")
                return True
            else:
                logger.error(f"上傳資料庫到雲端失敗: {remote_path}")
                return False
            
        except Exception as e:
            logger.error(f"上傳資料庫時出錯: {str(e)}")
            return False
    
    def download_database(self, remote_path: Optional[str] = None, local_path: Optional[str] = None) -> bool:
        """
        從雲端下載資料庫
        
        參數:
            remote_path (str, optional): 雲端資料庫路徑，預設為self.remote_db_path
            local_path (str, optional): 本地保存路徑，預設為self.local_db_path
            
        返回:
            bool: 是否成功下載
        """
        try:
            remote_path = remote_path or self.remote_db_path
            local_path = local_path or self.local_db_path
            
            # 如果本地資料庫存在，先備份
            if os.path.exists(local_path):
                self.backup_local_database()
            
            # 下載資料庫文件
            success = self.drive_connector.download_file_by_path(remote_path, local_path)
            
            if success:
                logger.info(f"已成功從雲端下載資料庫: {remote_path}")
                return True
            else:
                logger.error(f"從雲端下載資料庫失敗: {remote_path}")
                return False
            
        except Exception as e:
            logger.error(f"下載資料庫時出錯: {str(e)}")
            return False
    
    def synchronize_database(self, force_direction: Optional[str] = None) -> bool:
        """
        同步本地和雲端資料庫
        
        參數:
            force_direction (str, optional): 
                - 'upload': 強制上傳本地到雲端
                - 'download': 強制下載雲端到本地
                - None: 自動比較修改時間，較新的覆蓋較舊的
                
        返回:
            bool: 是否成功同步
        """
        try:
            if force_direction == 'upload':
                return self.upload_database()
            elif force_direction == 'download':
                return self.download_database()
            
            # 自動決定同步方向
            local_exists = os.path.exists(self.local_db_path)
            remote_exists = self.drive_connector.is_file_exists_by_path(self.remote_db_path)
            
            # 如果只有一方存在，直接同步
            if local_exists and not remote_exists:
                logger.info("本地資料庫存在但雲端不存在，執行上傳")
                return self.upload_database()
            elif not local_exists and remote_exists:
                logger.info("雲端資料庫存在但本地不存在，執行下載")
                return self.download_database()
            elif not local_exists and not remote_exists:
                logger.error("本地和雲端資料庫都不存在，無法同步")
                return False
            
            # 兩者都存在，比較修改時間
            local_mod_time = os.path.getmtime(self.local_db_path)
            remote_mod_time = self.drive_connector.get_file_modified_time_by_path(self.remote_db_path)
            
            if remote_mod_time is None:
                logger.error("無法獲取雲端資料庫修改時間")
                return False
            
            # 轉換雲端時間為時間戳
            if isinstance(remote_mod_time, str):
                import dateutil.parser
                remote_mod_time = dateutil.parser.parse(remote_mod_time).timestamp()
            
            # 比較修改時間（增加30秒容忍度）
            if local_mod_time > remote_mod_time + 30:
                logger.info("本地資料庫較新，執行上傳")
                return self.upload_database()
            elif remote_mod_time > local_mod_time + 30:
                logger.info("雲端資料庫較新，執行下載")
                return self.download_database()
            else:
                logger.info("本地和雲端資料庫時間相近，無需同步")
                return True
            
        except Exception as e:
            logger.error(f"同步資料庫時出錯: {str(e)}")
            return False
    
    def backup_to_cloud(self, backup_name: Optional[str] = None) -> bool:
        """
        備份資料庫到雲端
        
        參數:
            backup_name (str, optional): 備份檔案名稱，預設使用時間戳
            
        返回:
            bool: 是否成功備份
        """
        try:
            # 先建立本地備份
            if backup_name is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"gas_station_backup_{timestamp}.db"
            
            local_backup_path = self.backup_local_database(backup_name)
            
            if not local_backup_path:
                return False
            
            # 上傳備份到雲端
            remote_backup_path = f"data/backup/{backup_name}"
            
            # 確保雲端備份目錄存在
            self.drive_connector.ensure_directory("data/backup")
            
            # 上傳備份
            file_id = self.drive_connector.upload_file(local_backup_path, None, remote_backup_path)
            
            if file_id:
                logger.info(f"已成功上傳備份到雲端: {remote_backup_path}")
                return True
            else:
                logger.error(f"上傳備份到雲端失敗: {remote_backup_path}")
                return False
            
        except Exception as e:
            logger.error(f"備份資料庫到雲端時出錯: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_name: str, is_cloud_backup: bool = False) -> bool:
        """
        從備份還原資料庫
        
        參數:
            backup_name (str): 備份檔案名稱
            is_cloud_backup (bool): 是否為雲端備份
            
        返回:
            bool: 是否成功還原
        """
        try:
            # 先備份當前資料庫
            current_backup = self.backup_local_database()
            
            if is_cloud_backup:
                # 從雲端下載備份
                remote_backup_path = f"data/backup/{backup_name}"
                temp_backup_path = os.path.join(self.backup_dir, f"temp_{backup_name}")
                
                success = self.drive_connector.download_file_by_path(remote_backup_path, temp_backup_path)
                
                if not success:
                    logger.error(f"從雲端下載備份失敗: {remote_backup_path}")
                    return False
                
                backup_path = temp_backup_path
            else:
                # 使用本地備份
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                if not os.path.exists(backup_path):
                    logger.error(f"本地備份不存在: {backup_path}")
                    return False
            
            # 備份資料庫恢復前，需要先關閉所有連接
            self._close_all_connections()
            
            # 還原備份到主資料庫
            import shutil
            shutil.copy2(backup_path, self.local_db_path)
            logger.info(f"已從備份還原資料庫: {backup_name}")
            
            # 如果是從雲端下載的臨時備份，清理它
            if is_cloud_backup and os.path.exists(temp_backup_path):
                os.remove(temp_backup_path)
            
            return True
            
        except Exception as e:
            logger.error(f"還原資料庫時出錯: {str(e)}")
            # 嘗試恢復之前的資料庫
            if current_backup and os.path.exists(current_backup):
                try:
                    import shutil
                    shutil.copy2(current_backup, self.local_db_path)
                    logger.info(f"已恢復到還原前的資料庫")
                except:
                    pass
            return False
    
    def list_backups(self, include_cloud: bool = True) -> Dict[str, List[str]]:
        """
        列出所有可用的備份
        
        參數:
            include_cloud (bool): 是否包含雲端備份
            
        返回:
            Dict[str, List[str]]: 備份列表 {'local': [...], 'cloud': [...]}
        """
        result = {'local': [], 'cloud': []}
        
        try:
            # 列出本地備份
            if os.path.exists(self.backup_dir):
                for file in os.listdir(self.backup_dir):
                    if file.startswith("gas_station_backup_") and file.endswith(".db"):
                        result['local'].append(file)
                
                # 按修改時間排序（最新的在前）
                result['local'].sort(key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)), reverse=True)
            
            # 列出雲端備份
            if include_cloud:
                cloud_backups = self.drive_connector.list_files_in_folder("data/backup")
                for file in cloud_backups:
                    if file.get('name', '').startswith("gas_station_backup_") and file.get('name', '').endswith(".db"):
                        result['cloud'].append(file.get('name'))
                
                # 按修改時間排序（最新的在前）
                result['cloud'].sort(key=lambda x: self.drive_connector.get_file_modified_time_by_name("data/backup", x) or 0, reverse=True)
            
        except Exception as e:
            logger.error(f"列出備份時出錯: {str(e)}")
        
        return result
    
    def create_share_link(self) -> Optional[str]:
        """
        為雲端資料庫創建分享連結
        
        返回:
            Optional[str]: 分享連結，如果失敗則為None
        """
        return self.drive_connector.create_share_link_by_path(self.remote_db_path)
