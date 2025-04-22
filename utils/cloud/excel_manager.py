"""
Excel Manager for cloud integrations
Handles reading and writing Excel files from/to Google Drive
"""
import os
import io
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any
from utils.cloud.google_drive_connector import GoogleDriveConnector

# 設置日誌
logger = logging.getLogger(__name__)

class CloudExcelManager:
    """
    管理雲端Excel文件的類
    提供讀取和寫入Excel文件的功能，支持多工作表
    """
    
    def __init__(self, drive_connector: GoogleDriveConnector = None):
        """
        初始化雲端Excel管理器
        
        參數:
            drive_connector (GoogleDriveConnector, optional): Google Drive連接器實例
        """
        self.drive_connector = drive_connector or GoogleDriveConnector()
        # 確保連接器已經認證
        if not self.drive_connector.authorized:
            self.drive_connector.authenticate()
        
        # 本地缓存
        self._cache = {}
        self._cache_timestamps = {}
    
    def read_excel(self, remote_path: str, sheet_name: Optional[Union[str, List[str], int, None]] = None, 
                   use_cache: bool = True, cache_max_age: int = 300) -> Union[pd.DataFrame, Dict[str, pd.DataFrame], None]:
        """
        從雲端讀取Excel文件
        
        參數:
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            sheet_name (str, List[str], int, None, optional): 
                - 如果是str或int，則返回指定工作表的DataFrame
                - 如果是List[str]，則返回包含指定工作表的字典
                - 如果是None，則返回所有工作表的字典
            use_cache (bool): 是否使用本地缓存
            cache_max_age (int): 緩存有效期（秒）
            
        返回:
            Union[pd.DataFrame, Dict[str, pd.DataFrame], None]: Excel數據，如果失敗則為None
        """
        try:
            # 檢查是否有有效的缓存
            cache_key = f"{remote_path}_{sheet_name}"
            if use_cache and cache_key in self._cache:
                import time
                current_time = time.time()
                cache_time = self._cache_timestamps.get(cache_key, 0)
                
                # 檢查缓存是否仍然有效
                if current_time - cache_time < cache_max_age:
                    logger.info(f"使用本地缓存讀取: {remote_path}")
                    return self._cache[cache_key]
            
            # 獲取文件內容
            file_content = self.drive_connector.get_file_content_by_path(remote_path)
            if not file_content:
                logger.error(f"無法從雲端獲取文件內容: {remote_path}")
                return None
            
            # 將內容轉換為DataFrame
            file_io = io.BytesIO(file_content)
            
            if sheet_name is not None:
                if isinstance(sheet_name, (str, int)):
                    # 讀取單個工作表
                    df = pd.read_excel(file_io, sheet_name=sheet_name)
                    result = df
                else:
                    # 讀取多個工作表
                    result = pd.read_excel(file_io, sheet_name=sheet_name)
            else:
                # 讀取所有工作表
                result = pd.read_excel(file_io, sheet_name=None)
            
            # 更新缓存
            if use_cache:
                import time
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"從雲端讀取Excel時出錯: {str(e)}")
            return None
    
    def write_excel(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
                    remote_path: str, sheet_name: Optional[str] = None) -> bool:
        """
        將數據寫入雲端Excel文件
        
        參數:
            data (Union[pd.DataFrame, Dict[str, pd.DataFrame]]): 
                - 如果是DataFrame，則寫入單個工作表
                - 如果是Dict，則寫入多個工作表
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            sheet_name (str, optional): 
                - 如果data是DataFrame且sheet_name不為None，則寫入指定工作表
                - 如果data是DataFrame且sheet_name為None，則覆蓋整個文件
                - 如果data是Dict，則忽略此參數
                
        返回:
            bool: 是否成功寫入
        """
        try:
            if isinstance(data, pd.DataFrame) and sheet_name is not None:
                # 讀取現有文件（如果存在）
                existing_data = self.read_excel(remote_path)
                
                if existing_data is not None and isinstance(existing_data, dict):
                    # 更新特定工作表
                    existing_data[sheet_name] = data
                    data_to_write = existing_data
                else:
                    # 文件不存在或讀取失敗，創建新文件
                    data_to_write = {sheet_name: data}
            elif isinstance(data, dict):
                # 直接寫入多個工作表
                data_to_write = data
            else:
                # 直接覆蓋整個文件
                data_to_write = data
            
            # 將數據寫入BytesIO
            output = io.BytesIO()
            
            if isinstance(data_to_write, dict):
                # 寫入多個工作表
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for sheet, df in data_to_write.items():
                        df.to_excel(writer, sheet_name=sheet, index=False)
            else:
                # 寫入單個工作表
                data_to_write.to_excel(output, index=False)
            
            # 獲取BytesIO的內容
            output.seek(0)
            file_content = output.getvalue()
            
            # 上傳到雲端
            file_id = self.drive_connector.upload_file_content(file_content, remote_path)
            
            if file_id:
                # 清除相關缓存
                for key in list(self._cache.keys()):
                    if key.startswith(f"{remote_path}_"):
                        del self._cache[key]
                        if key in self._cache_timestamps:
                            del self._cache_timestamps[key]
                
                logger.info(f"已成功寫入Excel文件到雲端: {remote_path}")
                return True
            else:
                logger.error(f"上傳Excel文件到雲端失敗: {remote_path}")
                return False
            
        except Exception as e:
            logger.error(f"寫入Excel到雲端時出錯: {str(e)}")
            return False
    
    def update_excel_sheet(self, df: pd.DataFrame, remote_path: str, sheet_name: str) -> bool:
        """
        更新雲端Excel文件中的特定工作表
        
        參數:
            df (pd.DataFrame): 要寫入的數據
            remote_path (str): 雲端文件路徑（如 'data/file.xlsx'）
            sheet_name (str): 工作表名稱
            
        返回:
            bool: 是否成功更新
        """
        try:
            # 讀取現有Excel文件
            existing_data = self.read_excel(remote_path)
            
            if existing_data is None:
                # 文件不存在，創建新文件
                data_to_write = {sheet_name: df}
            elif isinstance(existing_data, dict):
                # 文件存在，更新特定工作表
                existing_data[sheet_name] = df
                data_to_write = existing_data
            else:
                # 文件存在但只有一個工作表
                data_to_write = {sheet_name: df}
            
            # 寫入更新後的數據
            return self.write_excel(data_to_write, remote_path)
            
        except Exception as e:
            logger.error(f"更新雲端Excel工作表時出錯: {str(e)}")
            return False
    
    def read_excel_with_fallback(self, remote_path: str, local_path: str, 
                                sheet_name: Optional[Union[str, List[str], int, None]] = None) -> Union[pd.DataFrame, Dict[str, pd.DataFrame], None]:
        """
        從雲端讀取Excel文件，如果失敗則從本地讀取
        
        參數:
            remote_path (str): 雲端文件路徑
            local_path (str): 本地文件路徑
            sheet_name: 要讀取的工作表
            
        返回:
            Union[pd.DataFrame, Dict[str, pd.DataFrame], None]: Excel數據，如果失敗則為None
        """
        try:
            # 首先嘗試從雲端讀取
            cloud_data = self.read_excel(remote_path, sheet_name)
            if cloud_data is not None:
                # 將雲端數據同步到本地（作為備份）
                self._sync_cloud_to_local(remote_path, local_path)
                return cloud_data
            
            # 如果從雲端讀取失敗，嘗試從本地讀取
            if os.path.exists(local_path):
                logger.info(f"從雲端讀取失敗，使用本地文件: {local_path}")
                if sheet_name is not None:
                    return pd.read_excel(local_path, sheet_name=sheet_name)
                else:
                    return pd.read_excel(local_path, sheet_name=None)
            
            logger.error(f"無法從雲端或本地讀取Excel文件: {remote_path}")
            return None
            
        except Exception as e:
            logger.error(f"讀取Excel（帶備用）時出錯: {str(e)}")
            return None
    
    def write_excel_with_fallback(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
                                 remote_path: str, local_path: str, 
                                 sheet_name: Optional[str] = None) -> bool:
        """
        將數據寫入雲端Excel文件，並在本地保存備份
        
        參數:
            data: 要寫入的數據
            remote_path: 雲端文件路徑
            local_path: 本地文件路徑
            sheet_name: 工作表名稱（僅當data為DataFrame時使用）
            
        返回:
            bool: 是否成功寫入
        """
        try:
            # 確保本地目錄存在
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            # 首先嘗試寫入雲端
            cloud_success = self.write_excel(data, remote_path, sheet_name)
            
            # 同時寫入本地（無論雲端是否成功）
            try:
                # 準備本地寫入
                if isinstance(data, pd.DataFrame) and sheet_name is not None:
                    # 需要更新現有工作表
                    if os.path.exists(local_path):
                        # 讀取現有文件
                        with pd.ExcelFile(local_path) as xls:
                            existing_sheets = xls.sheet_names
                            existing_data = {s: pd.read_excel(local_path, sheet_name=s) for s in existing_sheets if s != sheet_name}
                        
                        # 添加或更新目標工作表
                        existing_data[sheet_name] = data
                        
                        # 寫入更新後的數據
                        with pd.ExcelWriter(local_path) as writer:
                            for s, df in existing_data.items():
                                df.to_excel(writer, sheet_name=s, index=False)
                    else:
                        # 創建新文件
                        with pd.ExcelWriter(local_path) as writer:
                            data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                elif isinstance(data, dict):
                    # 寫入多個工作表
                    with pd.ExcelWriter(local_path) as writer:
                        for s, df in data.items():
                            df.to_excel(writer, sheet_name=s, index=False)
                else:
                    # 直接覆蓋整個文件
                    data.to_excel(local_path, index=False)
                
                logger.info(f"已寫入本地Excel文件: {local_path}")
                
            except Exception as e:
                logger.error(f"寫入本地Excel文件時出錯: {str(e)}")
                # 本地寫入失敗不影響返回結果
            
            return cloud_success
            
        except Exception as e:
            logger.error(f"寫入Excel（帶備用）時出錯: {str(e)}")
            return False
    
    def _sync_cloud_to_local(self, remote_path: str, local_path: str) -> bool:
        """
        將雲端文件同步到本地
        
        參數:
            remote_path: 雲端文件路徑
            local_path: 本地文件路徑
            
        返回:
            bool: 是否成功同步
        """
        try:
            # 確保本地目錄存在
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            # 下載雲端文件
            return self.drive_connector.download_file_by_path(remote_path, local_path)
            
        except Exception as e:
            logger.error(f"同步雲端到本地時出錯: {str(e)}")
            return False
    
    def _sync_local_to_cloud(self, local_path: str, remote_path: str) -> bool:
        """
        將本地文件同步到雲端
        
        參數:
            local_path: 本地文件路徑
            remote_path: 雲端文件路徑
            
        返回:
            bool: 是否成功同步
        """
        try:
            if not os.path.exists(local_path):
                logger.error(f"本地文件不存在: {local_path}")
                return False
            
            # 上傳本地文件
            file_id = self.drive_connector.upload_file(local_path, None, remote_path)
            return file_id is not None
            
        except Exception as e:
            logger.error(f"同步本地到雲端時出錯: {str(e)}")
            return False
    
    def resolve_conflict(self, remote_path: str, local_path: str, sheet_name: Optional[str] = None, 
                         strategy: str = 'cloud_wins') -> Union[pd.DataFrame, Dict[str, pd.DataFrame], None]:
        """
        解決雲端和本地文件之間的衝突
        
        參數:
            remote_path: 雲端文件路徑
            local_path: 本地文件路徑
            sheet_name: 要處理的工作表
            strategy: 衝突解決策略 ('cloud_wins', 'local_wins', 'merge')
            
        返回:
            解決衝突後的數據
        """
        try:
            # 獲取雲端數據
            cloud_data = self.read_excel(remote_path, sheet_name)
            
            # 獲取本地數據
            if os.path.exists(local_path):
                if sheet_name is not None:
                    local_data = pd.read_excel(local_path, sheet_name=sheet_name)
                else:
                    local_data = pd.read_excel(local_path, sheet_name=None)
            else:
                local_data = None
            
            # 如果其中一個不存在，返回另一個
            if cloud_data is None:
                return local_data
            if local_data is None:
                return cloud_data
            
            # 根據策略解決衝突
            if strategy == 'cloud_wins':
                return cloud_data
            elif strategy == 'local_wins':
                return local_data
            elif strategy == 'merge':
                # 根據數據類型進行合併
                if isinstance(cloud_data, pd.DataFrame) and isinstance(local_data, pd.DataFrame):
                    # 合併兩個DataFrame
                    merged_data = pd.concat([cloud_data, local_data]).drop_duplicates().reset_index(drop=True)
                    return merged_data
                elif isinstance(cloud_data, dict) and isinstance(local_data, dict):
                    # 合併兩個字典
                    merged_data = {}
                    all_sheets = set(list(cloud_data.keys()) + list(local_data.keys()))
                    
                    for sheet in all_sheets:
                        if sheet in cloud_data and sheet in local_data:
                            # 兩個都有此工作表，合併
                            merged_data[sheet] = pd.concat([cloud_data[sheet], local_data[sheet]]).drop_duplicates().reset_index(drop=True)
                        elif sheet in cloud_data:
                            # 只有雲端有此工作表
                            merged_data[sheet] = cloud_data[sheet]
                        else:
                            # 只有本地有此工作表
                            merged_data[sheet] = local_data[sheet]
                    
                    return merged_data
                else:
                    # 類型不匹配，使用雲端數據
                    logger.warning("雲端和本地數據類型不匹配，使用雲端數據")
                    return cloud_data
            else:
                logger.error(f"未知的衝突解決策略: {strategy}")
                return cloud_data
            
        except Exception as e:
            logger.error(f"解決衝突時出錯: {str(e)}")
            return None
    
    def clear_cache(self, remote_path: Optional[str] = None) -> None:
        """
        清除本地緩存
        
        參數:
            remote_path (Optional[str]): 如果指定，只清除此路徑的緩存；否則清除所有緩存
        """
        if remote_path:
            # 清除特定路徑的緩存
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{remote_path}_")]
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
            logger.info(f"已清除路徑的緩存: {remote_path}")
        else:
            # 清除所有緩存
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("已清除所有緩存")
    
    def create_share_link(self, remote_path: str) -> Optional[str]:
        """
        為雲端Excel文件創建分享連結
        
        參數:
            remote_path (str): 雲端文件路徑
            
        返回:
            Optional[str]: 分享連結，如果失敗則為None
        """
        return self.drive_connector.create_share_link_by_path(remote_path)
