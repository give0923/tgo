# tgo-deploy 部署指南

本仓库提供一套基于 Docker Compose 的一键部署方案，编排并启动：
- 依赖：Postgres(pgvector)、Redis、Kafka(+UI)、WuKongIM
- 应用：tgo-api、tgo-ai、tgo-platform、tgo-rag(+worker/beat/flower)、tgo-web、tgo-widget-app

> 说明：本仓库默认使用当前项目的 `repos/` 目录中的各子项目源码，不再在部署时自动克隆。

## 前置条件
- Docker (建议 24+)、Docker Compose 插件
- Bash 环境（macOS / Linux / WSL2 均可）

## 多架构支持 🚀

所有 TGO 服务的 Docker 镜像都支持多架构，可以在以下平台上原生运行：
- **AMD64** (x86_64) - 传统服务器和 PC
- **ARM64** (aarch64) - Apple Silicon (M1/M2/M3)、AWS Graviton、树莓派等

Docker 会自动选择与您系统架构匹配的镜像，无需额外配置。详见 [多架构支持文档](docs/MULTI_ARCH_SUPPORT.md)。

## 开发者说明

### Bootstrap 脚本构建系统

本项目使用自动化构建系统来维护 `bootstrap.sh` 和 `bootstrap_cn.sh`：

- **源文件**: `bootstrap.sh` - 国际版，作为主模板
- **生成文件**: `bootstrap_cn.sh` - 中国版，由构建脚本自动生成
- **构建脚本**: `build-bootstrap.sh` - 从 bootstrap.sh 生成 bootstrap_cn.sh

**修改 bootstrap 脚本时**：
1. 只需编辑 `bootstrap.sh`
2. 运行 `./build-bootstrap.sh` 重新生成 `bootstrap_cn.sh`
3. 提交两个文件

详见 [Bootstrap 构建系统文档](docs/BOOTSTRAP_BUILD_SYSTEM.md)。

## 快速开始
1) 克隆并进入仓库
- git clone <this-repo>
- cd tgo-deploy

2) 准备配置
- 首次运行 `./tgo.sh install` 会自动：
  - 如无 `.env`，从 `.env.example` 复制生成
  - 如无 `envs/`，从 `envs.docker/` 复制生成
  - 如 `envs/tgo-api.env` 中 `SECRET_KEY` 缺失/占位，将自动生成安全随机值
- 如需自定义，先编辑 `.env`（端口、数据库 DSN、API_BASE_URL 等），以及 `envs/<service>.env`

3) 启动
- ./tgo.sh install
- 首次会完成镜像构建、数据库迁移并以后台方式启动全部服务

## tgo.sh 命令一览
- `./tgo.sh help`：查看所有命令及用法
- `./tgo.sh install [--source] [--cn]`：部署全部服务（执行迁移并启动）
- `./tgo.sh uninstall [--source] [--cn]`：停止并移除所有服务，可选择是否删除 `./data/`
- `./tgo.sh service start [--source] [--cn]`：启动核心服务
- `./tgo.sh service stop [--source] [--cn]`：停止核心服务
- `./tgo.sh service remove [--source] [--cn]`：停止核心服务并移除镜像
- `./tgo.sh tools start`：启动调试工具（kafka-ui、adminer）
- `./tgo.sh tools stop`：停止调试工具
- `./tgo.sh build --source [--cn] <service>`：重建并重启指定服务（api|rag|ai|platform|web|widget|all）

### 部署模式选项
- **`--source`**：从本地源码构建镜像（使用 `repos/` 目录）
- **`--cn`**：使用中国镜像源（阿里云 ACR），适用于中国境内网络环境
- 两个选项可以组合使用：`./tgo.sh install --source --cn`

### 中国境内网络优化
如果你在中国境内部署，强烈建议使用 `--cn` 参数以获得更快的镜像拉取速度：

```bash
# 使用阿里云 ACR 镜像部署（推荐）
./tgo.sh install --cn

# 从源码构建并部署
./tgo.sh install --source --cn
```

详细说明请参考：[中国境内网络环境部署指南](docs/CN_MIRROR_GUIDE.md)

## 目录结构与持久化数据
- `docker-compose.yml`：服务编排
- `envs.docker/`：服务环境变量模板（首次会复制为 `envs/`）
- `envs/`：运行时服务环境。已被 `.gitignore` 忽略
- `repos/`：各子项目源码（本仓库默认已存在/自行放置；`.gitignore` 忽略）
- `data/`：统一的持久化数据目录（`.gitignore` 忽略）
  - `data/postgres` → /var/lib/postgresql/data
  - `data/redis` → /data
  - `data/kafka/data` → /var/lib/kafka/data
  - `data/wukongim` → /root/wukongim
  - `data/tgo-rag/uploads` → /app/uploads

## 配置说明与覆盖规则
- 全局配置：根目录 `.env`
  - 数据库 DSN：`DATABASE_URL`、`TGO_PG_DSN`
  - 端口：`API_PORT`、`AI_PORT`、`PLATFORM_PORT`、`RAG_PORT`、`WEB_PORT` 等
  - API 基础地址：`API_BASE_URL`（默认见 `.env.example`）
- 服务专属配置：`envs/<service>.env`
  - 仅放与该服务强相关的配置
- env_file 加载顺序与覆盖：
  - tgo-api：先加载 `envs/tgo-api.env`，再加载 `.env` → 允许用根目录 `.env` 覆盖 `API_BASE_URL`
  - 其他服务：先加载 `.env`，再加载 `envs/<service>.env` → 服务专属 env 可覆盖全局配置

## 访问入口（默认端口）
- API: http://localhost:8000
- AI: http://localhost:8002
- Platform: http://localhost:8003
- RAG: http://localhost:8082
- Web: http://localhost:3000
- Widget: http://localhost:3001
- Adminer: http://localhost:8888
- Kafka UI: http://localhost:8088
- WuKongIM: 5001(HTTP) / 5100(TCP) / 5200(WS) / 5300(Admin) / 5172(Demo) / 11110(Cluster)

## 常用命令
- 查看状态：`docker compose ps`
- 查看日志：`docker compose logs -f tgo-api`（替换为具体服务名）
- 停止：`docker compose down`
- 重新构建：`docker compose build --no-cache <service>`
- 清理数据（危险）：`docker compose down -v` 然后手动删除 `data/`

## 故障排查
- 子项目是否存在：`repos/` 下应包含 `tgo-api`、`tgo-ai`、`tgo-platform`、`tgo-rag`、`tgo-web`、`tgo-widget-app`
- 端口冲突：如被占用，请修改 `.env` 中相应端口后重启
- 权限问题：确保当前用户对 `data/` 具有读写权限
- 构建失败：检查对应子项目 Dockerfile 是否存在且可用

## 一键远程部署（bootstrap.sh）

适用场景：在一台干净机器上一条命令完成检查、克隆并运行 tgo.sh install。

### 国际版（bootstrap.sh）

使用 GitHub 仓库，适合海外服务器或网络环境良好的用户。

脚本行为概览：
- 检查 git、docker、docker compose
- 如当前目录已存在 tgo.sh 和 docker-compose.yml，直接运行 `./tgo.sh install`
- 否则克隆 REPO 到 DIR（默认 https://github.com/tgoai/tgo.git → ./tgo），可选切换到 REF（分支/Tag/提交）
- 在 DIR 中执行 `./tgo.sh install`

推荐用法（GitHub Raw 示例）：
- 最新主分支：`curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash`
- 指定版本/分支：`REF=v1.0.0 curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash`
- 自定义仓库/目录：`REPO=https://gitee.com/your/tgo.git DIR=tgo curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash`

通过 SSH 在远程服务器一键执行：
- `ssh user@server 'curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash'`
- 指定版本：`ssh user@server 'REF=v1.0.0 curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash'`

本地运行（已在仓库内）：
- `bash ./bootstrap.sh`

### 中国版（bootstrap_cn.sh）⚡

**推荐中国境内用户使用**，使用 Gitee 镜像仓库和阿里云容器镜像服务，显著提升部署速度。

主要优化：
- 使用 Gitee 镜像（https://gitee.com/tgoai/tgo.git）加速 Git 克隆
- 自动执行 `./tgo.sh install --cn` 使用阿里云 ACR 镜像
- 其他功能与国际版完全一致

推荐用法（Gitee Raw 示例）：
- 最新主分支：`curl -fsSL https://gitee.com/tgoai/tgo/raw/main/bootstrap_cn.sh | bash`
- 指定版本/分支：`REF=v1.0.0 curl -fsSL https://gitee.com/tgoai/tgo/raw/main/bootstrap_cn.sh | bash`

通过 SSH 在远程服务器一键执行：
- `ssh user@server 'curl -fsSL https://gitee.com/tgoai/tgo/raw/main/bootstrap_cn.sh | bash'`

本地运行（已在仓库内）：
- `bash ./bootstrap_cn.sh`

### 可配置项（环境变量）

- **REPO**：仓库地址
  - bootstrap.sh 默认：`https://github.com/tgoai/tgo.git`
  - bootstrap_cn.sh 默认：`https://gitee.com/tgoai/tgo.git`
- **DIR**：克隆目录名（默认 `tgo`）
- **REF**：可选分支/Tag/提交（为空则使用默认分支）

### 性能对比（中国境内网络）

| 操作 | bootstrap.sh | bootstrap_cn.sh | 提升 |
|------|-------------|-----------------|------|
| Git 克隆 | ~5-15 分钟 | ~30-60 秒 | **10-15x** |
| 镜像拉取 | ~10-30 分钟 | ~2-5 分钟 | **5-10x** |
| 总部署时间 | ~15-45 分钟 | ~3-6 分钟 | **5-7x** |

注意：如果你将 bootstrap.sh 或 bootstrap_cn.sh 托管到自有域名，请把上述 URL 替换为你的地址即可。

# 配置域名和 SSL（https） 证书

```
# 配置域名

# 配置web域名
./tgo.sh config web_domain www.example.com
# 配置widget域名
./tgo.sh config widget_domain widget.example.com
# 配置api域名
./tgo.sh config api_domain api.example.com
# 配置websocket域名
./tgo.sh config ws_domain ws.example.com

# 配置SSL证书
./tgo.sh config ssl_mode auto
# 配置Let's Encrypt邮箱
./tgo.sh config ssl_email admin@example.com
# 应用配置
./tgo.sh config apply

# 自动申请证书
sudo ./tgo.sh config setup_letsencrypt

# 重启服务
./tgo.sh up

```
