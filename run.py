from app import create_app
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from utils.common import logger
import os
import json

# 從config.json讀取配置
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("config.json文件不存在")
        return {}
    except json.JSONDecodeError:
        logger.error("config.json格式錯誤")
        return {}

logger.info("嘗試載入config.json配置檔案")
config_data = load_config()

# 檢查必要的配置項
if not config_data:
    print("錯誤: 未找到config.json檔案或檔案為空")
    print("請確保config.json檔案存在且包含必要的配置項")
    exit(1)

google_config = config_data.get('google_oauth', {})
required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
missing_vars = [var for var in required_vars if not google_config.get(var)]

if missing_vars:
    print(f"錯誤: 缺少以下配置項: {', '.join(missing_vars)}")
    print("請檢查您的config.json檔案是否包含這些項目")
    exit(1)
else:
    logger.info("已成功載入配置")

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
