from flask import Flask
from utils.common import ensure_directories, logger
from routes.main_routes import main_routes
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
import cloud_integration

# 創建並配置應用
def create_app():
    app = Flask(__name__)
    
    # 確保所有必要目錄存在
    ensure_directories()
    
    # 確保主數據文件存在
    ensure_master_data()
    
    # 確保庫存文件存在
    ensure_inventory_data()
    
    # 確保交易記錄文件存在
    ensure_transactions_data()
    
    # 註冊路由藍圖
    app.register_blueprint(main_routes)
    
    # 記錄雲端整合狀態
    cloud_mode = "雲端模式" if cloud_integration.is_cloud_mode() else "本地模式"
    logger.info(f"應用初始化完成，運行於{cloud_mode}")
    return app

app = create_app()

# 啟動應用
if __name__ == '__main__':
    print("啟動加油站POS系統 v2，請訪問 http://127.0.0.1:8080/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8080)
