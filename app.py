from flask import Flask
from utils.common import ensure_directories, logger
from routes.main_routes import main_routes
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from database import db_manager
import os

# 創建並配置應用
def create_app():
    app = Flask(__name__)
    
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

# 從Excel檔案匯入資料(如果需要)
def import_data_if_needed():
    # 檢查資料庫是否已有資料
    result = db_manager.execute_query("SELECT COUNT(*) FROM transactions")
    
    # 如果資料庫是空的，且Excel檔案存在，才進行匯入
    if result and result[0][0] == 0:
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'transactions.xlsx')
        if os.path.exists(excel_path):
            logger.info("檢測到舊的Excel資料，開始匯入到SQLite...")
            db_manager.import_from_excel()
        else:
            logger.info("沒有找到舊的Excel資料，跳過匯入步驟")

app = create_app()

# 啟動應用
if __name__ == '__main__':
    print("啟動加油站POS系統 v2，請訪問 http://127.0.0.1:8080/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8080)
