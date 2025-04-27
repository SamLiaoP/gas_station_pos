import os
import pandas as pd
from utils.common import DATA_PATH, logger
from database import db_manager

# 確保主數據存在
def ensure_master_data():
    """確保主數據（系統配置、員工廠商）存在"""
    # 檢查系統配置表中是否有資料
    result = db_manager.execute_query("SELECT COUNT(*) FROM system_config")
    if result and result[0][0] > 0:
        return True
    
    # 如果沒有資料，載入預設資料
    db_manager.load_default_data()
    return True

# 確保庫存資料存在
def ensure_inventory_data():
    """確保庫存資料存在"""
    # 檢查庫存表中是否有資料
    result = db_manager.execute_query("SELECT COUNT(*) FROM inventory")
    if result and result[0][0] > 0:
        return True
    
    # 如果沒有資料，載入預設資料
    db_manager.load_default_data()
    return True

# 確保交易記錄資料表存在
def ensure_transactions_data():
    """確保交易記錄資料表存在"""
    # 檢查交易記錄表是否存在
    result = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if result:
        return True
    
    # 如果表不存在，重新初始化資料庫
    db_manager.init_db()
    return True

# 讀取主數據中的指定資料
def read_master_data(sheet_name):
    """讀取主數據（系統配置或員工廠商）"""
    ensure_master_data()  # 確保資料存在
    
    try:
        if sheet_name == '系統配置':
            # 讀取系統配置
            df = db_manager.query_to_dataframe("SELECT key AS 鍵, value AS 值 FROM system_config")
        elif sheet_name == '員工廠商':
            # 讀取員工廠商
            df = db_manager.query_to_dataframe("SELECT type AS 類型, name AS 名稱, commission_rate AS 分潤比例 FROM staff_farmers")
        else:
            logger.error(f"無效的主數據表名: {sheet_name}")
            return pd.DataFrame()
        
        return df
    except Exception as e:
        logger.error(f"讀取主數據 {sheet_name} 時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取庫存資料
def read_inventory():
    """讀取庫存資料"""
    ensure_inventory_data()  # 確保資料存在
    
    try:
        df = db_manager.query_to_dataframe("""
            SELECT product_id AS 產品編號, product_name AS 產品名稱, unit AS 單位, 
                   quantity AS 數量, unit_price AS 單價, supplier AS 供應商
            FROM inventory
        """)
        return df
    except Exception as e:
        logger.error(f"讀取庫存資料時出錯: {str(e)}")
        return pd.DataFrame()

# 讀取交易記錄
def read_transactions(transaction_type=None, start_date=None, end_date=None):
    """讀取交易記錄，可根據交易類型和日期範圍進行篩選"""
    ensure_transactions_data()  # 確保資料存在
    
    try:
        query = """
            SELECT transaction_id AS 交易ID, transaction_type AS 交易類型, date AS 日期, time AS 時間,
                   staff AS 員工, shift AS 班別, product_id AS 產品編號, product_name AS 產品名稱,
                   unit AS 單位, quantity AS 數量, unit_price AS 單價, total_price AS 總價,
                   supplier AS 供應商, return_reason AS 退貨原因
            FROM transactions
            WHERE 1=1
        """
        params = []
        
        # 根據交易類型過濾
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type)
        
        # 根據日期範圍過濾
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        df = db_manager.query_to_dataframe(query, tuple(params))
        return df
    except Exception as e:
        logger.error(f"讀取交易記錄時出錯: {str(e)}")
        return pd.DataFrame()

# 保存主數據
def save_master_data(df, sheet_name):
    """保存主數據（系統配置或員工廠商）"""
    ensure_master_data()  # 確保資料存在
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        if sheet_name == '系統配置':
            # 清空現有資料
            cursor.execute("DELETE FROM system_config")
            
            # 插入新資料
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO system_config (key, value) VALUES (?, ?)",
                    (row['鍵'], row['值'])
                )
            
        elif sheet_name == '員工廠商':
            # 清空現有資料
            cursor.execute("DELETE FROM staff_farmers")
            
            # 插入新資料
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO staff_farmers (type, name, commission_rate) VALUES (?, ?, ?)",
                    (row['類型'], row['名稱'], row['分潤比例'])
                )
        else:
            logger.error(f"無效的主數據表名: {sheet_name}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        logger.info(f"已更新主數據 {sheet_name}")
        return True
    except Exception as e:
        logger.error(f"保存主數據 {sheet_name} 時出錯: {str(e)}")
        return False

# 保存庫存資料
def save_inventory(df):
    """保存庫存資料"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 清空現有資料
        cursor.execute("DELETE FROM inventory")
        
        # 插入新資料
        for _, row in df.iterrows():
            cursor.execute(
                """INSERT INTO inventory (product_id, product_name, unit, quantity, unit_price, supplier) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    int(row['產品編號']), row['產品名稱'], row['單位'], 
                    float(row['數量']), float(row['單價']), row['供應商']
                )
            )
        
        conn.commit()
        conn.close()
        
        logger.info("已更新庫存資料")
        return True
    except Exception as e:
        logger.error(f"保存庫存資料時出錯: {str(e)}")
        return False

# 添加交易記錄
def add_transaction(transaction_data):
    """添加新的交易記錄"""
    ensure_transactions_data()  # 確保交易記錄表存在
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 獲取最大交易ID
        cursor.execute("SELECT MAX(transaction_id) FROM transactions")
        result = cursor.fetchone()
        max_id = result[0] if result[0] is not None else 0
        transaction_id = max_id + 1
        
        # 添加交易ID
        transaction_data['交易ID'] = transaction_id
        
        # 從交易資料中取出欄位數據
        shift = transaction_data.get('班別', '')
        return_reason = transaction_data.get('退貨原因', '')
        
        # 執行插入操作
        cursor.execute(
            """INSERT INTO transactions (transaction_id, transaction_type, date, time, staff, shift, 
               product_id, product_name, unit, quantity, unit_price, total_price, supplier, return_reason) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                transaction_id, transaction_data['交易類型'], 
                str(transaction_data['日期']), transaction_data['時間'], 
                transaction_data['員工'], shift,
                transaction_data['產品編號'], transaction_data['產品名稱'], 
                transaction_data['單位'], float(transaction_data['數量']), 
                float(transaction_data['單價']), float(transaction_data['總價']), 
                transaction_data['供應商'], return_reason
            )
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"已添加交易記錄，ID: {transaction_id}")
        return transaction_id
    except Exception as e:
        logger.error(f"添加交易記錄時出錯: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# 獲取員工和廠商列表
def get_staff_and_farmers():
    """獲取員工和廠商列表"""
    staff_farmers_df = read_master_data('員工廠商')
    
    staff = staff_farmers_df[staff_farmers_df['類型'] == 'staff']['名稱'].tolist()
    farmers = staff_farmers_df[staff_farmers_df['類型'] == 'farmer']['名稱'].tolist()
    
    return staff, farmers
