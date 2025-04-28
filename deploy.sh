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
echo -e "${BLUE}   加油站POS系統 - Docker 部署工具    ${NC}"
echo -e "${BLUE}========================================${NC}"

# 檢查 Docker 是否已安裝
if ! command -v docker &> /dev/null; then
    echo -e "${RED}錯誤: Docker 未安裝${NC}"
    echo -e "請前往 https://docs.docker.com/get-docker/ 安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose 是否已安裝
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}錯誤: Docker Compose 未安裝${NC}"
    echo -e "請前往 https://docs.docker.com/compose/install/ 安裝 Docker Compose"
    exit 1
fi

# 檢查 config.json 文件是否存在
if [ ! -f config.json ]; then
    echo -e "${YELLOW}警告: config.json 文件未找到${NC}"
    echo -e "是否要從範例創建配置文件? (y/n): "
    read create_config
    
    if [[ $create_config =~ ^[Yy]$ ]]; then
        cp config.json.example config.json
        echo -e "${YELLOW}已創建 config.json 文件，請編輯其中的設定項再繼續。${NC}"
        echo -e "是否要現在編輯配置文件? (y/n): "
        read edit_config
        
        if [[ $edit_config =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} config.json
        else
            echo -e "${YELLOW}請稍後手動編輯 config.json 文件。${NC}"
            exit 0
        fi
    else
        echo -e "${RED}部署已取消。請先創建 config.json 文件。${NC}"
        exit 1
    fi
fi

# 創建必要的目錄
echo -e "${CYAN}創建必要的目錄...${NC}"
mkdir -p data logs reports

# 設置目錄權限
echo -e "${CYAN}設置目錄權限...${NC}"
chmod 755 data logs reports
chmod 600 config.json

# 構建並啟動容器
echo -e "${CYAN}構建並啟動容器...${NC}"
docker-compose up -d --build

# 檢查容器狀態
echo -e "${CYAN}檢查容器狀態...${NC}"
docker-compose ps

echo -e "${GREEN}部署完成！應用程式現在應該在 http://localhost:8080 運行。${NC}"
echo -e "${CYAN}使用以下命令查看容器日誌:${NC}"
echo -e "  docker-compose logs -f"
echo -e "${CYAN}使用以下命令停止服務:${NC}"
echo -e "  docker-compose down"

# 設置執行權限
chmod +x deploy.sh 