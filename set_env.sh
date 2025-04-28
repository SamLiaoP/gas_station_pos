#!/bin/bash

# 檢查.env文件是否存在
if [ -f .env ]; then
    echo "從.env文件中加載環境變量..."
    
    # 讀取.env文件並導出環境變量
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # 忽略空行和注釋
        if [ -n "$key" ] && [[ ! $key =~ ^# ]]; then
            # 移除可能的引號
            value=$(echo $value | sed -e "s/^['\"]//g" -e "s/['\"]$//g")
            # 導出變量
            export "$key=$value"
            echo "已設置: $key"
        fi
    done < .env
    
    echo "環境變量已成功加載"
else
    echo "錯誤：.env文件未找到"
    echo "請創建.env文件並填入以下環境變量："
    echo "GOOGLE_CLIENT_ID=<您的Google客戶端ID>"
    echo "GOOGLE_CLIENT_SECRET=<您的Google客戶端密鑰>"
    echo "SECRET_KEY=<用於Flask應用的密鑰>"
    exit 1
fi

# 啟動應用
echo "啟動應用..."
cd "$(dirname "$0")"
python run.py 