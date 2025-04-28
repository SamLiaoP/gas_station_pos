#!/bin/bash

# 設置顏色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # 無顏色

# 標題
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   加油站POS系統 - 配置設置輔助工具    ${NC}"
echo -e "${BLUE}========================================${NC}"

# 檢查 config.json 文件是否已存在
if [ -f config.json ]; then
    echo -e "${YELLOW}警告：config.json 文件已存在${NC}"
    read -p "是否要覆蓋現有的 config.json 文件？(y/n): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}操作已取消，保留現有的 config.json 文件。${NC}"
        exit 0
    fi
fi

# 生成隨機密鑰
echo -e "${CYAN}生成隨機密鑰...${NC}"
random_key=$(openssl rand -hex 16)

# 輸入 Google Client ID
echo -e "${CYAN}請輸入您的 Google Client ID:${NC}"
read client_id

# 輸入 Google Client Secret
echo -e "${CYAN}請輸入您的 Google Client Secret:${NC}"
read client_secret

# 輸入授權電子郵件
echo -e "${CYAN}請輸入允許登入的電子郵件地址 (多個地址用空格分隔):${NC}"
read emails

# 創建郵件地址數組
emails_array="["
for email in $emails; do
    if [ -n "$email" ]; then
        if [ "$emails_array" != "[" ]; then
            emails_array="$emails_array, \"$email\""
        else
            emails_array="$emails_array\"$email\""
        fi
    fi
done
emails_array="$emails_array, \"ba88052@gmail.com\"]"

# 輸入資料庫路徑 (可選)
echo -e "${CYAN}請輸入資料庫路徑 (按 Enter 使用預設路徑 data/gas_station.db):${NC}"
read db_path
if [ -z "$db_path" ]; then
    db_path="data/gas_station.db"
fi

# 創建 config.json 檔案
cat > config.json << EOF
{
    "app": {
        "SECRET_KEY": "$random_key"
    },
    "google_oauth": {
        "GOOGLE_CLIENT_ID": "$client_id",
        "GOOGLE_CLIENT_SECRET": "$client_secret",
        "GOOGLE_DISCOVERY_URL": "https://accounts.google.com/.well-known/openid-configuration"
    },
    "auth": {
        "AUTHORIZED_EMAILS": $emails_array
    },
    "database": {
        "DB_PATH": "$db_path"
    },
    "testing": {
        "TESTING": "False"
    }
}
EOF

echo -e "${GREEN}配置設置完成!${NC}"
echo -e "${YELLOW}重要：config.json 文件包含敏感信息，請勿提交到公共代碼庫!${NC}"
echo -e "${CYAN}使用以下命令啟動應用程式:${NC}"
echo -e "  python run.py"

chmod +x setup_config.sh
echo -e "${GREEN}已設置 setup_config.sh 的執行權限${NC}" 