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
echo -e "${BLUE}   加油站POS系統 - 環境設置輔助工具    ${NC}"
echo -e "${BLUE}========================================${NC}"

# 檢查 env.example 是否存在
if [ ! -f env.example ]; then
    echo -e "${RED}錯誤: env.example 文件不存在${NC}"
    exit 1
fi

# 檢查 .env 文件是否已存在
if [ -f .env ]; then
    echo -e "${YELLOW}警告：.env 文件已存在${NC}"
    read -p "是否要覆蓋現有的 .env 文件？(y/n): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}操作已取消，保留現有的 .env 文件。${NC}"
        exit 0
    fi
fi

# 複製 env.example 到 .env
echo -e "${CYAN}從 env.example 創建 .env 文件...${NC}"
cp env.example .env

# 生成隨機密鑰
echo -e "${CYAN}生成隨機密鑰...${NC}"
random_key=$(openssl rand -hex 16)
sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$random_key/" .env

# 輸入 Google Client ID
echo -e "${CYAN}請輸入您的 Google Client ID:${NC}"
read client_id
sed -i '' "s/GOOGLE_CLIENT_ID=.*/GOOGLE_CLIENT_ID=$client_id/" .env

# 輸入 Google Client Secret
echo -e "${CYAN}請輸入您的 Google Client Secret:${NC}"
read client_secret
sed -i '' "s/GOOGLE_CLIENT_SECRET=.*/GOOGLE_CLIENT_SECRET=$client_secret/" .env

# 輸入授權電子郵件
echo -e "${CYAN}請輸入允許登入的電子郵件地址 (多個地址用逗號分隔):${NC}"
read emails
if [ -n "$emails" ]; then
    sed -i '' "s/AUTHORIZED_EMAILS=.*/AUTHORIZED_EMAILS=$emails/" .env
fi

echo -e "${GREEN}環境變數設置完成!${NC}"
echo -e "${YELLOW}重要：.env 文件包含敏感信息，請勿提交到公共代碼庫!${NC}"
echo -e "${CYAN}使用以下命令啟動應用程式:${NC}"
echo -e "  source ./set_env.sh"
echo -e "  python run.py"

# 設置權限
chmod +x set_env.sh
echo -e "${GREEN}已設置 set_env.sh 的執行權限${NC}" 