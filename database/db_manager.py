"""
SQLite資料庫管理模組
作為資料庫操作的統一入口點
"""
import os
from utils.common import DATA_PATH

# 資料庫檔案路徑
DB_PATH = os.path.join(DATA_PATH, 'gas_station.db')

# 從子模組導入所有功能
from database.core.init import init_db, load_default_data, get_connection
from database.core.migration import import_from_excel
from database.core.query import (
    query_to_dataframe, 
    execute_query, 
    execute_command, 
    execute_many
)

# 導出所有功能
__all__ = [
    'DB_PATH',
    'init_db',
    'load_default_data',
    'get_connection',
    'import_from_excel',
    'query_to_dataframe',
    'execute_query',
    'execute_command',
    'execute_many'
]
