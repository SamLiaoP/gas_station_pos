"""
Google Drive Connector for GAS_STATION_POS_v2
Handles authentication and basic file operations with Google Drive API
"""
import os
import io
import pickle
import logging
from typing import List, Dict, Optional, Union, Tuple, Any
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
import time

# 設置日誌
logger = logging.getLogger(__name__)

class GoogleDriveConnector:
    """
    處理Google Drive API連接和操作的類
    """
    # 定義應用程序所需的權限範圍
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_path='config/credentials.json', token_path='config/token.pickle'):
        """
        初始化Google Drive連接器
        
        參數:
            credentials_path (str): OAuth 2.0憑證JSON文件的路徑
            token_path (str): 保存授權令牌的路徑
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.root_folder_id = None
        self.root_folder_name = 'GAS_STATION_POS'
        self.authorized = False
        
    def authenticate(self) -> bool:
        """
        執行OAuth 2.0認證流程
        
        返回:
            bool: 認證是否成功
        """
        try:
            creds = None
            
            # 嘗試從現有令牌加載憑證
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # 如果沒有憑證或已失效，則執行認證流程
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        # 刷新令牌失效，需要重新認證
                        if os.path.exists(self.credentials_path):
                            flow = InstalledAppFlow.from_client_secrets_file(
                                self.credentials_path, self.SCOPES)
                            creds = flow.run_local_server(port=0)
                        else:
                            logger.error(f"找不到憑證文件: {self.credentials_path}")
                            return False
                else:
                    # 需要全新的認證
                    if os.path.exists(self.credentials_path):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.error(f"找不到憑證文件: {self.credentials_path}")
                        return False
                
                # 保存令牌供以後使用
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            # 創建Drive API服務
            self.service = build('drive', 'v3', credentials=creds)
            self.authorized = True
            
            # 確保根文件夾存在
            self._ensure_root_folder()
            
            return True
            
        except Exception as e:
            logger.error(f"Google Drive認證失敗: {str(e)}")
            self.authorized = False
            return False
    
    def _ensure_root_folder(self) -> None:
        """
        確保Google Drive上存在根文件夾
        """
        if not self.service:
            logger.error("未認證，無法創建根文件夾")
            return
        
        # 查找根文件夾
        query = f"name = '{self.root_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            # 找到現有文件夾
            self.root_folder_id = items[0]['id']
            logger.info(f"找到現有根文件夾: {self.root_folder_name}")
        else:
            # 創建新文件夾
            folder_metadata = {
                'name': self.root_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            self.root_folder_id = folder.get('id')
            logger.info(f"已創建新的根文件夾: {self.root_folder_name}")
        
        # 確保存在data和reports子文件夾
        self._ensure_subfolder('data')
        self._ensure_subfolder('reports')
    
    def _ensure_subfolder(self, folder_name: str) -> Optional[str]:
        """
        確保在根文件夾下存在指定的子文件夾
        
        參數:
            folder_name (str): 子文件夾名稱
            
        返回:
            Optional[str]: 子文件夾ID，如果失敗則為None
        """
        if not self.service or not self.root_folder_id:
            logger.error("未認證或無根文件夾，無法創建子文件夾")
            return None
        
        # 查找子文件夾
        query = f"name = '{folder_name}' and '{self.root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            # 找到現有文件夾
            subfolder_id = items[0]['id']
            logger.info(f"找到現有子文件夾: {folder_name}")
            return subfolder_id
        else:
            # 創建新文件夾
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.root_folder_id]
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            subfolder_id = folder.get('id')
            logger.info(f"已創建新的子文件夾: {folder_name}")
            return subfolder_id
    
    def get_folder_id(self, path: str) -> Optional[str]:
        """
        獲取指定路徑的文件夾ID
        
        參數:
            path (str): 文件夾路徑，例如 'data' 或 'reports/monthly'
            
        返回:
            Optional[str]: 文件夾ID，如果不存在或失敗則為None
        """
        if not self.service or not self.root_folder_id:
            if not self.authenticate():
                return None
        
        path_parts = path.strip('/').split('/')
        current_folder_id = self.root_folder_id
        
        for part in path_parts:
            if not part:  # 跳過空部分
                continue
                
            query = f"name = '{part}' and '{current_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if not items:
                logger.warning(f"路徑中的文件夾不存在: {part}")
                return None
            
            current_folder_id = items[0]['id']
        
        return current_folder_id
    
    def ensure_directory(self, path: str) -> Optional[str]:
        """
        確保指定路徑的目錄存在（如果不存在則創建）
        
        參數:
            path (str): 目錄路徑，例如 'data' 或 'reports/monthly'
            
        返回:
            Optional[str]: 目錄ID，如果失敗則為None
        """
        if not self.service or not self.root_folder_id:
            if not self.authenticate():
                return None
        
        path_parts = path.strip('/').split('/')
        current_parent_id = self.root_folder_id
        
        for i, part in enumerate(path_parts):
            if not part:  # 跳過空部分
                continue
                
            # 查詢當前部分是否存在
            query = f"name = '{part}' and '{current_parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if items:
                # 文件夾存在，繼續處理路徑的下一部分
                current_parent_id = items[0]['id']
            else:
                # 文件夾不存在，創建它
                folder_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [current_parent_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                current_parent_id = folder.get('id')
                logger.info(f"已創建新文件夾: {'/'.join(path_parts[:i+1])}")
        
        return current_parent_id
    
    def find_file(self, file_name: str, folder_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        在Google Drive上查找文件
        
        參數:
            file_name (str): 文件名稱
            folder_path (Optional[str]): 要查找的文件夾路徑，默認為根文件夾
            
        返回:
            Optional[Dict[str, Any]]: 文件元數據，如果不存在則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        parent_id = self.root_folder_id
        if folder_path:
            parent_id = self.get_folder_id(folder_path)
            if not parent_id:
                logger.warning(f"找不到文件夾: {folder_path}")
                return None
        
        query = f"name = '{file_name}' and '{parent_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name, createdTime, modifiedTime, size)').execute()
        items = results.get('files', [])
        
        return items[0] if items else None
    
    def upload_file(self, local_path: str, remote_folder_path: Optional[str] = None, remote_filename: Optional[str] = None) -> Optional[str]:
        """
        將文件上傳到Google Drive
        
        參數:
            local_path (str): 本地文件路徑
            remote_folder_path (Optional[str]): 雲端文件夾路徑，默認為根文件夾
            remote_filename (Optional[str]): 雲端文件名稱，默認使用本地文件名
            
        返回:
            Optional[str]: 上傳的文件ID，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        if not os.path.exists(local_path):
            logger.error(f"本地文件不存在: {local_path}")
            return None
        
        # 獲取父文件夾ID
        parent_id = self.root_folder_id
        if remote_folder_path:
            parent_id = self.ensure_directory(remote_folder_path)
            if not parent_id:
                logger.error(f"無法確保文件夾存在: {remote_folder_path}")
                return None
        
        # 決定文件名
        if not remote_filename:
            remote_filename = os.path.basename(local_path)
        
        # 檢查文件是否已存在
        existing_file = self.find_file(remote_filename, remote_folder_path)
        
        # 準備上傳
        file_metadata = {
            'name': remote_filename,
            'parents': [parent_id]
        }
        
        media = MediaFileUpload(local_path, resumable=True)
        
        try:
            if existing_file:
                # 更新現有文件
                file = self.service.files().update(
                    fileId=existing_file['id'],
                    body={'name': remote_filename},
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"已更新文件: {remote_filename}")
                return file.get('id')
            else:
                # 創建新文件
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"已上傳文件: {remote_filename}")
                return file.get('id')
        except Exception as e:
            logger.error(f"上傳文件 {remote_filename} 時出錯: {str(e)}")
            return None
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        從Google Drive下載文件
        
        參數:
            file_id (str): 文件ID
            local_path (str): 保存到本地的路徑
            
        返回:
            bool: 是否成功下載
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # 確保目標目錄存在
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            # 創建下載請求
            request = self.service.files().get_media(fileId=file_id)
            
            # 下載文件內容
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"已下載文件到: {local_path}")
            return True
        
        except Exception as e:
            logger.error(f"下載文件到 {local_path} 時出錯: {str(e)}")
            return False
    
    def download_file_by_path(self, remote_path: str, local_path: str) -> bool:
        """
        通過雲端路徑從Google Drive下載文件
        
        參數:
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            local_path (str): 保存到本地的路徑
            
        返回:
            bool: 是否成功下載
        """
        # 分解路徑
        remote_parts = remote_path.strip('/').split('/')
        remote_filename = remote_parts[-1]
        remote_folder_path = '/'.join(remote_parts[:-1]) if len(remote_parts) > 1 else None
        
        # 查找文件
        file_info = self.find_file(remote_filename, remote_folder_path)
        if not file_info:
            logger.error(f"找不到雲端文件: {remote_path}")
            return False
        
        # 下載文件
        return self.download_file(file_info['id'], local_path)
    
    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """
        獲取Google Drive文件的內容
        
        參數:
            file_id (str): 文件ID
            
        返回:
            Optional[bytes]: 文件內容，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # 創建下載請求
            request = self.service.files().get_media(fileId=file_id)
            
            # 下載到內存
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content.getvalue()
            
        except Exception as e:
            logger.error(f"獲取文件內容時出錯: {str(e)}")
            return None
    
    def get_file_content_by_path(self, remote_path: str) -> Optional[bytes]:
        """
        通過雲端路徑獲取Google Drive文件的內容
        
        參數:
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            
        返回:
            Optional[bytes]: 文件內容，如果失敗則為None
        """
        # 分解路徑
        remote_parts = remote_path.strip('/').split('/')
        remote_filename = remote_parts[-1]
        remote_folder_path = '/'.join(remote_parts[:-1]) if len(remote_parts) > 1 else None
        
        # 查找文件
        file_info = self.find_file(remote_filename, remote_folder_path)
        if not file_info:
            logger.error(f"找不到雲端文件: {remote_path}")
            return None
        
        # 獲取文件內容
        return self.get_file_content(file_info['id'])
    
    def upload_file_content(self, content: bytes, remote_path: str) -> Optional[str]:
        """
        將內容上傳為Google Drive文件
        
        參數:
            content (bytes): 文件內容
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            
        返回:
            Optional[str]: 上傳的文件ID，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        # 分解路徑
        remote_parts = remote_path.strip('/').split('/')
        remote_filename = remote_parts[-1]
        remote_folder_path = '/'.join(remote_parts[:-1]) if len(remote_parts) > 1 else None
        
        # 獲取父文件夾ID
        parent_id = self.root_folder_id
        if remote_folder_path:
            parent_id = self.ensure_directory(remote_folder_path)
            if not parent_id:
                logger.error(f"無法確保文件夾存在: {remote_folder_path}")
                return None
        
        # 檢查文件是否已存在
        existing_file = self.find_file(remote_filename, remote_folder_path)
        
        # 準備上傳
        file_metadata = {
            'name': remote_filename,
            'parents': [parent_id]
        }
        
        # 創建臨時內存文件
        file_content = io.BytesIO(content)
        media = MediaIoBaseUpload(file_content, mimetype='application/octet-stream', resumable=True)
        
        try:
            if existing_file:
                # 更新現有文件
                file = self.service.files().update(
                    fileId=existing_file['id'],
                    body={'name': remote_filename},
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"已更新文件: {remote_filename}")
                return file.get('id')
            else:
                # 創建新文件
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"已上傳文件: {remote_filename}")
                return file.get('id')
        except Exception as e:
            logger.error(f"上傳文件 {remote_filename} 時出錯: {str(e)}")
            return None
    
    def list_files(self, folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夾中的所有文件
        
        參數:
            folder_path (Optional[str]): 文件夾路徑，默認為根文件夾
            
        返回:
            List[Dict[str, Any]]: 文件列表
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        # 獲取文件夾ID
        folder_id = self.root_folder_id
        if folder_path:
            folder_id = self.get_folder_id(folder_path)
            if not folder_id:
                logger.warning(f"找不到文件夾: {folder_path}")
                return []
        
        # 查詢文件夾內容
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, modifiedTime, size)'
        ).execute()
        
        return results.get('files', [])
    
    def create_folder(self, folder_name: str, parent_path: Optional[str] = None) -> Optional[str]:
        """
        在Google Drive上創建文件夾
        
        參數:
            folder_name (str): 文件夾名稱
            parent_path (Optional[str]): 父文件夾路徑，默認為根文件夾
            
        返回:
            Optional[str]: 創建的文件夾ID，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        # 獲取父文件夾ID
        parent_id = self.root_folder_id
        if parent_path:
            parent_id = self.get_folder_id(parent_path)
            if not parent_id:
                logger.warning(f"找不到父文件夾: {parent_path}")
                return None
        
        # 檢查文件夾是否已存在
        query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            # 文件夾已存在
            logger.info(f"文件夾已存在: {folder_name}")
            return items[0]['id']
        
        # 創建新文件夾
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        
        try:
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            logger.info(f"已創建文件夾: {folder_name}")
            return folder.get('id')
        except Exception as e:
            logger.error(f"創建文件夾 {folder_name} 時出錯: {str(e)}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        從Google Drive刪除文件
        
        參數:
            file_id (str): 文件ID
            
        返回:
            bool: 是否成功刪除
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"已刪除文件: {file_id}")
            return True
        except Exception as e:
            logger.error(f"刪除文件 {file_id} 時出錯: {str(e)}")
            return False
    
    def delete_file_by_path(self, remote_path: str) -> bool:
        """
        通過雲端路徑從Google Drive刪除文件
        
        參數:
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            
        返回:
            bool: 是否成功刪除
        """
        # 分解路徑
        remote_parts = remote_path.strip('/').split('/')
        remote_filename = remote_parts[-1]
        remote_folder_path = '/'.join(remote_parts[:-1]) if len(remote_parts) > 1 else None
        
        # 查找文件
        file_info = self.find_file(remote_filename, remote_folder_path)
        if not file_info:
            logger.error(f"找不到雲端文件: {remote_path}")
            return False
        
        # 刪除文件
        return self.delete_file(file_info['id'])
    
    def create_share_link(self, file_id: str, role: str = 'reader', type: str = 'anyone') -> Optional[str]:
        """
        為文件創建分享連結
        
        參數:
            file_id (str): 文件ID
            role (str): 權限角色，'reader'、'writer'或'commenter'
            type (str): 訪問類型，'user'、'group'、'domain'或'anyone'
            
        返回:
            Optional[str]: 分享連結，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # 創建權限
            permission = {
                'type': type,
                'role': role,
                'allowFileDiscovery': False
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id',
            ).execute()
            
            # 獲取文件信息以構建分享連結
            file_info = self.service.files().get(fileId=file_id, fields='webViewLink').execute()
            
            return file_info.get('webViewLink')
            
        except Exception as e:
            logger.error(f"創建分享連結時出錯: {str(e)}")
            return None
    
    def create_share_link_by_path(self, remote_path: str, role: str = 'reader', type: str = 'anyone') -> Optional[str]:
        """
        通過雲端路徑為文件創建分享連結
        
        參數:
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            role (str): 權限角色，'reader'、'writer'或'commenter'
            type (str): 訪問類型，'user'、'group'、'domain'或'anyone'
            
        返回:
            Optional[str]: 分享連結，如果失敗則為None
        """
        # 分解路徑
        remote_parts = remote_path.strip('/').split('/')
        remote_filename = remote_parts[-1]
        remote_folder_path = '/'.join(remote_parts[:-1]) if len(remote_parts) > 1 else None
        
        # 查找文件
        file_info = self.find_file(remote_filename, remote_folder_path)
        if not file_info:
            logger.error(f"找不到雲端文件: {remote_path}")
            return None
        
        # 創建分享連結
        return self.create_share_link(file_info['id'], role, type)
        
    def check_connection(self) -> bool:
        """
        檢查與Google Drive的連接狀態
        
        返回:
            bool: 是否連接正常
        """
        if not self.service:
            return self.authenticate()
        
        try:
            # 嘗試進行一個簡單的API調用
            self.service.files().list(pageSize=1).execute()
            return True
        except Exception as e:
            logger.error(f"連接檢查失敗: {str(e)}")
            self.authorized = False
            return False
            
    def get_last_modified_time(self, file_id: str) -> Optional[str]:
        """
        獲取文件的最後修改時間
        
        參數:
            file_id (str): 文件ID
            
        返回:
            Optional[str]: 最後修改時間，如果失敗則為None
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            file_info = self.service.files().get(fileId=file_id, fields='modifiedTime').execute()
            return file_info.get('modifiedTime')
        except Exception as e:
            logger.error(f"獲取文件修改時間時出錯: {str(e)}")
            return None
