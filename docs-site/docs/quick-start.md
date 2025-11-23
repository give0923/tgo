---
id: quick-start
title: 快速开始
---

本页给出 **最简版安装命令** 和必要的版本说明，帮助你在一台新机器上快速拉起 tgo。

## 海外网络（GitHub）

在目标服务器上直接执行：

```bash
REF=latest curl -fsSL https://raw.githubusercontent.com/tgoai/tgo/main/bootstrap.sh | bash
```

## 中国大陆网络（Gitee + 阿里云镜像）

如果在中国境内部署，推荐使用：

```bash
REF=latest curl -fsSL https://gitee.com/tgoai/tgo/raw/main/bootstrap_cn.sh | bash
```

> 说明：`REF` 用来指定要部署的版本：
> - `REF=latest`：使用仓库默认分支的当前最新版本；
> - 也可以改为具体 Tag/分支/提交号，例如 `REF=v1.0.0`。

## 安装完成后如何访问

安装脚本会自动完成仓库克隆与 `./tgo.sh install` 调用，所有核心服务拉起后：

- 在服务器本机浏览器访问：`http://localhost`
- 如果是远程服务器，则用：`http://<服务器IP>` 或之后配置好的域名访问。

> 进阶：更多关于命令和配置，请看「安装与配置」文档；  
> 域名和 HTTPS 证书相关内容在单独的「域名与 SSL 配置」文档中说明。


