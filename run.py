from app import create_app
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from utils.common import logger
import os
from dotenv import load_dotenv

# 載入.env檔案中的環境變數
load_dotenv()
logger.info("嘗試載入.env檔案中的環境變數")

# 檢查環境變數
required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"錯誤: 缺少以下環境變數: {', '.join(missing_vars)}")
    print("請檢查您的.env檔案是否包含這些變數，或者通過以下方式設定:")
    print("1. 確認.env檔案位於項目根目錄")
    print("2. 或使用以下命令設定環境變數:")
    print("   export GOOGLE_CLIENT_ID='your-client-id'")
    print("   export GOOGLE_CLIENT_SECRET='your-client-secret'")
    exit(1)
else:
    logger.info("已成功載入環境變數")

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
    
    logger.info("啟動加油站POS系統 v2，請訪問 http://127.0.0.1:8080/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8080)
