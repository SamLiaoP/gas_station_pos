"""
SQLite資料庫初始化模組
處理資料庫結構和預設資料的建立
"""
import os
import sqlite3
import pandas as pd
from utils.common import logger, DATA_PATH

# 資料庫檔案路徑
DB_PATH = os.path.join(DATA_PATH, 'gas_station.db')

def get_connection():
    """建立並返回一個SQLite資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓查詢結果以字典形式返回
    return conn

def init_db():
    """初始化資料庫結構，建立必要的資料表"""
    logger.info("初始化資料庫...")
    
    # 建立連線
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 建立系統配置資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
        ''')
        
        # 建立員工與廠商資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            commission_rate REAL NOT NULL,
            UNIQUE (type, name)
        )
        ''')
        
        # 建立庫存資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            supplier TEXT NOT NULL,
            UNIQUE (product_name, unit, supplier)
        )
        ''')
        
        # 建立交易記錄資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            staff TEXT NOT NULL,
            shift TEXT,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            supplier TEXT NOT NULL,
            return_reason TEXT,
            FOREIGN KEY (product_id) REFERENCES inventory (product_id)
        )
        ''')
        
        conn.commit()
        logger.info("資料庫結構初始化完成")
        
        # 載入預設資料
        load_default_data()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"初始化資料庫時發生錯誤: {str(e)}")
    finally:
        conn.close()

def load_default_data():
    """如果資料表是空的，載入預設資料"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 檢查系統配置是否為空
        cursor.execute("SELECT COUNT(*) FROM system_config")
        if cursor.fetchone()[0] == 0:
            # 載入預設配置
            config_data = [
                ('morning_shift_start', '06:00'),
                ('morning_shift_end', '14:00'),
                ('afternoon_shift_start', '14:00'),
                ('afternoon_shift_end', '22:00'),
                ('night_shift_start', '22:00'),
                ('night_shift_end', '06:00')
            ]
            cursor.executemany(
                "INSERT INTO system_config (key, value) VALUES (?, ?)",
                config_data
            )
            logger.info("已載入預設系統配置")
        
        # 檢查員工與廠商是否為空
        cursor.execute("SELECT COUNT(*) FROM staff_farmers")
        if cursor.fetchone()[0] == 0:
            # 載入預設員工與廠商
            staff_farmers_data = [
                ('staff', '王小明', 0.05),
                ('staff', '李小華', 0.05),
                ('staff', '張大力', 0.05),
                ('farmer', '有機農場', 0.15),
                ('farmer', '綠色蔬果', 0.12),
                ('farmer', '友善耕作', 0.10)
            ]
            cursor.executemany(
                "INSERT INTO staff_farmers (type, name, commission_rate) VALUES (?, ?, ?)",
                staff_farmers_data
            )
            logger.info("已載入預設員工與廠商資料")
        
        # 檢查庫存是否為空
        cursor.execute("SELECT COUNT(*) FROM inventory")
        if cursor.fetchone()[0] == 0:
            # 載入預設庫存
            inventory_data = [
                ('有機小白菜', '把', 20, 35, '有機農場'),
                ('有機青菜', '把', 15, 30, '有機農場'),
                ('有機紅蘿蔔', '公斤', 30, 60, '綠色蔬果'),
                ('有機紅蘿蔔', '條', 40, 20, '綠色蔬果'),
                ('有機番茄', '公斤', 25, 70, '綠色蔬果'),
                ('有機番茄', '顆', 50, 15, '綠色蔬果'),
                ('有機馬鈴薯', '公斤', 40, 45, '友善耕作'),
                ('新鮮蘋果', '顆', 50, 20, '有機農場'),
                ('新鮮蘋果', '箱', 5, 400, '有機農場'),
                ('新鮮蘋果', '公斤', 10, 80, '有機農場')
            ]
            cursor.executemany(
                "INSERT INTO inventory (product_name, unit, quantity, unit_price, supplier) VALUES (?, ?, ?, ?, ?)",
                inventory_data
            )
            logger.info("已載入預設庫存資料")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"載入預設資料時發生錯誤: {str(e)}")
    finally:
        conn.close()
