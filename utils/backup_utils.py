import os
import shutil
import datetime
import logging
from utils.cloud.google_drive_connector import GoogleDriveConnector
from config import Config

logger = logging.getLogger(__name__)

def backup_database_to_gdrive():
    """
    將 SQLite 資料庫備份到 Google Drive。
    """
    db_path = Config.DB_PATH
    if not os.path.exists(db_path):
        logger.error(f"資料庫檔案不存在於 {db_path}")
        return

    backup_filename = f"gas_station_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # 建立本地備份副本
    temp_backup_path = os.path.join("data", backup_filename) # 暫存於 data 目錄
    try:
        shutil.copy2(db_path, temp_backup_path)
        logger.info(f"資料庫已成功複製到 {temp_backup_path}")
    except Exception as e:
        logger.error(f"建立本地資料庫備份失敗: {e}")
        return

    # 初始化 Google Drive 連接器
    gdrive_connector = GoogleDriveConnector(
        credentials_path=Config.GOOGLE_DRIVE_CREDENTIALS_PATH,
        token_path=Config.GOOGLE_DRIVE_TOKEN_PATH
    )

    if not gdrive_connector.authenticate():
        logger.error("Google Drive 認證失敗，無法備份資料庫。")
        if os.path.exists(temp_backup_path): # 清理臨時備份檔
            os.remove(temp_backup_path)
        return

    # 上傳備份檔案到 Google Drive 的 'data' 子目錄
    try:
        # 確保 'data' 子目錄存在於 Google Drive
        backup_subfolder_name = Config.GOOGLE_DRIVE_BACKUP_SUBFOLDER_NAME
        data_folder_id = gdrive_connector.get_or_create_subfolder(backup_subfolder_name)
        if not data_folder_id:
            logger.error(f"無法在 Google Drive 上找到或建立 '{backup_subfolder_name}' 子目錄。")
            if os.path.exists(temp_backup_path):
                 os.remove(temp_backup_path)
            return

        file_metadata = {'name': backup_filename, 'parents': [data_folder_id]}
        file_id = gdrive_connector.upload_file(temp_backup_path, backup_filename, remote_folder_id=data_folder_id)
        
        if file_id:
            logger.info(f"資料庫備份 '{backup_filename}' 已成功上傳到 Google Drive (ID: {file_id})")
            share_link = gdrive_connector.create_share_link(file_id)
            if share_link:
                logger.info(f"備份檔案分享連結: {share_link}")
        else:
            logger.error(f"上傳備份檔案 '{backup_filename}' 到 Google Drive 失敗")

    except Exception as e:
        logger.error(f"上傳資料庫備份到 Google Drive 時發生錯誤: {e}")
    finally:
        # 清理本地臨時備份檔案
        if os.path.exists(temp_backup_path):
            os.remove(temp_backup_path)
            logger.info(f"已刪除本地臨時備份檔案: {temp_backup_path}")

if __name__ == '__main__':
    # 方便手動測試
    # 需要確保環境變數和 Google Drive 設定正確
    # 例如: GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_DRIVE_TOKEN_PATH
    
    # 配置日誌記錄器以查看輸出
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 執行備份
    # backup_database_to_gdrive()
    # logger.info("手動備份測試完成。請檢查日誌和 Google Drive。")
    
    # 您可能需要先手動運行一次 setup_google_drive.py 來生成 token.pickle
    # 並將 credentials.json 放在 config/ 目錄下
    logger.info("要執行手動備份, 請取消註解 backup_database_to_gdrive() 並確保 Google Drive 已設定。") 