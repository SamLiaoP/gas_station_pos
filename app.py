from flask import Flask, redirect, url_for
from utils.common import ensure_directories, logger
from routes.main_routes import main_routes
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data
from database import db_manager
from auth import auth, login_manager, authorized_required
from config import Config
import os

# 創建並配置應用
def create_app():
    app = Flask(__name__)
    
    # 從配置類載入設定
    app.config.from_object(Config)
    
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
    
    # 初始化登入管理器
    login_manager.init_app(app)
    
    # 註冊路由藍圖
    app.register_blueprint(auth)
    app.register_blueprint(main_routes)
    
    # 保護所有主要路由需要登入
    @app.before_request
    def require_login():
        from flask import request, redirect, url_for
        from flask_login import current_user
        
        # 允許訪問的路徑前綴和路由
        allowed_paths = [
            '/login', 
            '/static/', 
            '/auth/'
        ]
        
        # 如果路徑是允許匿名訪問的，或用戶已經登入，則允許訪問
        if any(request.path.startswith(path) for path in allowed_paths) or current_user.is_authenticated:
            return None
            
        # 否則重定向到登入頁面
        return redirect(url_for('auth.login'))
    
    # 將根路徑重定向到登入頁面
    @app.route('/')
    def index():
        return redirect(url_for('main_routes.index'))
    
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
    app.run(host='127.0.0.1', port=8080, debug=True)
