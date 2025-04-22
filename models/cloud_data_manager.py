"""
雲端數據管理模組 for GAS_STATION_POS_v2
整合 Google Drive 雲端儲存功能的數據管理模組
"""
import os
import pandas as pd
from utils.common import DATA_PATH, logger
from utils.cloud.excel_manager import CloudExcelManager
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.cloud_config_manager import CloudConfigManager
from utils.cloud.sync_manager import SyncManager
from models.data_manager import ensure_excel_file

# 雲端配置管理器
cloud_config = CloudConfigManager()
drive_connector = GoogleDriveConnector(
    credentials_path=cloud_config.get("credentials_path"),
    token_path=cloud_config.get("token_path")
)
excel_manager = CloudExcelManager(drive_connector)
sync_manager = SyncManager(drive_connector, excel_manager, cloud_config)

# 讀取主數據文件中的指定sheet
def read_master_data(sheet_name):
    """
    從雲端或本地讀取主數據文件中的指定工作表

    參數:
        sheet_name (str): 工作表名稱

    返回:
        pandas.DataFrame: 讀取的數據
    """
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    remote_path = f"data/master_data.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 從雲端讀取
            df = excel_manager.read_excel_with_fallback(remote_path, master_data_path, sheet_name)
            if df is not None:
                return df
            logger.warning(f"從雲端讀取主數據 {sheet_name} 失敗，嘗試使用本地文件")
        
        # 本地模式或雲端讀取失敗，使用本地文件
        from models.data_manager import ensure_master_data
        ensure_master_data()  # 確保本地文件存在
        return pd.read_excel(master_data_path, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"讀取主數據 {sheet_name} 時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取庫存數據
def read_inventory():
    """
    從雲端或本地讀取庫存數據

    返回:
        pandas.DataFrame: 庫存數據
    """
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    remote_path = f"data/inventory.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 從雲端讀取
            df = excel_manager.read_excel_with_fallback(remote_path, inventory_path)
            if df is not None:
                return df
            logger.warning("從雲端讀取庫存數據失敗，嘗試使用本地文件")
        
        # 本地模式或雲端讀取失敗，使用本地文件
        from models.data_manager import ensure_inventory_data
        ensure_inventory_data()  # 確保本地文件存在
        return pd.read_excel(inventory_path)
    except Exception as e:
        logger.error(f"讀取庫存數據時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取交易記錄
def read_transactions(transaction_type=None, start_date=None, end_date=None):
    """
    從雲端或本地讀取交易記錄

    參數:
        transaction_type (str, optional): 交易類型
        start_date (str, optional): 開始日期
        end_date (str, optional): 結束日期

    返回:
        pandas.DataFrame: 交易記錄數據
    """
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    remote_path = f"data/transactions.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 從雲端讀取
            df = excel_manager.read_excel_with_fallback(remote_path, transactions_path)
            if df is not None:
                # 根據交易類型過濾
                if transaction_type:
                    df = df[df['交易類型'] == transaction_type]
                
                # 根據日期範圍過濾
                if start_date and end_date:
                    df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
                elif start_date:
                    df = df[df['日期'] >= start_date]
                elif end_date:
                    df = df[df['日期'] <= end_date]
                
                return df
            logger.warning("從雲端讀取交易記錄失敗，嘗試使用本地文件")
        
        # 本地模式或雲端讀取失敗，使用本地文件
        from models.data_manager import ensure_transactions_data
        ensure_transactions_data()  # 確保本地文件存在
        df = pd.read_excel(transactions_path)
        
        # 根據交易類型過濾
        if transaction_type:
            df = df[df['交易類型'] == transaction_type]
        
        # 根據日期範圍過濾
        if start_date and end_date:
            df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
        elif start_date:
            df = df[df['日期'] >= start_date]
        elif end_date:
            df = df[df['日期'] <= end_date]
        
        return df
    except Exception as e:
        logger.error(f"讀取交易記錄時出錯: {str(e)}")
        return pd.DataFrame()

# 保存主數據
def save_master_data(df, sheet_name):
    """
    保存主數據到雲端或本地

    參數:
        df (pandas.DataFrame): 要保存的數據
        sheet_name (str): 工作表名稱

    返回:
        bool: 是否保存成功
    """
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    remote_path = f"data/master_data.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 寫入雲端
            success = excel_manager.update_excel_sheet(df, remote_path, sheet_name)
            if success:
                # 同步到本地
                excel_manager._sync_cloud_to_local(remote_path, master_data_path)
                logger.info(f"已更新主數據 {sheet_name} 到雲端和本地")
                return True
            logger.warning(f"寫入主數據 {sheet_name} 到雲端失敗，嘗試使用本地文件")
        
        # 本地模式或雲端寫入失敗，使用本地文件
        from models.data_manager import ensure_master_data
        ensure_master_data()  # 確保本地文件存在
        
        # 讀取所有工作表數據
        with pd.ExcelFile(master_data_path) as xls:
            sheet_names = xls.sheet_names
            sheet_data = {name: pd.read_excel(master_data_path, sheet_name=name) for name in sheet_names}
        
        # 更新特定工作表數據
        sheet_data[sheet_name] = df
        
        # 保存所有工作表
        with pd.ExcelWriter(master_data_path) as writer:
            for name, data in sheet_data.items():
                data.to_excel(writer, sheet_name=name, index=False)
        
        logger.info(f"已更新主數據 {sheet_name} 到本地")
        return True
    except Exception as e:
        logger.error(f"保存主數據 {sheet_name} 時出錯: {str(e)}")
        return False

# 保存庫存數據
def save_inventory(df):
    """
    保存庫存數據到雲端或本地

    參數:
        df (pandas.DataFrame): 要保存的庫存數據

    返回:
        bool: 是否保存成功
    """
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    remote_path = f"data/inventory.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 寫入雲端
            success = excel_manager.write_excel(df, remote_path)
            if success:
                # 同步到本地
                excel_manager._sync_cloud_to_local(remote_path, inventory_path)
                logger.info("已更新庫存數據到雲端和本地")
                return True
            logger.warning("寫入庫存數據到雲端失敗，嘗試使用本地文件")
        
        # 本地模式或雲端寫入失敗，使用本地文件
        df.to_excel(inventory_path, index=False)
        logger.info("已更新庫存數據到本地")
        return True
    except Exception as e:
        logger.error(f"保存庫存數據時出錯: {str(e)}")
        return False

# 添加交易記錄
def add_transaction(transaction_data):
    """
    添加交易記錄到雲端或本地

    參數:
        transaction_data (dict): 交易記錄數據

    返回:
        int: 交易ID，如果失敗則為None
    """
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    remote_path = f"data/transactions.xlsx"
    
    try:
        # 檢查是否啟用雲端模式
        if cloud_config.is_cloud_mode():
            # 從雲端讀取現有數據
            df = excel_manager.read_excel_with_fallback(remote_path, transactions_path)
        else:
            # 從本地讀取現有數據
            from models.data_manager import ensure_transactions_data
            ensure_transactions_data()  # 確保本地文件存在
            df = pd.read_excel(transactions_path)
        
        # 生成交易ID
        if df.empty:
            transaction_id = 1
        else:
            transaction_id = df['交易ID'].max() + 1
        
        # 添加交易ID到數據中
        transaction_data['交易ID'] = transaction_id
        
        # 添加新的交易記錄
        new_transaction = pd.DataFrame([transaction_data])
        df = pd.concat([df, new_transaction], ignore_index=True)
        
        # 保存更新後的交易記錄
        if cloud_config.is_cloud_mode():
            # 寫入雲端
            success = excel_manager.write_excel(df, remote_path)
            if success:
                # 同步到本地
                excel_manager._sync_cloud_to_local(remote_path, transactions_path)
                logger.info(f"已添加交易記錄到雲端和本地，ID: {transaction_id}")
                return transaction_id
            logger.warning("寫入交易記錄到雲端失敗，嘗試使用本地文件")
        
        # 本地模式或雲端寫入失敗，使用本地文件
        df.to_excel(transactions_path, index=False)
        logger.info(f"已添加交易記錄到本地，ID: {transaction_id}")
        return transaction_id
    except Exception as e:
        logger.error(f"添加交易記錄時出錯: {str(e)}")
        return None

# 獲取員工和廠商列表
def get_staff_and_farmers():
    """
    獲取員工和廠商列表

    返回:
        tuple: (員工列表, 廠商列表)
    """
    staff_farmers_df = read_master_data('員工廠商')
    
    staff = staff_farmers_df[staff_farmers_df['類型'] == 'staff']['名稱'].tolist()
    farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']['名稱'].tolist()
    
    return staff, farmers

# 切換雲端模式
def toggle_cloud_mode(enabled=None):
    """
    切換雲端模式

    參數:
        enabled (bool, optional): 是否啟用雲端模式，如果為None則切換當前狀態

    返回:
        bool: 切換後的狀態
    """
    return cloud_config.toggle_cloud_mode(enabled)

# 檢查是否處於雲端模式
def is_cloud_mode():
    """
    檢查是否處於雲端模式

    返回:
        bool: 是否啟用雲端模式
    """
    return cloud_config.is_cloud_mode()

# 檢查雲端連接狀態
def check_cloud_connection():
    """
    檢查雲端連接狀態

    返回:
        bool: 連接是否正常
    """
    return sync_manager.update_connection_status()
