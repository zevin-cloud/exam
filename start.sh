#!/bin/bash
set -e

# 清理旧进程
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true
sleep 1

# 启动后端
cd /root/code/exam/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /root/code/exam/backend.log 2>&1 &
echo "[Backend] Started on http://0.0.0.0:8000 (PID: $!)"

# 启动前端
cd /root/code/exam/frontend
nohup npm run dev -- --host 0.0.0.0 --port 5173 > /root/code/exam/frontend.log 2>&1 &
echo "[Frontend] Started on http://0.0.0.0:5173 (PID: $!)"

sleep 3
echo "=== Service Status ==="
ps aux | grep -E "uvicorn|vite" | grep -v grep
