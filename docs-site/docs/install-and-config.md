---
id: install-and-config
title: 安装与配置
---

本页在「快速开始」的基础上，简要说明：

- 一键安装脚本的大致行为；
- 安装完成后如何用 `./tgo.sh` 管理服务；
- 默认访问方式。

> 详细技术细节可以在仓库根目录的 `README.md` 与 `tgo.sh` 中找到，本页只保留最常用的用户操作。

## 一键安装脚本简要说明

无论是 GitHub 版本还是 Gitee 版本，安装脚本都会做三件事：

1. 检查 `git` / `docker` / `docker compose` 是否可用；
2. 克隆 `tgo` 仓库到本机（默认目录为 `./tgo`，可通过 `DIR` 环境变量覆盖）；
3. 进入仓库目录后执行：

   ```bash
   ./tgo.sh install
   ```

脚本会自动准备 `.env` 和 `envs/`，创建数据目录，完成镜像拉取或构建、数据库迁移，并后台启动所有核心服务。

`REF` 环境变量用于指定要部署的代码版本：

- `REF=latest`：使用默认分支的当前最新代码；
- 也可以改为具体 Tag、分支名或提交号，例如：`REF=v1.0.0`。

## 安装完成后如何管理服务

所有运维操作都通过根目录的 `./tgo.sh` 完成，常用命令包括：

- 首次安装（通常由一键脚本触发）：

  ```bash
  ./tgo.sh install [--source] [--cn]
  ```

- 启动服务（不重新初始化）：

  ```bash
  ./tgo.sh up [--source] [--cn]
  ```

- 关闭服务：

  ```bash
  ./tgo.sh down
  ```

- 查看帮助与所有命令：

  ```bash
  ./tgo.sh help
  ```

更多子命令（如 `upgrade`、`service`、`tools`、`build` 等）的说明可以参考 `README.md` 和 `tgo.sh` 头部的 usage 文档。

## 默认访问方式

当安装脚本完成并 `./tgo.sh install` 执行成功后，系统会通过 Nginx 统一对外暴露入口，你可以直接在浏览器访问：

- 本机访问：`http://localhost`
- 远程访问：`http://<服务器IP>`

后续如果配置了域名和 HTTPS，则可以通过 `https://<你的域名>` 访问，这部分内容见「域名与 SSL 配置」文档。


