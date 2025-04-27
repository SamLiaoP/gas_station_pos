from flask import Flask
from utils.common import ensure_directories, logger
from routes.main_routes import main_routes
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from database import db_manager
import os
import secrets

# 創建並配置應用
def create_app():
    app = Flask(__name__)
    
    # 設定 secret_key 用於 session
    app.secret_key = secrets.token_hex(16)
    
    # 確保所有必要目錄存在
    ensure_directories()
    
    # 初始化SQLite資料庫
    logger.info("初始化SQLite資料庫...")
    db_manager.init_db()
    
    # 確保主數據存在
    ensure_master_data()
    
    # 確保庫存資料存在
    ensure_inventory_data()
    
    # 確保交易記錄資料表存在
    ensure_transactions_data()
    
    # 從舊Excel檔案匯入資料(如果需要)
    import_data_if_needed()
    
    # 註冊路由藍圖
    app.register_blueprint(main_routes)
    
    # 記錄系統狀態
    logger.info(f"應用初始化完成，運行於本地模式")
    return app

# 從舊Excel檔案匯入資料(如果需要)
def import_data_if_needed():
    logger.info("初始化數據...")
    
    # 從Excel匯入資料
    # db_manager.import_from_excel()
    
    logger.info("數據初始化完成")

# 應用入口點
if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=8081, debug=True)
