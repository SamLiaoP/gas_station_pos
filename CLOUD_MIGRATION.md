# 雲端整合遷移指南

本文件說明如何將 GAS_STATION_POS_v2 系統與雲端硬碟整合，以便在不同裝置間同步資料。

## 前置需求

1. Google 帳號 (用於 Google Drive 整合)
2. Python 3.7 或更高版本
3. 安裝 Google Drive API 相關套件

## 安裝雲端整合所需套件

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## 整合步驟

### 1. 建立 Google Drive API 憑證

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建一個新專案
3. 啟用 Google Drive API
4. 創建 OAuth 2.0 憑證
5. 下載憑證 JSON 檔案並命名為 `credentials.json`，放置於專案根目錄

### 2. 修改 cloud_helper.py

將 `cloud_helper.py` 中的範例函數改寫為實際的 Google Drive API 調用。以下是參考實作：

```python
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import pickle
import io
import pandas as pd
from utils.common import logger

# 定義存取 Google Drive 的權限範圍
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """獲取授權的 Google Drive 服務"""
    creds = None
    # 檢查是否有已存在的令牌
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # 如果沒有憑證或已失效，重新登入
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 保存憑證供下次使用
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def find_file_by_name(service, file_name, folder_id=None):
    """在 Google Drive 中查找檔案"""
    query = f"name = '{file_name}' and trashed = false"
    if folder_id:
        query += f" and '{folder_id}' in parents"
        
    results = service.files().list(
        q=query, fields="files(id, name)").execute()
        
    items = results.get('files', [])
    return items[0] if items else None

def read_excel_from_cloud(file_path, sheet_name=None):
    """從 Google Drive 讀取 Excel 檔案"""
    try:
        service = get_drive_service()
        file_name = os.path.basename(file_path)
        
        # 查找檔案
        file_metadata = find_file_by_name(service, file_name)
        if not file_metadata:
            logger.error(f"雲端找不到檔案: {file_name}")
            return pd.DataFrame() if sheet_name else None
        
        # 下載檔案
        file_id = file_metadata['id']
        request = service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_content.seek(0)
        
        # 讀取 Excel
        if sheet_name:
            return pd.read_excel(file_content, sheet_name=sheet_name)
        else:
            return pd.read_excel(file_content)
            
    except Exception as e:
        logger.error(f"從雲端讀取 Excel 檔案時出錯: {str(e)}")
        return pd.DataFrame() if sheet_name else None

def write_excel_to_cloud(data, file_path, sheet_name=None):
    """寫入 Excel 檔案到 Google Drive"""
    try:
        service = get_drive_service()
        file_name = os.path.basename(file_path)
        
        # 創建臨時檔案
        temp_file = f"temp_{file_name}"
        
        if sheet_name:
            # 如果要寫入特定工作表，需要先讀取現有檔案
            existing_file = find_file_by_name(service, file_name)
            
            if existing_file:
                # 下載現有檔案
                existing_content = read_excel_from_cloud(file_path)
                
                if existing_content is not None:
                    # 使用 ExcelWriter 寫入多個工作表
                    with pd.ExcelWriter(temp_file) as writer:
                        # 寫入所有現有工作表
                        with pd.ExcelFile(io.BytesIO(existing_content)) as xls:
                            for sheet in xls.sheet_names:
                                if sheet != sheet_name:
                                    sheet_data = pd.read_excel(io.BytesIO(existing_content), sheet_name=sheet)
                                    sheet_data.to_excel(writer, sheet_name=sheet, index=False)
                        
                        # 寫入/替換目標工作表
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # 檔案不存在，創建新檔案
                with pd.ExcelWriter(temp_file) as writer:
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # 直接覆蓋整個檔案
            data.to_excel(temp_file, index=False)
        
        # 上傳檔案到 Google Drive
        file_metadata = {'name': file_name}
        media = MediaFileUpload(temp_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # 查找是否已存在同名檔案
        existing_file = find_file_by_name(service, file_name)
        
        if existing_file:
            # 更新現有檔案
            service.files().update(
                fileId=existing_file['id'],
                body=file_metadata,
                media_body=media).execute()
        else:
            # 創建新檔案
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id').execute()
        
        # 刪除臨時檔案
        os.remove(temp_file)
        return True
            
    except Exception as e:
        logger.error(f"將 Excel 檔案寫入雲端時出錯: {str(e)}")
        # 確保清理臨時檔案
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def is_file_exists_in_cloud(file_path):
    """檢查 Google Drive 中檔案是否存在"""
    try:
        service = get_drive_service()
        file_name = os.path.basename(file_path)
        
        # 查找檔案
        file_metadata = find_file_by_name(service, file_name)
        return file_metadata is not None
        
    except Exception as e:
        logger.error(f"檢查雲端檔案時出錯: {str(e)}")
        return False
```

### 3. 修改 models/data_manager.py

修改 `models/data_manager.py` 中的檔案讀寫函數，使用雲端助手：

```python
# 在文件頂部添加導入
from cloud_helper import read_excel_from_cloud, write_excel_to_cloud, is_file_exists_in_cloud

# 修改 read_master_data 函數
def read_master_data(sheet_name):
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    ensure_master_data()  # 確保文件存在
    
    try:
        # 從雲端讀取
        return read_excel_from_cloud(master_data_path, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"讀取主數據 {sheet_name} 時出錯: {str(e)}")
        return pd.DataFrame()

# 修改 save_master_data 函數
def save_master_data(df, sheet_name):
    master_data_path = os.path.join(DATA_PATH, 'master_data.xlsx')
    ensure_master_data()  # 確保文件存在
    
    try:
        # 寫入雲端
        success = write_excel_to_cloud(df, master_data_path, sheet_name=sheet_name)
        
        if success:
            logger.info(f"已更新主數據 {sheet_name}")
            return True
        else:
            logger.error(f"保存主數據 {sheet_name} 到雲端時出錯")
            return False
    except Exception as e:
        logger.error(f"保存主數據 {sheet_name} 時出錯: {str(e)}")
        return False
```

### 4. 測試雲端整合

1. 運行系統並進行基本操作，確保能成功讀寫雲端檔案
2. 檢查 Google Drive 中是否有相應的檔案
3. 在不同裝置上運行系統，確認資料同步正常

## 注意事項

1. 請確保網路連接穩定
2. 考慮實作資料衝突解決機制
3. 定期備份雲端資料
4. 保管好 OAuth 憑證，避免未授權存取
5. 謹慎處理權限設定，避免資料洩露

## 常見問題

### Q: 雲端整合後系統啟動變慢怎麼辦？
A: 可以實作資料快取機制，減少不必要的雲端請求。

### Q: 如果多人同時修改同一檔案怎麼處理？
A: 考慮實作樂觀鎖或版本控制機制，檢測並解決衝突。

### Q: 雲端連接失敗如何處理？
A: 實作本地備份和斷線重連機制，確保資料安全性。
