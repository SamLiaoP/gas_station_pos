from flask import Flask
from utils.common import ensure_directories, archive_yesterday_data, logger
from routes.main_routes import main_routes

# 創建並配置應用
def create_app():
    app = Flask(__name__)
    
    # 確保所有必要目錄存在
    ensure_directories()
    
    # 嘗試封存昨日數據
    archive_yesterday_data()
    
    # 註冊路由藍圖
    app.register_blueprint(main_routes)
    
    logger.info("應用初始化完成")
    return app

app = create_app()

# 啟動應用
if __name__ == '__main__':
    print("啟動加油站小農POS系統，請訪問 http://127.0.0.1:8080/")
    # 如果需要在區域網內裡訪問，請將host設為'0.0.0.0'
    # 如果只在本機訪問，請使用'127.0.0.1'
    app.run(debug=True, host='0.0.0.0', port=8080)
