"""
SQLite資料庫遷移模組
處理從Excel到SQLite的資料遷移
"""
import os
import pandas as pd
from utils.common import logger, DATA_PATH
from database.core.init import get_connection

def import_from_excel():
    """從現有的Excel檔案匯入資料到SQLite資料庫"""
    
    # 要匯入的Excel檔案路徑
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    inventory_path = os.path.join(DATA_PATH, 'inventory.xlsx')
    transactions_path = os.path.join(DATA_PATH, 'transactions.xlsx')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 先清空資料表
        cursor.execute("DELETE FROM system_config")
        cursor.execute("DELETE FROM staff_farmers")
        cursor.execute("DELETE FROM inventory")
        cursor.execute("DELETE FROM transactions")
        
        # 匯入系統配置
        if os.path.exists(master_data_path):
            config_df = pd.read_excel(master_data_path, sheet_name='系統配置')
            for _, row in config_df.iterrows():
                cursor.execute(
                    "INSERT INTO system_config (key, value) VALUES (?, ?)",
                    (row['鍵'], row['值'])
                )
            
            # 匯入員工與廠商
            staff_farmers_df = pd.read_excel(master_data_path, sheet_name='員工廠商')
            for _, row in staff_farmers_df.iterrows():
                cursor.execute(
                    "INSERT INTO staff_farmers (type, name, commission_rate) VALUES (?, ?, ?)",
                    (row['類型'], row['名稱'], row['分潤比例'])
                )
            
            logger.info("已從Excel匯入主資料")
        
        # 匯入庫存
        if os.path.exists(inventory_path):
            inventory_df = pd.read_excel(inventory_path)
            for _, row in inventory_df.iterrows():
                cursor.execute(
                    "INSERT INTO inventory (product_id, product_name, unit, quantity, unit_price, supplier) VALUES (?, ?, ?, ?, ?, ?)",
                    (int(row['產品編號']), row['產品名稱'], row['單位'], float(row['數量']), float(row['單價']), row['供應商'])
                )
            
            logger.info("已從Excel匯入庫存資料")
        
        # 匯入交易記錄
        if os.path.exists(transactions_path):
            transactions_df = pd.read_excel(transactions_path)
            for _, row in transactions_df.iterrows():
                # 處理可能為空的欄位
                shift = row['班別'] if '班別' in row and not pd.isna(row['班別']) else ''
                return_reason = row['退貨原因'] if '退貨原因' in row and not pd.isna(row['退貨原因']) else ''
                
                cursor.execute(
                    """INSERT INTO transactions (transaction_id, transaction_type, date, time, staff, shift, 
                    product_id, product_name, unit, quantity, unit_price, total_price, supplier, return_reason) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        int(row['交易ID']), row['交易類型'], str(row['日期']), row['時間'], row['員工'], shift,
                        int(row['產品編號']), row['產品名稱'], row['單位'], float(row['數量']), float(row['單價']), 
                        float(row['總價']), row['供應商'], return_reason
                    )
                )
            
            logger.info("已從Excel匯入交易記錄")
        
        conn.commit()
        logger.info("Excel資料成功匯入SQLite資料庫")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"從Excel匯入資料時發生錯誤: {str(e)}")
        return False
    finally:
        conn.close()
