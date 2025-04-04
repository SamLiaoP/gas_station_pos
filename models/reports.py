import os
import pandas as pd
import traceback
from utils.common import DATA_PATH, logger

# 獲取指定月份的數據
def get_monthly_data(file_name, year=None, month=None, start_date=None, end_date=None):
    """Read monthly data from the specified file.
    
    Args:
        file_name (str): The Excel file name to read from
        year (int, optional): Year of the data. Defaults to None.
        month (int, optional): Month of the data. Defaults to None.
        start_date (str, optional): Start date for custom range in format 'YYYY-MM-DD'. Defaults to None.
        end_date (str, optional): End date for custom range in format 'YYYY-MM-DD'. Defaults to None.
    
    Returns:
        pandas.DataFrame: Filtered data for the specified month or date range
    """
    try:
        # 檢查檔案是否存在
        file_path = os.path.join(DATA_PATH, file_name)
        if not os.path.exists(file_path):
            logger.warning(f"檔案不存在: {file_path}")
            return pd.DataFrame()
        
        # 讀取檔案
        df = pd.read_excel(file_path)
        
        # 檢查欄位
        if '日期' not in df.columns:
            logger.error(f"檔案 {file_name} 缺少日期欄位")
            return pd.DataFrame()
        
        # 根據欄位列表的時間範圍過濾數據
        if start_date and end_date:
            # 如果提供了起止日期，則範圍為: start_date <= 日期 <= end_date
            mask = (df['日期'] >= start_date) & (df['日期'] <= end_date)
            return df[mask]
        elif year and month:
            # 如果提供了年和月，則過濾或者建構出範圍給您
            # 特別處理日期格式
            if df['日期'].dtype == 'object':
                # 如果日期欄位是字符串，嘗試轉換為 datetime
                try:
                    df['日期'] = pd.to_datetime(df['日期'])
                except Exception as e:
                    logger.error(f"轉換日期時出錯: {str(e)}")
                    logger.error(traceback.format_exc())
                    return pd.DataFrame()
            
            # 過濾指定年月的數據
            month_start = f"{year}-{month:02d}-01"
            if month == 12:
                next_month_start = f"{year+1}-01-01"
            else:
                next_month_start = f"{year}-{month+1:02d}-01"
            
            mask = (df['日期'] >= month_start) & (df['日期'] < next_month_start)
            return df[mask]
        else:
            # 如果沒有提供任何過濾條件，返回所有數據
            return df
    except Exception as e:
        logger.error(f"讀取數據時出錯: {str(e)}")
        logger.error(traceback.format_exc())
        return pd.DataFrame()

# 獲取退貨記錄
def get_returns_data(year=None, month=None, start_date=None, end_date=None):
    """Get returns data for the specified period.
    
    Args:
        year (int, optional): Year of the data. Defaults to None.
        month (int, optional): Month of the data. Defaults to None.
        start_date (str, optional): Start date for custom range in format 'YYYY-MM-DD'. Defaults to None.
        end_date (str, optional): End date for custom range in format 'YYYY-MM-DD'. Defaults to None.
    
    Returns:
        pandas.DataFrame: Filtered returns data for the specified period
    """
    # 使用已有的 get_monthly_data 函數讀取退貨檔案
    return get_monthly_data('returns.xlsx', year, month, start_date, end_date)
