import os
import pandas as pd
import traceback
from utils.common import DATA_PATH, ARCHIVES_PATH, REPORTS_PATH, logger

# 查詢指定月份或日期範圍的所有數據
def get_monthly_data(file_name, year=None, month=None, start_date=None, end_date=None):
    try:
        result_df = pd.DataFrame()
        
        # 決定篩選條件
        if start_date and end_date:
            # 使用日期範圍篩選
            date_range = (start_date, end_date)
            date_filter = lambda df: (df['日期'] >= pd.to_datetime(start_date)) & (df['日期'] <= pd.to_datetime(end_date))
        else:
            # 使用年月篩選
            month_str = f"{year}-{month:02d}"
            date_filter = lambda df: df['日期'].dt.strftime('%Y-%m') == month_str
        
        # 檢查當前數據目錄中是否有數據
        current_file = os.path.join(DATA_PATH, file_name)
        if os.path.exists(current_file):
            try:
                df = pd.read_excel(current_file)
                if not df.empty:
                    # 轉換日期欄位
                    df['日期'] = pd.to_datetime(df['日期'])
                    # 篩選指定範圍的數據
                    filtered_df = df[date_filter(df)]
                    # 合併到結果中
                    result_df = pd.concat([result_df, filtered_df])
            except Exception as e:
                logger.error(f"讀取當前檔案 {file_name} 時出錯: {str(e)}")
        
        # 掃瞄所有封存目錄
        for date_dir in os.listdir(ARCHIVES_PATH):
            archive_dir = os.path.join(ARCHIVES_PATH, date_dir)
            if os.path.isdir(archive_dir):
                archived_file = os.path.join(archive_dir, file_name)
                if os.path.exists(archived_file):
                    try:
                        df = pd.read_excel(archived_file)
                        if not df.empty:
                            # 轉換日期欄位
                            df['日期'] = pd.to_datetime(df['日期'])
                            # 篩選指定範圍的數據
                            filtered_df = df[date_filter(df)]
                            # 合併到結果中
                            result_df = pd.concat([result_df, filtered_df])
                    except Exception as e:
                        logger.error(f"讀取封存檔案 {archived_file} 時出錯: {str(e)}")
        
        # 重置索引
        if not result_df.empty:
            result_df = result_df.reset_index(drop=True)
            
            # 記錄日誌
            if start_date and end_date:
                logger.info(f"已成功讀取 {start_date} 至 {end_date} 的 {file_name} 數據，共 {len(result_df)} 筆記錄")
            else:
                logger.info(f"已成功讀取 {year}年{month}月 的 {file_name} 數據，共 {len(result_df)} 筆記錄")
        else:
            if start_date and end_date:
                logger.warning(f"找不到 {start_date} 至 {end_date} 的 {file_name} 數據")
            else:
                logger.warning(f"找不到 {year}年{month}月 的 {file_name} 數據")
            
        return result_df
    
    except Exception as e:
        logger.error(f"取得數據時出錯: {str(e)}")
        logger.error(traceback.format_exc())
        return pd.DataFrame()
