#!/usr/bin/env python
"""
本地模式轉換為雲端模式工具

這個腳本將幫助您設置 Google Drive API 憑證並將本地數據同步到雲端。
運行此腳本後，系統將自動切換到雲端模式。
"""

import os
import sys
import time
import webbrowser
import shutil
from utils.common import DATA_PATH, REPORTS_PATH, logger, ensure_directories
from utils.cloud.cloud_config_manager import CloudConfigManager
from utils.cloud.google_drive_connector import GoogleDriveConnector
from utils.cloud.excel_manager import CloudExcelManager
from models.data_manager import ensure_master_data, ensure_inventory_data, ensure_transactions_data

def main():
    print("===== 本地模式轉換為雲端模式工具 =====")
    
    # 確保本地目錄和數據文件存在
    ensure_directories()
    ensure_master_data()
    ensure_inventory_data()
    ensure_transactions_data()
    
    # 初始化雲端配置管理器
    config = CloudConfigManager()
    
    # 檢查是否已經處於雲端模式
    if config.is_cloud_mode():
        print("系統已經處於雲端模式。")
        user_input = input("是否繼續進行雲端設置和同步？(y/n): ").strip().lower()
        if user_input != 'y':
            print("操作已取消。")
            return
    
    # 設置 Google Drive API 憑證
    credentials_path = config.get("credentials_path")
    token_path = config.get("token_path")
    
    print("\n===== 步驟 1: 設置 Google Drive API 憑證 =====")
    print("請按照以下步驟操作：")
    print("1. 前往 Google Cloud Console 創建專案")
    print("2. 啟用 Google Drive API")
    print("3. 創建 OAuth 2.0 憑證")
    print("4. 下載憑證 JSON 文件")
    print("5. 將下載的憑證文件保存到以下路徑：")
    print(f"   {os.path.abspath(credentials_path)}")
    
    print("\n是否打開 Google Cloud Console？")
    user_input = input("(y/n): ").strip().lower()
    if user_input == 'y':
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
    
    print("\n請確保您已完成上述步驟並準備好憑證文件")
    user_input = input("按 Enter 繼續...")
    
    # 檢查憑證文件是否存在
    if not os.path.exists(credentials_path):
        print(f"\n錯誤: 找不到憑證文件 {credentials_path}")
        print("請確保您已將憑證文件保存到正確位置後再重試")
        return
    
    print("\n===== 步驟 2: 測試 Google Drive 連接 =====")
    print("正在測試 Google Drive 連接...")
    
    # 初始化 Google Drive 連接器
    connector = GoogleDriveConnector(
        credentials_path=credentials_path,
        token_path=token_path
    )
    
    # 嘗試認證
    if not connector.authenticate():
        print("錯誤: Google Drive 認證失敗")
        print("請檢查憑證文件和網絡連接後再重試")
        return
    
    print("Google Drive 連接成功！")
    
    # 啟用雲端模式
    config.toggle_cloud_mode(True)
    print("已啟用雲端模式")
    
    print("\n===== 步驟 3: 建立雲端目錄結構 =====")
    
    # 確保雲端目錄結構存在
    root_folder_name = config.get("root_folder_name")
    data_folder_name = config.get("data_folder_name")
    reports_folder_name = config.get("reports_folder_name")
    
    print(f"正在創建根目錄: {root_folder_name}")
    if connector._ensure_root_folder():
        print(f"根目錄 {root_folder_name} 已創建/存在")
    else:
        print(f"創建根目錄 {root_folder_name} 失敗")
        return
    
    print(f"正在創建數據目錄: {data_folder_name}")
    data_folder_id = connector.ensure_directory(data_folder_name)
    if data_folder_id:
        print(f"數據目錄 {data_folder_name} 已創建/存在")
    else:
        print(f"創建數據目錄 {data_folder_name} 失敗")
        return
    
    print(f"正在創建報表目錄: {reports_folder_name}")
    reports_folder_id = connector.ensure_directory(reports_folder_name)
    if reports_folder_id:
        print(f"報表目錄 {reports_folder_name} 已創建/存在")
    else:
        print(f"創建報表目錄 {reports_folder_name} 失敗")
        return
    
    print("\n===== 步驟 4: 同步本地數據到雲端 =====")
    
    # 同步主要數據文件
    data_files = ["master_data.xlsx", "inventory.xlsx", "transactions.xlsx"]
    
    for filename in data_files:
        local_path = os.path.join(DATA_PATH, filename)
        
        if os.path.exists(local_path):
            print(f"正在上傳 {filename}...")
            file_id = connector.upload_file(local_path, data_folder_name, filename)
            
            if file_id:
                print(f"成功上傳 {filename}")
            else:
                print(f"上傳 {filename} 失敗")
        else:
            print(f"本地不存在 {filename}，跳過")
    
    # 同步報表文件
    if os.path.exists(REPORTS_PATH):
        for root, dirs, files in os.walk(REPORTS_PATH):
            # 獲取相對路徑
            rel_path = os.path.relpath(root, REPORTS_PATH)
            if rel_path == '.':
                rel_path = ''
            
            # 構建雲端路徑
            cloud_path = f"{reports_folder_name}/{rel_path}" if rel_path else reports_folder_name
            
            # 確保雲端目錄存在
            if rel_path:
                print(f"正在創建報表子目錄: {cloud_path}")
                connector.ensure_directory(cloud_path)
            
            # 同步文件
            for filename in files:
                local_file_path = os.path.join(root, filename)
                
                print(f"正在上傳報表: {rel_path}/{filename}")
                file_id = connector.upload_file(local_file_path, cloud_path, filename)
                
                if file_id:
                    print(f"成功上傳報表: {rel_path}/{filename}")
                else:
                    print(f"上傳報表失敗: {rel_path}/{filename}")
    
    print("\n===== 轉換完成 =====")
    print("系統現在已經完全轉換為雲端模式，所有數據將自動與 Google Drive 同步。")
    print("您可以通過運行 'python cloud_setup.py mode' 來隨時切換回本地模式。")

if __name__ == '__main__':
    main()
