import os
import secrets
from dotenv import load_dotenv

# 確保環境變數已載入
load_dotenv()

# 應用程式配置
class Config:
    # 安全設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Google OAuth 設定
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    
    # 授權用戶清單 - 只有這些郵箱地址可以登入系統
    AUTHORIZED_EMAILS = [
        # 在此處添加允許登入的Google郵箱地址
        'ba88052@gmail.com',
    ]
    
    # 從環境變數中讀取授權用戶
    if os.environ.get('AUTHORIZED_EMAILS'):
        env_emails = os.environ.get('AUTHORIZED_EMAILS').split(',')
        for email in env_emails:
            if email.strip() and email.strip() not in AUTHORIZED_EMAILS:
                AUTHORIZED_EMAILS.append(email.strip())
    
    # 如果處於測試模式，添加測試用戶到授權清單
    if os.environ.get('TESTING') == 'True':
        AUTHORIZED_EMAILS.append('test@example.com')
    
    # 資料庫路徑
    DB_PATH = os.environ.get('DB_PATH') or os.path.join('data', 'gas_station.db') 