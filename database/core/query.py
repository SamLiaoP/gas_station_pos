"""
SQLite資料庫查詢模組
處理資料庫查詢和DataFrame轉換
"""
import pandas as pd
from utils.common import logger
from database.core.init import get_connection

def query_to_dataframe(query, params=()):
    """執行SQL查詢並將結果轉換為DataFrame"""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        logger.error(f"執行查詢時發生錯誤: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_query(query, params=()):
    """執行SQL查詢並返回結果"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"執行查詢時發生錯誤: {str(e)}")
        return []
    finally:
        conn.close()

def execute_command(query, params=()):
    """執行SQL指令（INSERT, UPDATE, DELETE等）並返回影響的行數"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error(f"執行指令時發生錯誤: {str(e)}")
        return 0
    finally:
        conn.close()

def execute_many(query, param_list):
    """執行多筆SQL指令並返回影響的行數"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, param_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error(f"執行多筆指令時發生錯誤: {str(e)}")
        return 0
    finally:
        conn.close()
