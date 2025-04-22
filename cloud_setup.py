#!/usr/bin/env python
"""
Google Drive 雲端整合設置工具

這個工具用於設置和管理 GAS_STATION_POS_v2 系統的雲端整合功能。
它可以幫助您：
1. 設置 Google Drive API 憑證
2. 測試雲端連接
3. 同步本地數據到雲端
4. 切換雲端/本地模式
5. 解決數據衝突

使用方法:
    python cloud_setup.py [命令]

可用命令:
    setup       - 設置 Google Drive API 憑證
    test        - 測試雲端連接
    sync        - 同步本地數據到雲端
    mode        - 切換雲端/本地模式
    resolve     - 解決數據衝突
    help        - 顯示幫助信息
"""

import os
import sys
import time
import argparse
import webbrowser
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.cloud_config_manager import CloudConfigManager
from utils.cloud.excel_manager import CloudExcelManager
from utils.common import DATA_PATH, REPORTS_PATH, logger, ensure_directories

def setup_credentials():
    """設置 Google Drive API 憑證"""
    config = CloudConfigManager()
    credentials_path = config.get("credentials_path")
    
    print("===== Google Drive API 憑證設置 =====")
    print("請按照以下步驟操作：")
    print("1. 前往 Google Cloud Console 創建專案和 OAuth 2.0 憑證")
    print("2. 啟用 Google Drive API")
    print("3. 下載憑證 JSON 文件")
    print("4. 將下載的憑證文件保存到以下路徑：")
    print(f"   {os.path.abspath(credentials_path)}")
    
    while True:
        user_input = input("\n您是否已經準備好憑證文件？(y/n): ").strip().lower()
        if user_input == 'y':
            break
        elif user_input == 'n':
            webbrowser.open("https://console.cloud.google.com/apis/credentials")
            user_input = input("\n準備好後，按 Enter 繼續...")
        else:
            print("無效的輸入，請輸入 y 或 n")
    
    # 檢查憑證文件
    if os.path.exists(credentials_path):
        print(f"\n已找到憑證文件: {credentials_path}")
    else:
        print(f"\n錯誤: 找不到憑證文件: {credentials_path}")
        print("請確保您已將憑證文件保存到正確的位置")
        return False
    
    # 測試連接
    print("\n正在測試 Google Drive 連接...")
    connector = GoogleDriveConnector(credentials_path=credentials_path)
    
    if connector.authenticate():
        print("連接成功！已成功設置 Google Drive API 憑證")
        
        # 啟用雲端模式
        config.toggle_cloud_mode(True)
        print("已啟用雲端模式")
        
        return True
    else:
        print("連接失敗！請檢查憑證文件和網絡連接")
        return False

def test_connection():
    """測試雲端連接"""
    config = CloudConfigManager()
    
    if not config.is_cloud_mode():
        print("當前處於本地模式，無法測試雲端連接")
        user_input = input("是否切換到雲端模式？(y/n): ").strip().lower()
        if user_input == 'y':
            config.toggle_cloud_mode(True)
            print("已切換到雲端模式")
        else:
            return False
    
    print("正在測試雲端連接...")
    connector = GoogleDriveConnector(
        credentials_path=config.get("credentials_path"),
        token_path=config.get("token_path")
    )
    
    if connector.authenticate():
        print("連接成功！")
        
        # 檢查根文件夾
        root_folder_name = config.get("root_folder_name")
        print(f"正在檢查根文件夾: {root_folder_name}")
        
        # 檢查數據文件夾
        data_folder_name = config.get("data_folder_name")
        data_folder_path = f"{data_folder_name}"
        data_folder_id = connector.get_folder_id(data_folder_path)
        
        if data_folder_id:
            print(f"已找到數據文件夾: {data_folder_path}")
            
            # 列出文件夾內容
            files = connector.list_files(data_folder_path)
            if files:
                print(f"文件夾中包含 {len(files)} 個文件/文件夾:")
                for file in files:
                    file_type = "文件夾" if file.get('mimeType') == 'application/vnd.google-apps.folder' else "文件"
                    print(f"  - {file['name']} ({file_type})")
            else:
                print("文件夾為空")
        else:
            print(f"未找到數據文件夾，將創建: {data_folder_path}")
            folder_id = connector.ensure_directory(data_folder_path)
            if folder_id:
                print(f"成功創建數據文件夾: {data_folder_path}")
            else:
                print(f"創建數據文件夾失敗: {data_folder_path}")
        
        # 檢查報表文件夾
        reports_folder_name = config.get("reports_folder_name")
        reports_folder_path = f"{reports_folder_name}"
        reports_folder_id = connector.get_folder_id(reports_folder_path)
        
        if reports_folder_id:
            print(f"已找到報表文件夾: {reports_folder_path}")
            
            # 列出文件夾內容
            files = connector.list_files(reports_folder_path)
            if files:
                print(f"文件夾中包含 {len(files)} 個文件/文件夾")
            else:
                print("文件夾為空")
        else:
            print(f"未找到報表文件夾，將創建: {reports_folder_path}")
            folder_id = connector.ensure_directory(reports_folder_path)
            if folder_id:
                print(f"成功創建報表文件夾: {reports_folder_path}")
            else:
                print(f"創建報表文件夾失敗: {reports_folder_path}")
        
        return True
    else:
        print("連接失敗！請檢查憑證和網絡連接")
        return False

def sync_data():
    """同步本地數據到雲端"""
    config = CloudConfigManager()
    
    if not config.is_cloud_mode():
        print("當前處於本地模式，無法同步數據")
        user_input = input("是否切換到雲端模式？(y/n): ").strip().lower()
        if user_input == 'y':
            config.toggle_cloud_mode(True)
            print("已切換到雲端模式")
        else:
            return False
    
    # 確保本地目錄存在
    ensure_directories()
    
    # 初始化雲端連接器
    connector = GoogleDriveConnector(
        credentials_path=config.get("credentials_path"),
        token_path=config.get("token_path")
    )
    
    if not connector.authenticate():
        print("雲端連接失敗！無法同步數據")
        return False
    
    # 確保雲端目錄存在
    data_folder_path = config.get("data_folder_name")
    reports_folder_path = config.get("reports_folder_name")
    
    connector.ensure_directory(data_folder_path)
    connector.ensure_directory(reports_folder_path)
    
    # 同步數據文件
    print("\n===== 同步數據文件 =====")
    
    data_files = ["master_data.xlsx", "inventory.xlsx", "transactions.xlsx"]
    for filename in data_files:
        local_path = os.path.join(DATA_PATH, filename)
        remote_path = f"{data_folder_path}/{filename}"
        
        if os.path.exists(local_path):
            print(f"正在同步 {filename}...")
            
            # 檢查雲端文件是否存在
            remote_file = connector.find_file_by_path(remote_path)
            
            if remote_file:
                print(f"雲端已存在 {filename}，檢查修改時間...")
                
                # 獲取本地和雲端的修改時間
                local_modified = os.path.getmtime(local_path)
                
                try:
                    # 解析雲端修改時間
                    from datetime import datetime
                    cloud_modified = remote_file.get('modifiedTime')
                    cloud_dt = datetime.strptime(cloud_modified.replace('Z', '+00:00'), "%Y-%m-%dT%H:%M:%S.%f%z")
                    cloud_timestamp = cloud_dt.timestamp()
                    
                    print(f"  - 本地修改時間: {datetime.fromtimestamp(local_modified)}")
                    print(f"  - 雲端修改時間: {cloud_dt}")
                    
                    if cloud_timestamp > local_modified:
                        print("雲端文件較新，將下載到本地...")
                        if connector.download_file(remote_file['id'], local_path):
                            print(f"已成功下載 {filename}")
                        else:
                            print(f"下載 {filename} 失敗")
                    else:
                        print("本地文件較新，將上傳到雲端...")
                        if connector.upload_file(local_path, data_folder_path, filename):
                            print(f"已成功上傳 {filename}")
                        else:
                            print(f"上傳 {filename} 失敗")
                            
                except Exception as e:
                    print(f"處理修改時間時出錯: {str(e)}")
                    print("默認上傳本地文件...")
                    if connector.upload_file(local_path, data_folder_path, filename):
                        print(f"已成功上傳 {filename}")
                    else:
                        print(f"上傳 {filename} 失敗")
            else:
                print(f"雲端不存在 {filename}，將上傳本地文件...")
                if connector.upload_file(local_path, data_folder_path, filename):
                    print(f"已成功上傳 {filename}")
                else:
                    print(f"上傳 {filename} 失敗")
        else:
            print(f"本地不存在 {filename}，檢查雲端...")
            
            remote_file = connector.find_file_by_path(remote_path)
            if remote_file:
                print(f"雲端存在 {filename}，將下載到本地...")
                if connector.download_file(remote_file['id'], local_path):
                    print(f"已成功下載 {filename}")
                else:
                    print(f"下載 {filename} 失敗")
            else:
                print(f"雲端也不存在 {filename}，跳過")
    
    print("\n===== 同步報表文件 =====")
    
    # 同步報表目錄
    if os.path.exists(REPORTS_PATH):
        for root, dirs, files in os.walk(REPORTS_PATH):
            # 獲取相對路徑
            rel_path = os.path.relpath(root, REPORTS_PATH)
            if rel_path == '.':
                rel_path = ''
            
            # 構建雲端路徑
            cloud_path = f"{reports_folder_path}/{rel_path}" if rel_path else reports_folder_path
            
            # 確保雲端目錄存在
            connector.ensure_directory(cloud_path)
            
            # 同步文件
            for filename in files:
                local_file_path = os.path.join(root, filename)
                remote_file_path = f"{cloud_path}/{filename}"
                
                print(f"正在同步報表: {rel_path}/{filename}")
                
                # 檢查雲端文件是否存在
                remote_file = connector.find_file_by_path(remote_file_path)
                
                if remote_file:
                    # 獲取本地修改時間
                    local_modified = os.path.getmtime(local_file_path)
                    
                    try:
                        # 解析雲端修改時間
                        from datetime import datetime
                        cloud_modified = remote_file.get('modifiedTime')
                        cloud_dt = datetime.strptime(cloud_modified.replace('Z', '+00:00'), "%Y-%m-%dT%H:%M:%S.%f%z")
                        cloud_timestamp = cloud_dt.timestamp()
                        
                        if cloud_timestamp > local_modified:
                            print("  雲端文件較新，將下載到本地...")
                            connector.download_file(remote_file['id'], local_file_path)
                        else:
                            print("  本地文件較新，將上傳到雲端...")
                            connector.upload_file(local_file_path, cloud_path, filename)
                    except Exception as e:
                        print(f"  處理修改時間時出錯: {str(e)}")
                        print("  默認上傳本地文件...")
                        connector.upload_file(local_file_path, cloud_path, filename)
                else:
                    print("  雲端不存在此文件，將上傳...")
                    connector.upload_file(local_file_path, cloud_path, filename)
    
    print("\n===== 同步完成 =====")
    return True

def toggle_mode():
    """切換雲端/本地模式"""
    config = CloudConfigManager()
    current_mode = "雲端模式" if config.is_cloud_mode() else "本地模式"
    
    print(f"當前模式: {current_mode}")
    
    if config.is_cloud_mode():
        user_input = input("是否切換到本地模式？(y/n): ").strip().lower()
        if user_input == 'y':
            config.toggle_cloud_mode(False)
            print("已切換到本地模式")
            return True
        else:
            print("保持雲端模式")
            return False
    else:
        user_input = input("是否切換到雲端模式？(y/n): ").strip().lower()
        if user_input == 'y':
            # 嘗試連接雲端
            connector = GoogleDriveConnector(
                credentials_path=config.get("credentials_path"),
                token_path=config.get("token_path")
            )
            
            if connector.authenticate():
                config.toggle_cloud_mode(True)
                print("已切換到雲端模式")
                
                # 詢問是否同步資料
                user_input = input("是否立即同步資料？(y/n): ").strip().lower()
                if user_input == 'y':
                    sync_data()
                
                return True
            else:
                print("雲端連接失敗！無法切換到雲端模式")
                return False
        else:
            print("保持本地模式")
            return False

def resolve_conflicts():
    """解決數據衝突"""
    config = CloudConfigManager()
    
    if not config.is_cloud_mode():
        print("當前處於本地模式，無法解決衝突")
        return False
    
    # 讀取衝突策略
    current_strategy = config.get("conflict_resolution_strategy", "cloud_wins")
    print(f"當前衝突解決策略: {current_strategy}")
    
    print("\n可用的衝突解決策略:")
    print("1. cloud_wins - 雲端優先，下載雲端文件覆蓋本地")
    print("2. local_wins - 本地優先，上傳本地文件覆蓋雲端")
    print("3. rename_local - 保留本地文件的備份，然後下載雲端文件")
    
    while True:
        user_input = input("\n請選擇衝突解決策略 (1/2/3)，或按 Enter 保持當前策略: ").strip()
        
        if not user_input:
            break
        
        if user_input == '1':
            config.set("conflict_resolution_strategy", "cloud_wins")
            config.save_config()
            print("已設置衝突解決策略為: cloud_wins")
            break
        elif user_input == '2':
            config.set("conflict_resolution_strategy", "local_wins")
            config.save_config()
            print("已設置衝突解決策略為: local_wins")
            break
        elif user_input == '3':
            config.set("conflict_resolution_strategy", "rename_local")
            config.save_config()
            print("已設置衝突解決策略為: rename_local")
            break
        else:
            print("無效的選項，請重新輸入")
    
    # 強制同步所有文件，應用新的衝突解決策略
    user_input = input("\n是否立即進行全面同步來解決所有衝突？(y/n): ").strip().lower()
    if user_input == 'y':
        return sync_data()
    
    return True

def show_help():
    """顯示幫助信息"""
    print(__doc__)

def main():
    parser = argparse.ArgumentParser(description="Google Drive 雲端整合設置工具")
    parser.add_argument('command', nargs='?', default='help',
                        choices=['setup', 'test', 'sync', 'mode', 'resolve', 'help'],
                        help="要執行的命令")
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_credentials()
    elif args.command == 'test':
        test_connection()
    elif args.command == 'sync':
        sync_data()
    elif args.command == 'mode':
        toggle_mode()
    elif args.command == 'resolve':
        resolve_conflicts()
    elif args.command == 'help':
        show_help()
    else:
        print(f"未知命令: {args.command}")
        show_help()

if __name__ == '__main__':
    main()
