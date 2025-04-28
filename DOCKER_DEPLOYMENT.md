# Docker 部署指南

本文檔提供使用 Docker 部署加油站 POS 系統的詳細說明。

## 前置需求

- 安裝 [Docker](https://docs.docker.com/get-docker/)
- 安裝 [Docker Compose](https://docs.docker.com/compose/install/)

## 部署步驟

### 1. 配置系統

在部署前，您需要先創建 `config.json` 配置文件：

```bash
# 複製配置範例
cp config.json.example config.json

# 編輯配置文件
nano config.json
```

填入您的 Google OAuth 憑證和其他必要配置。

### 2. 使用 Docker Compose 部署

```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

應用將在 http://localhost:8080 上運行。

### 3. 停止服務

```bash
docker-compose down
```

## 數據持久化

以下目錄會被映射到主機以保存數據：

- `./data`：存儲數據庫和其他系統數據
- `./logs`：存儲系統日誌
- `./reports`：存儲系統生成的報表
- `./config.json`：配置文件

## 更新應用

當有新版本時，您可以按照以下步驟更新：

```bash
# 拉取最新代碼
git pull

# 重新構建並啟動容器
docker-compose up -d --build
```

## 故障排除

### 連接問題

如果無法連接到應用，請檢查：

1. 確認容器是否運行：`docker-compose ps`
2. 檢查容器日誌：`docker-compose logs gas_station_pos`

### 數據庫問題

如果遇到數據庫問題：

1. 確保 `data` 目錄有正確的權限
2. 檢查 `config.json` 中的數據庫路徑設置

### Google OAuth 問題

如果 Google 登錄失敗：

1. 確認 `config.json` 中的 OAuth 配置正確
2. 檢查 Google 開發者控制台中的重定向 URI 設置

## 安全考量

- 請確保 `config.json` 有適當的權限，只允許需要訪問的用戶讀取
- 考慮使用 Docker 密碼或環境變量管理敏感信息
- 定期備份 `data` 目錄中的數據

## 生產環境建議

在生產環境中部署時，建議：

1. 使用反向代理（如 Nginx）處理 HTTPS
2. 設置適當的防火牆規則
3. 實施定期備份策略
4. 監控系統運行狀態 