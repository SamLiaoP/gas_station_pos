from app import create_app
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from utils.common import logger

# 創建應用實例
app = create_app()

if __name__ == '__main__':
    logger.info("初始化數據...")
    
    # 確保主數據文件存在
    ensure_master_data()
    
    # 確保庫存文件存在
    ensure_inventory_data()
    
    # 確保交易記錄文件存在
    ensure_transactions_data()
    
    logger.info("數據初始化完成")
    
    logger.info("啟動加油站POS系統 v2，請訪問 http://127.0.0.1:8081/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8081)
