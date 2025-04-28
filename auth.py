from flask import Blueprint, redirect, url_for, session, request, render_template, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests
import json
from functools import wraps
from utils.common import logger
from config import Config
import os

# 建立認證藍圖
auth = Blueprint('auth', __name__)

# 用戶類別
class User(UserMixin):
    def __init__(self, id, name, email, profile_pic):
        self.id = id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

# 初始化 LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '請先登入系統'

# 用戶加載函數
@login_manager.user_loader
def load_user(user_id):
    if 'user_info' in session:
        user_info = session['user_info']
        return User(
            id=user_info['id'],
            name=user_info['name'],
            email=user_info['email'],
            profile_pic=user_info['profile_pic']
        )
    return None

# 獲取Google的配置信息
def get_google_provider_cfg():
    try:
        return requests.get(Config.GOOGLE_DISCOVERY_URL).json()
    except Exception as e:
        logger.error(f"無法獲取Google配置信息: {str(e)}")
        return None

# 只允許授權用戶訪問的裝飾器
def authorized_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 測試模式下跳過授權檢查
        if os.environ.get('TESTING') == 'True':
            return f(*args, **kwargs)
            
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # 檢查用戶郵箱是否在授權清單中
        if current_user.email not in Config.AUTHORIZED_EMAILS:
            logout_user()
            flash('您無權訪問系統。請使用授權的Google帳號登入。', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

# 登入路由
@auth.route('/login')
def login():
    # 測試模式下自動登入
    if os.environ.get('TESTING') == 'True':
        # 創建測試用戶
        user = User(
            id='test_user_id',
            name='測試用戶',
            email='test@example.com',
            profile_pic=None
        )
        login_user(user)
        session['user_info'] = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'profile_pic': user.profile_pic
        }
        logger.info(f"測試模式：自動登入用戶 {user.email}")
        return redirect(url_for('main_routes.index'))
        
    return render_template('login.html')

# Google登入
@auth.route('/login/google')
def google_login():
    from authlib.integrations.flask_client import OAuth
    
    # 創建OAuth物件
    oauth = OAuth(current_app)
    
    # 獲取Google配置
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash('無法連接到Google認證服務，請稍後再試', 'danger')
        return redirect(url_for('auth.login'))
    
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # 註冊Google客戶端
    oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url=Config.GOOGLE_DISCOVERY_URL,
        client_kwargs={
            "scope": "openid email profile"
        }
    )
    
    # 重定向到Google授權頁面
    redirect_uri = url_for('auth.google_callback', _external=True)
    logger.info(f"Google登入回調URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

# Google回調
@auth.route('/login/google/callback')
def google_callback():
    from authlib.integrations.flask_client import OAuth
    
    # 創建OAuth物件
    oauth = OAuth(current_app)
    
    # 註冊Google客戶端
    oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url=Config.GOOGLE_DISCOVERY_URL,
        client_kwargs={
            "scope": "openid email profile"
        }
    )
    
    # 獲取Google配置
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash('無法連接到Google認證服務，請稍後再試', 'danger')
        return redirect(url_for('auth.login'))
    
    # 獲取認證響應
    token = oauth.google.authorize_access_token()
    
    # 獲取用戶信息
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    
    # 發送請求到Google API
    resp = requests.get(userinfo_endpoint, headers={'Authorization': f'Bearer {token["access_token"]}'})
    userinfo = resp.json()
    
    # 檢查用戶郵箱是否在授權清單中
    if userinfo.get("email") not in Config.AUTHORIZED_EMAILS:
        flash('您無權訪問系統。請使用授權的Google帳號登入。', 'danger')
        return redirect(url_for('auth.login'))
    
    # 創建用戶實例
    user = User(
        id=userinfo["sub"],
        name=userinfo["name"],
        email=userinfo["email"],
        profile_pic=userinfo.get("picture", None)
    )
    
    # 登入用戶
    login_user(user)
    
    # 保存用戶信息
    session['user_info'] = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'profile_pic': user.profile_pic
    }
    
    logger.info(f"用戶 {user.email} 登入成功")
    
    # 重定向到主頁
    return redirect(url_for('main_routes.index'))

# 登出路由
@auth.route('/logout')
@login_required
def logout():
    logger.info(f"用戶 {current_user.email} 登出")
    logout_user()
    session.pop('user_info', None)
    flash('您已成功登出系統', 'success')
    return redirect(url_for('auth.login')) 