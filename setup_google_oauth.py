#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import getpass
import re
import webbrowser
import json
import time
from pathlib import Path

# 彩色輸出函數
def print_color(text, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['end']}")

# 顯示歡迎訊息和說明
def show_welcome():
    print_color("\n=== Google OAuth 2.0 設置嚮導 ===", "blue")
    print_color("這個腳本將引導您完成為加油站POS系統設置Google OAuth的過程。", "cyan")
    print_color("您將需要訪問Google Cloud Console並執行幾個簡單的步驟。\n", "cyan")
    
    print_color("設置分為以下步驟：", "yellow")
    print_color("1. 建立Google Cloud項目")
    print_color("2. 設置OAuth同意屏幕")
    print_color("3. 建立OAuth客戶端ID")
    print_color("4. 配置應用程式\n")
    
    input(print_color("按 Enter 開始...", "green"))

# 第一步：建立Google Cloud項目
def step1_create_project():
    print_color("\n--- 步驟 1: 建立Google Cloud項目 ---", "blue")
    
    print("1. 訪問 Google Cloud Console (將在瀏覽器中自動打開)")
    print("2. 如果需要，請登錄您的Google帳號")
    print("3. 點擊頁面頂部的項目下拉選單，然後點擊「新建項目」")
    print("4. 輸入項目名稱（例如「加油站POS系統」），並點擊「建立」")
    print("5. 等待項目創建完成，確保已選擇該項目")
    
    proceed = input("\n要在瀏覽器中打開Google Cloud Console嗎？(y/n): ")
    if proceed.lower() == 'y':
        webbrowser.open("https://console.cloud.google.com/")
        
    project_name = input("\n輸入您剛創建的項目名稱 (僅作記錄用途): ")
    
    print_color("\n✓ 完成步驟 1：已建立Google Cloud項目", "green")
    input("按 Enter 繼續下一步...")
    return project_name

# 第二步：設置OAuth同意屏幕
def step2_oauth_consent():
    print_color("\n--- 步驟 2: 設置OAuth同意屏幕 ---", "blue")
    
    print("1. 在Google Cloud Console左側菜單中，選擇「API和服務」>「OAuth 同意屏幕」")
    print("2. 選擇用戶類型（推薦：外部），然後點擊「建立」")
    print("3. 填寫應用程式資訊:")
    print("   - 應用名稱: 加油站POS系統")
    print("   - 用戶支持電子郵件: [您的郵箱]")
    print("   - 開發者聯絡資訊: [您的郵箱]")
    print("4. 點擊「儲存並繼續」")
    print("5. 在「範圍」頁面，點擊「添加或刪除範圍」，選擇:")
    print("   - .../auth/userinfo.email")
    print("   - .../auth/userinfo.profile")
    print("   - openid")
    print("6. 點擊「更新」並「儲存並繼續」")
    print("7. 添加測試用戶（您的Gmail地址），然後點擊「儲存並繼續」")
    print("8. 檢查摘要，然後點擊「回到儀表板」")
    
    proceed = input("\n要在瀏覽器中打開OAuth同意屏幕設置頁面嗎？(y/n): ")
    if proceed.lower() == 'y':
        webbrowser.open("https://console.cloud.google.com/apis/credentials/consent")
    
    input("\n完成OAuth同意屏幕設置後，按 Enter 繼續...")
    print_color("\n✓ 完成步驟 2：已設置OAuth同意屏幕", "green")
    return True

# 第三步：建立OAuth客戶端ID
def step3_client_credentials():
    print_color("\n--- 步驟 3: 建立OAuth客戶端ID ---", "blue")
    
    print("1. 在Google Cloud Console左側菜單中，選擇「API和服務」>「憑證」")
    print("2. 點擊頂部的「+ 建立憑證」按鈕，然後選擇「OAuth客戶端ID」")
    print("3. 在「應用程式類型」下拉選單中，選擇「Web 應用程式」")
    print("4. 在「名稱」欄位中，輸入「加油站POS系統」")
    print("5. 在「授權的重定向URI」部分，點擊「+ 添加URI」，添加以下URI:")
    print("   - http://localhost:8080/auth/google/callback")
    print("   - http://127.0.0.1:8080/auth/google/callback")
    print("   - http://localhost:8080/login/google/callback")
    print("   - http://127.0.0.1:8080/login/google/callback")
    print("6. 如果您的應用將在其他域名或IP上運行，也需要添加相應的回調URL")
    print("7. 點擊「建立」")
    print("8. 創建完成後，系統會顯示您的客戶端ID和客戶端密鑰，請記下這些值")
    
    proceed = input("\n要在瀏覽器中打開憑證頁面嗎？(y/n): ")
    if proceed.lower() == 'y':
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
    
    # 獲取客戶端ID和密鑰
    print_color("\n請輸入從Google獲取的客戶端ID和密鑰", "yellow")
    client_id = input("客戶端ID: ")
    client_secret = input("客戶端密鑰: ")
    
    while not client_id or not client_secret:
        print_color("錯誤：客戶端ID和密鑰不能為空", "red")
        client_id = input("客戶端ID: ")
        client_secret = input("客戶端密鑰: ")
    
    print_color("\n✓ 完成步驟 3：已獲取OAuth客戶端憑證", "green")
    return client_id, client_secret

# 第四步：配置應用程式
def step4_configure_app(client_id, client_secret):
    print_color("\n--- 步驟 4: 配置應用程式 ---", "blue")
    
    # 獲取授權電子郵件地址
    print_color("請輸入允許訪問系統的Google郵箱地址 (可以添加多個，每行一個，輸入空行完成):", "yellow")
    emails = []
    while True:
        email = input("電子郵件地址 (或按 Enter 完成): ")
        if not email:
            break
        # 簡單的電子郵件格式驗證
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            emails.append(email)
        else:
            print_color("無效的電子郵件格式，請重試", "red")
    
    # 確保至少有一個電子郵件
    if not emails:
        default_email = input("您沒有輸入任何電子郵件。是否使用您自己的Google郵箱？ (y/n): ")
        if default_email.lower() == 'y':
            email = input("請輸入您的Google郵箱: ")
            while not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                print_color("無效的電子郵件格式，請重試", "red")
                email = input("請輸入您的Google郵箱: ")
            emails.append(email)
    
    # 更新 set_env.sh
    update_set_env_sh(client_id, client_secret)
    
    # 更新 config.py
    update_config_py(emails)
    
    print_color("\n✓ 完成步驟 4：應用程式配置已更新", "green")
    return True

# 更新 set_env.sh 檔案
def update_set_env_sh(client_id, client_secret):
    try:
        with open('set_env.sh', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 替換客戶端ID和密鑰
        content = re.sub(
            r"export GOOGLE_CLIENT_ID='.*?'", 
            f"export GOOGLE_CLIENT_ID='{client_id}'", 
            content
        )
        content = re.sub(
            r"export GOOGLE_CLIENT_SECRET='.*?'", 
            f"export GOOGLE_CLIENT_SECRET='{client_secret}'", 
            content
        )
        
        with open('set_env.sh', 'w', encoding='utf-8') as file:
            file.write(content)
        
        # 確保檔案可執行
        os.chmod('set_env.sh', 0o755)
        
        print_color("已更新 set_env.sh 並設置執行權限", "green")
    except Exception as e:
        print_color(f"更新 set_env.sh 時出錯: {str(e)}", "red")
        return False
    
    return True

# 更新 config.py 檔案
def update_config_py(emails):
    try:
        with open('config.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 構建授權郵箱列表
        email_list = "\n        ".join([f"'{email}'," for email in emails])
        
        # 替換授權郵箱
        pattern = r"AUTHORIZED_EMAILS = \[(.*?)\]"
        replacement = f"AUTHORIZED_EMAILS = [\n        # 在此處添加允許登入的Google郵箱地址\n        {email_list}\n    ]"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open('config.py', 'w', encoding='utf-8') as file:
            file.write(content)
        
        print_color("已更新 config.py 中的授權郵箱", "green")
    except Exception as e:
        print_color(f"更新 config.py 時出錯: {str(e)}", "red")
        return False
    
    return True

# 完成設置並提供下一步說明
def finish_setup():
    print_color("\n=== Google OAuth 設置完成！===", "green")
    print_color("\n要運行應用程式，請執行以下命令：", "yellow")
    print_color("  source ./set_env.sh")
    print_color("  python run.py")
    
    print_color("\n應用程式將在 http://127.0.0.1:8080 上運行", "cyan")
    print_color("您可以使用已授權的Google帳號登入系統", "cyan")
    
    # 詢問是否要啟動應用
    start_app = input("\n是否現在啟動應用程式？(y/n): ")
    if start_app.lower() == 'y':
        try:
            os.system("source ./set_env.sh && python run.py")
        except Exception as e:
            print_color(f"啟動應用程式時出錯: {str(e)}", "red")
            print_color("請手動執行上述命令", "yellow")
    
    return True

# 主函數
def main():
    try:
        # 檢查必要檔案
        required_files = ['config.py', 'set_env.sh', 'app.py', 'run.py']
        for file in required_files:
            if not os.path.exists(file):
                print_color(f"錯誤：找不到必要檔案 {file}", "red")
                return False
        
        show_welcome()
        project_name = step1_create_project()
        step2_oauth_consent()
        client_id, client_secret = step3_client_credentials()
        step4_configure_app(client_id, client_secret)
        finish_setup()
        
        print_color("\n設置嚮導完成。祝您使用愉快！", "green")
        
    except KeyboardInterrupt:
        print_color("\n\n設置已取消。您可以隨時重新運行此腳本。", "yellow")
    except Exception as e:
        print_color(f"\n發生錯誤: {str(e)}", "red")
        print_color("設置未完成。請修復錯誤後重試。", "red")

if __name__ == "__main__":
    main() 