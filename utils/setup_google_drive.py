import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import Config # <--- 註釋或刪除此行

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Google Drive API 的權限範圍
SCOPES = ['https://www.googleapis.com/auth/drive.file'] # 只請求建立和管理它自己建立的檔案權限

def setup_google_drive_token():
    # from config import Config # <--- 將導入移到這裡
    """
    執行 Google Drive OAuth 2.0 認證流程並儲存 token。
    """
    creds = None
    token_path = Config.GOOGLE_DRIVE_TOKEN_PATH
    credentials_path = Config.GOOGLE_DRIVE_CREDENTIALS_PATH

    # 檢查 token.pickle 是否存在
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            creds = pickle.load(token_file)
            logger.info("已從 token.pickle 載入現有憑證。")

    # 如果沒有有效的憑證，則執行認證流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("憑證已過期，正在嘗試刷新...")
            try:
                creds.refresh(Request())
                logger.info("憑證刷新成功。")
            except Exception as e:
                logger.warning(f"刷新憑證失敗: {e}。需要重新認證。")
                creds = None # 強制重新認證
        
        if not creds: # 需要全新認證或刷新失敗
            if not os.path.exists(credentials_path):
                logger.error(f"Google Drive API 憑證檔案 (credentials.json) 未找到於: {credentials_path}")
                logger.error("請從 Google Cloud Console 下載您的 OAuth 2.0 用戶端 ID JSON 檔案並將其儲存為 config/credentials.json")
                return False
            
            logger.info("正在啟動 Google OAuth 流程以取得新的 token...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # 注意: Zeabur 環境下 run_local_server 可能會有問題，需要思考替代方案或確保本機完成
            # 這裡假設在本機或可互動環境執行此腳本
            creds = flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='請在瀏覽器中授權此應用程式存取您的 Google Drive：')
            logger.info("OAuth 流程完成，已獲取新的憑證。")
        
        # 儲存憑證供下次使用
        try:
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'wb') as token_file:
                pickle.dump(creds, token_file)
            logger.info(f"憑證已儲存到 {token_path}")
        except Exception as e:
            logger.error(f"儲存 token.pickle 失敗: {e}")
            return False
    else:
        logger.info("現有憑證仍然有效。")
        
    return True

if __name__ == '__main__':
    logger.info("開始設定 Google Drive 授權...")
    if setup_google_drive_token():
        logger.info("Google Drive 授權設定成功完成！")
    else:
        logger.error("Google Drive 授權設定失敗。請檢查日誌中的錯誤訊息。") 