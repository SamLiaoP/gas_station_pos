import os
import secrets
import json
import logging

# 從config.json讀取配置
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("config.json文件不存在")
        return {}
    except json.JSONDecodeError:
        logging.error("config.json格式錯誤")
        return {}

# 載入配置
config_data = load_config()

# 應用程式配置
class Config:
    # 安全設定
    SECRET_KEY = config_data.get('app', {}).get('SECRET_KEY') or secrets.token_hex(16)
    
    # Google OAuth 設定
    GOOGLE_CLIENT_ID = config_data.get('google_oauth', {}).get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = config_data.get('google_oauth', {}).get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_DISCOVERY_URL = config_data.get('google_oauth', {}).get('GOOGLE_DISCOVERY_URL', 'https://accounts.google.com/.well-known/openid-configuration')
    
    # 測試模式設定
    TESTING = config_data.get('testing', {}).get('TESTING', 'False')
    
    # 授權用戶清單 - 只有這些郵箱地址可以登入系統
    AUTHORIZED_EMAILS = [
        # 在此處添加允許登入的Google郵箱地址
        'ba88052@gmail.com',
    ]
    
    # 從配置檔案中讀取授權用戶
    config_emails = config_data.get('auth', {}).get('AUTHORIZED_EMAILS', [])
    for email in config_emails:
        if email and email not in AUTHORIZED_EMAILS:
            AUTHORIZED_EMAILS.append(email)
    
    # 如果處於測試模式，添加測試用戶到授權清單
    if TESTING == 'True':
        AUTHORIZED_EMAILS.append('test@example.com')
    
    # 資料庫路徑
    DB_PATH = config_data.get('database', {}).get('DB_PATH') or os.path.join('data', 'gas_station.db') 