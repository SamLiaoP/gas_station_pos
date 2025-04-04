#!/bin/bash

# 獲取未被使用的端口（從8081開始查找）
PORT=8081
while [ $(lsof -ti:$PORT | wc -l) -gt 0 ]; do
  PORT=$((PORT+1))
done

echo "找到可用端口: $PORT"

# 修改run.py文件，替換端口號
sed -i '' "s/port=8080/port=$PORT/g" run.py

echo "已將端口從8080更改為$PORT"
echo "請使用以下命令啟動系統："
echo "python run.py"
