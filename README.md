# 🎓 企业在线考务与培训考核系统 (Enterprise Exam System)

基于 **FastAPI + Vue 3 + MySQL / SQLite** 构建的现代化轻量级企业在线考务与培训考核平台，内置 **OneAuth 统一身份源对接**、**可视化试卷编辑器**、**防作弊答题监考**与**自动化/人工阅卷流水线**。

---

## 🌟 系统核心特性

- **统一身份认证 (OneAuth SSO)**：一键同步企业部门架构树与员工成员，支持 OAuth2 授权码免密登录。
- **可视化试卷设计**：三栏可视化编辑器，支持单选、多选、判断、填空、简答等 5 大主流题型与分值实时统计。
- **考务排期与权限管控**：按全员 / 部门 / 指定人员多维授权，支持自定义开考时间窗口或永久有效。
- **防作弊考场机制**：支持切屏次数实时监测与超限强制交卷，支持公开/保密两种考后查卷模式。
- **极简一体化容器化交付**：采用 **FastAPI 一体化 + MySQL 8.0 双容器架构**，免装 Nginx 与 Node.js，单端口（默认 `8000`）搞定全套前后台。

---

## 🛠️ 环境准备

在目标机器上部署，**仅需满足以下基础环境之一**：

- **推荐方式（Docker 部署）**：
  - Docker 20.10+
  - Docker Compose 2.0+（支持 `docker compose` 命令）
- **本地直接运行方式（开发/无 Docker 机器）**：
  - Python 3.10+
  - Node.js 18+（及 npm）

---

## 🚀 方式一：Docker 一键生产部署（推荐）

通过 Docker 容器化部署，宿主机**无需安装任何 Python / Node.js 依赖**，全自动编译前端并初始化数据库。

### 1. 克隆项目
```bash
git clone <项目仓库地址> /root/code/exam
cd /root/code/exam
```

### 2. 配置环境变量
复制并检查 `.env` 文件：
```bash
cp .env.example .env
```
> 💡 若需修改外部访问端口、OneAuth 对接地址或数据库密码，可直接编辑 `.env`：
> - `PORT=8000`：对外访问端口（可改为 `80` 或任意可用端口）；
> - `ONEAUTH_SERVER_URL`：OneAuth 统一认证后台地址（默认 `http://<IP>:5174`）；
> - `ONEAUTH_REDIRECT_URI`：SSO 登录跳回地址（格式：`http://<当前机器IP或域名>:8000/auth/callback`）。

### 3. 一键构建并启动
```bash
bash deploy.sh start
```
脚本将自动完成：
1. 容器内多阶段编译打包前端 Vue 3 代码；
2. 启动并初始化 MySQL 8.0 数据库服务；
3. 启动 FastAPI 多进程应用并自动建表与插入演示种子数据。

### 4. 访问系统
- **考务系统前台/管理后台（单端口一体化）**：`http://<服务器IP>:8000`
- **Swagger API 接口文档**：`http://<服务器IP>:8000/docs`

> 🔑 **系统内置初始超级管理员账号**：
> - **用户名**：`admin`
> - **默认密码**：`admin123`

---

## 💻 方式二：本地直接运行（开发与调试）

如果您在开发环境或不需要 Docker 的机器上运行：

### 1. 启动后端
```bash
cd /root/code/exam/backend
pip install -r requirements.txt
# 启动 FastAPI 后端 (开发模式使用 SQLite 数据库，开箱即用)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动前端
```bash
cd /root/code/exam/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

或直接在根目录执行一键启动脚本：
```bash
bash /root/code/exam/start.sh
```

---

## 📋 常用运维管理命令 (Docker 模式)

在项目根目录下使用 `deploy.sh` 脚本进行日常运维：

| 操作需求 | 执行命令 | 说明 |
| :--- | :--- | :--- |
| **启动 / 构建更新** | `bash deploy.sh start` | 自动构建镜像并在后台守护运行 |
| **停止服务** | `bash deploy.sh stop` | 优雅停止并清理容器 |
| **重启系统** | `bash deploy.sh restart` | 快速重启所有服务 |
| **查看运行日志** | `bash deploy.sh logs` | 实时查看 FastAPI 业务与访问日志 |
| **查看全部日志** | `bash deploy.sh logs-all` | 同时查看 MySQL 与后端日志 |
| **一键备份数据库** | `bash deploy.sh backup` | 自动导出 SQL 备份至 `backups/` 目录 |

---

## ⚙️ 配置文件说明 (`.env`)

| 配置项 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `PORT` | `8000` | 对外开放的 HTTP 访问端口 |
| `MYSQL_PORT` | `3306` | MySQL 对外端口（可用于外部数据库客户端连接） |
| `MYSQL_ROOT_PASSWORD` | `root123456` | MySQL root 密码 |
| `MYSQL_DATABASE` | `exam_db` | 考务系统数据库名称 |
| `MYSQL_USER` | `exam_user` | 业务数据库用户名 |
| `MYSQL_PASSWORD` | `exam_pass123` | 业务数据库密码 |
| `SECRET_KEY` | *(随机字符串)* | JWT Token 鉴权加密密钥 |
| `ONEAUTH_SERVER_URL` | `http://...:5174` | OneAuth 统一身份源服务器地址 |
| `ONEAUTH_CLIENT_ID` | `app_...` | OneAuth 应用 Client ID |
| `ONEAUTH_CLIENT_SECRET` | `...` | OneAuth 应用 Client Secret |
| `ONEAUTH_REDIRECT_URI` | `http://...:8000/auth/callback` | OAuth2 授权回调地址 |

---

## 📁 目录结构

```text
exam/
├── backend/                  # FastAPI 后端源码
│   ├── app/
│   │   ├── api/v1/          # 业务接口 (用户/题库/试卷/考务/阅卷)
│   │   ├── core/            # 核心配置、数据库引擎与安全加密
│   │   ├── models/          # SQLAlchemy 数据模型定义
│   │   └── services/        # 核心业务逻辑 (OneAuth 对接、自动批改)
│   ├── requirements.txt     # Python 依赖清单
│   └── uploads/             # 上传的试题附件/图片存储目录
├── frontend/                 # Vue 3 前端源码
│   ├── src/
│   │   ├── api/             # 请求封装与接口列表
│   │   ├── views/           # 页面 (登录/考务/试卷编辑/答题/组织管理)
│   │   └── router/          # 路由守卫与导航定义
│   ├── package.json         # 前端依赖配置
│   └── vite.config.js       # Vite 打包配置
├── Dockerfile                # 多阶段构建生产镜像 Dockerfile
├── docker-compose.yml        # Docker 编排定义 (MySQL + App)
├── .env.example              # 环境变量配置模板
├── deploy.sh                 # 生产运维管理脚本 (start/stop/logs/backup)
├── start.sh                  # 本地无 Docker 开发调试脚本
└── README.md                 # 部署与使用文档
```
