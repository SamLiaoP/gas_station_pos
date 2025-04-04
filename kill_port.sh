#!/bin/bash

# 獲取使用8080端口的進程ID
PID=$(lsof -ti:8080)

if [ -z "$PID" ]; then
  echo "沒有發現使用8080端口的進程。"
else
  echo "發現使用8080端口的進程，PID: $PID，正在終止..."
  kill -9 $PID
  echo "進程已終止。"
fi
