#!/bin/bash

PORT=8080

echo "嘗試終止所有使用 $PORT 端口的進程..."

# 使用lsof找出所有使用該端口的進程
PIDs=$(lsof -ti:$PORT)

if [ -z "$PIDs" ]; then
  echo "沒有發現使用 $PORT 端口的進程。"
  exit 0
fi

# 逐個終止進程
for PID in $PIDs; do
  echo "終止進程 PID: $PID"
  kill -9 $PID 2>/dev/null
done

# 檢查是否成功終止
sleep 1
PIDs_after=$(lsof -ti:$PORT)

if [ -z "$PIDs_after" ]; then
  echo "成功終止所有使用 $PORT 端口的進程。"
else
  echo "警告: 仍有進程使用 $PORT 端口，可能需要手動終止。"
  echo "剩餘進程: $PIDs_after"
fi
