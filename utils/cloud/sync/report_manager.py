"""
Report Sync Manager for GAS_STATION_POS_v2
報表同步管理功能
"""
import os
import logging
from typing import Tuple
from utils.common import REPORTS_PATH
from utils.cloud.sync.base_manager import BaseSyncManager

# 設置日誌
logger = logging.getLogger(__name__)

class ReportSyncManager(BaseSyncManager):
    """
    報表同步管理類
    專門用於報表文件的同步管理
    """
    
    def sync_reports(self) -> Tuple[int, int]:
        """
        同步報表文件
        
        返回:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        # 檢查網絡連接
        if not self.update_connection_status():
            logger.warning("網絡連接不可用，無法同步報表")
            return (0, 0)
        
        # 檢查報表目錄是否存在
        if not os.path.exists(REPORTS_PATH):
            logger.warning(f"報表目錄不存在: {REPORTS_PATH}")
            return (0, 0)
        
        success_count = 0
        fail_count = 0
        
        # 遍歷報表目錄
        for root, dirs, files in os.walk(REPORTS_PATH):
            # 獲取相對路徑
            rel_path = os.path.relpath(root, REPORTS_PATH)
            remote_dir = f"reports/{rel_path}" if rel_path != '.' else "reports"
            
            # 確保雲端目錄存在
            if not self.drive_connector.ensure_directory(remote_dir):
                logger.error(f"創建雲端目錄失敗: {remote_dir}")
                fail_count += len(files)
                continue
            
            # 同步文件
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = f"{remote_dir}/{file_name}"
                
                try:
                    # 上傳文件
                    file_id = self.drive_connector.upload_file(local_file_path, None, remote_file_path)
                    
                    if file_id:
                        logger.info(f"報表同步成功: {remote_file_path}")
                        success_count += 1
                    else:
                        logger.error(f"報表同步失敗: {remote_file_path}")
                        fail_count += 1
                except Exception as e:
                    logger.error(f"同步報表時出錯 {remote_file_path}: {str(e)}")
                    fail_count += 1
        
        return (success_count, fail_count)
    
    def download_reports(self, remote_dir="reports", local_dir=None) -> Tuple[int, int]:
        """
        從雲端下載報表文件
        
        參數:
            remote_dir (str): 雲端報表目錄
            local_dir (str): 本地保存目錄，預設為REPORTS_PATH
            
        返回:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        if local_dir is None:
            local_dir = REPORTS_PATH
        
        # 檢查網絡連接
        if not self.update_connection_status():
            logger.warning("網絡連接不可用，無法下載報表")
            return (0, 0)
        
        # 確保本地目錄存在
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        try:
            # 獲取雲端目錄中的所有文件
            files = self.drive_connector.list_files_in_folder(remote_dir)
            
            for file in files:
                file_name = file.get('name')
                file_id = file.get('id')
                
                if not file_name or not file_id:
                    continue
                
                # 如果是目錄，遞歸下載
                if file.get('mimeType') == 'application/vnd.google-apps.folder':
                    sub_remote_dir = f"{remote_dir}/{file_name}"
                    sub_local_dir = os.path.join(local_dir, file_name)
                    
                    # 確保子目錄存在
                    if not os.path.exists(sub_local_dir):
                        os.makedirs(sub_local_dir, exist_ok=True)
                    
                    # 遞歸下載子目錄
                    sub_success, sub_fail = self.download_reports(sub_remote_dir, sub_local_dir)
                    success_count += sub_success
                    fail_count += sub_fail
                else:
                    # 下載文件
                    local_file_path = os.path.join(local_dir, file_name)
                    
                    # 檢查是否需要下載（如果本地文件較新則跳過）
                    need_download = True
                    if os.path.exists(local_file_path):
                        local_mod_time = os.path.getmtime(local_file_path)
                        remote_mod_time = self.drive_connector.get_file_modified_time(file_id)
                        
                        if remote_mod_time is None:
                            need_download = True
                        elif isinstance(remote_mod_time, str):
                            import dateutil.parser
                            remote_mod_time = dateutil.parser.parse(remote_mod_time).timestamp()
                            need_download = remote_mod_time > local_mod_time
                    
                    if need_download:
                        success = self.drive_connector.download_file(file_id, local_file_path)
                        
                        if success:
                            logger.info(f"報表下載成功: {file_name}")
                            success_count += 1
                        else:
                            logger.error(f"報表下載失敗: {file_name}")
                            fail_count += 1
                    else:
                        logger.info(f"報表已是最新，跳過下載: {file_name}")
                        success_count += 1
        
        except Exception as e:
            logger.error(f"下載報表時出錯: {str(e)}")
            fail_count += 1
        
        return (success_count, fail_count)
