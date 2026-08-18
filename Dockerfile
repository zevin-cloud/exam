# ==========================================
# 阶段 1：编译前端 Vue3 静态资源
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

# ==========================================
# 阶段 2：FastAPI 一体化生产镜像 (包含前端静态)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    FRONTEND_DIST_DIR=/app/frontend_dist

# 安装基础系统工具与时区
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 生产依赖
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端核心代码
COPY backend/app /app/app

# 从阶段 1 拷贝打包好的前端静态资源 (直接挂载给 FastAPI)
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# 创建持久化上传目录
RUN mkdir -p /app/uploads

EXPOSE 8000

# 生产级多 Worker 高并发启动 (默认 4 个 Worker)
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
