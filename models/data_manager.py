import os
import pandas as pd
import shutil
import traceback
from utils.common import DATA_PATH, ARCHIVES_PATH, logger

# 確保當前數據存在並可用
def ensure_data_file_exists(file_name, columns=None):
    file_path = os.path.join(DATA_PATH, file_name)
    
    # 確保目錄存在
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH, exist_ok=True)
    
    # 如果文件存在，直接返回
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    
    # 如果文件不存在，先嘗試從最近的封存中複製
    try:
        # 尋找最近的封存
        archive_dates = sorted([d for d in os.listdir(ARCHIVES_PATH) if os.path.isdir(os.path.join(ARCHIVES_PATH, d))], reverse=True)
        
        if archive_dates:
            latest_date = archive_dates[0]
            latest_file = os.path.join(ARCHIVES_PATH, latest_date, file_name)
            
            if os.path.exists(latest_file):
                # 複製到當前目錄
                shutil.copy2(latest_file, file_path)
                logger.info(f"已從封存({latest_date})中複製 {file_name} 到今日資料夾")
                return pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"從封存複製 {file_name} 時出錯: {str(e)}")
    
    # 如果沒有封存可用，創建新的空白 DataFrame
    if columns is None:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(columns=columns)
    
    # 保存空白檔案
    df.to_excel(file_path, index=False)
    logger.info(f"已創建新的空白 {file_name} 檔案")
    
    return df

# 讀取員工和廠商列表
def get_staff_and_farmers():
    # 先檢查今日數據文件
    file_path = os.path.join(DATA_PATH, 'staff_farmers.xlsx')
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        staff = df[df['類型'] == 'staff']['名稱'].tolist()
        farmers = df[df['類型'] == 'farmer']['名稱'].tolist()
        return staff, farmers
    
    # 如果今日文件不存在，嘗試從最近的封存中複製
    try:
        # 初始化空數據框並確保數據路徑存在
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH, exist_ok=True)
        
        # 尋找最新的封存文件
        archive_dates = sorted([d for d in os.listdir(ARCHIVES_PATH) if os.path.isdir(os.path.join(ARCHIVES_PATH, d))], reverse=True)
        
        if archive_dates:
            latest_date = archive_dates[0]
            latest_file = os.path.join(ARCHIVES_PATH, latest_date, 'staff_farmers.xlsx')
            
            if os.path.exists(latest_file):
                # 複製到今日數據文件夾
                shutil.copy2(latest_file, file_path)
                logger.info(f"已從封存({latest_date})中複製 staff_farmers.xlsx 到今日資料夾")
                
                # 重新嘗試讀取
                df = pd.read_excel(file_path)
                staff = df[df['類型'] == 'staff']['名稱'].tolist()
                farmers = df[df['類型'] == 'farmer']['名稱'].tolist()
                return staff, farmers
    except Exception as e:
        logger.error(f"嘗試從封存複製 staff_farmers.xlsx 時出錯: {str(e)}")
    
    # 如果所有嘗試都失敗，返回空列表
    return [], []

# 讀取庫存
def get_inventory():
    file_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    
    # 如果今日文件不存在，嘗試從最近的封存中複製
    try:
        # 確保數據路徑存在
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH, exist_ok=True)
        
        # 尋找最新的封存文件
        archive_dates = sorted([d for d in os.listdir(ARCHIVES_PATH) if os.path.isdir(os.path.join(ARCHIVES_PATH, d))], reverse=True)
        
        if archive_dates:
            latest_date = archive_dates[0]
            latest_file = os.path.join(ARCHIVES_PATH, latest_date, 'inventory.xlsx')
            
            if os.path.exists(latest_file):
                # 複製到今日數據文件夾
                shutil.copy2(latest_file, file_path)
                logger.info(f"已從封存({latest_date})中複製 inventory.xlsx 到今日資料夾")
                
                # 重新嘗試讀取
                return pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"嘗試從封存複製 inventory.xlsx 時出錯: {str(e)}")
    
    # 如果所有嘗試都失敗，返回空 DataFrame
    return pd.DataFrame()
