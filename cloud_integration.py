"""
Google Drive 雲端整合模組 for GAS_STATION_POS_v2

提供主應用程式與 Google Drive 雲端儲存整合的功能。
這個模組用於初始化雲端整合，並提供切換本地/雲端模式的功能。
"""

import os
import logging
from utils.cloud.cloud_config_manager import CloudConfigManager
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.excel_manager import CloudExcelManager
from utils.common import DATA_PATH, REPORTS_PATH, logger

# 初始化雲端配置管理器
cloud_config = CloudConfigManager()

def init_cloud_integration():
    """
    初始化雲端整合
    
    返回:
        bool: 是否成功初始化
    """
    try:
        # 檢查是否啟用雲端模式
        if not cloud_config.is_cloud_mode():
            logger.info("雲端模式未啟用，使用本地檔案")
            return False
        
        # 初始化 Google Drive 連接器
        drive_connector = GoogleDriveConnector(
            credentials_path=cloud_config.get("credentials_path"),
            token_path=cloud_config.get("token_path")
        )
        
        # 嘗試認證
        if not drive_connector.authenticate():
            logger.warning("Google Drive 認證失敗，將使用本地檔案")
            cloud_config.toggle_cloud_mode(False)
            return False
        
        # 確保雲端目錄結構存在
        data_folder_path = cloud_config.get("data_folder_name")
        reports_folder_path = cloud_config.get("reports_folder_name")
        
        drive_connector.ensure_directory(data_folder_path)
        drive_connector.ensure_directory(reports_folder_path)
        
        logger.info("雲端整合初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"初始化雲端整合時出錯: {str(e)}")
        cloud_config.toggle_cloud_mode(False)
        return False

def toggle_cloud_mode(enabled=None):
    """
    切換雲端模式
    
    參數:
        enabled (bool, optional): 是否啟用雲端模式，如果為None則切換當前狀態
        
    返回:
        bool: 切換後的狀態
    """
    new_state = cloud_config.toggle_cloud_mode(enabled)
    
    if new_state:
        # 如果啟用了雲端模式，嘗試初始化
        success = init_cloud_integration()
        if not success:
            # 初始化失敗，回退到本地模式
            cloud_config.toggle_cloud_mode(False)
            return False
    
    return cloud_config.is_cloud_mode()

def is_cloud_mode():
    """
    檢查是否處於雲端模式
    
    返回:
        bool: 是否啟用雲端模式
    """
    return cloud_config.is_cloud_mode()

def check_cloud_connection():
    """
    檢查雲端連接狀態
    
    返回:
        bool: 連接是否正常
    """
    if not cloud_config.is_cloud_mode():
        return False
    
    try:
        drive_connector = GoogleDriveConnector(
            credentials_path=cloud_config.get("credentials_path"),
            token_path=cloud_config.get("token_path")
        )
        
        return drive_connector.check_connection()
    except Exception as e:
        logger.error(f"檢查雲端連接時出錯: {str(e)}")
        return False

def get_cloud_status():
    """
    獲取雲端狀態信息
    
    返回:
        dict: 狀態信息
    """
    if not cloud_config.is_cloud_mode():
        return {
            "enabled": False,
            "connected": False,
            "data_folder": None,
            "reports_folder": None
        }
    
    try:
        drive_connector = GoogleDriveConnector(
            credentials_path=cloud_config.get("credentials_path"),
            token_path=cloud_config.get("token_path")
        )
        
        connected = drive_connector.check_connection()
        
        if connected:
            data_folder = cloud_config.get("data_folder_name")
            reports_folder = cloud_config.get("reports_folder_name")
            
            # 檢查文件夾是否存在
            data_folder_id = drive_connector.get_folder_id(data_folder)
            reports_folder_id = drive_connector.get_folder_id(reports_folder)
            
            return {
                "enabled": True,
                "connected": True,
                "data_folder": {
                    "name": data_folder,
                    "exists": data_folder_id is not None,
                    "id": data_folder_id
                },
                "reports_folder": {
                    "name": reports_folder,
                    "exists": reports_folder_id is not None,
                    "id": reports_folder_id
                }
            }
        else:
            return {
                "enabled": True,
                "connected": False,
                "data_folder": None,
                "reports_folder": None
            }
            
    except Exception as e:
        logger.error(f"獲取雲端狀態時出錯: {str(e)}")
        return {
            "enabled": True,
            "connected": False,
            "error": str(e),
            "data_folder": None,
            "reports_folder": None
        }

# 應用啟動時初始化雲端整合
initialized = init_cloud_integration()
if initialized:
    logger.info("已啟用雲端模式")
else:
    logger.info("使用本地模式")
