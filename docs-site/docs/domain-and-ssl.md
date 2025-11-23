---
id: domain-and-ssl
title: 域名与 SSL 配置
---

本页说明如何通过 `./tgo.sh config ...` 配置 Web / Widget / API 域名，并开启 HTTPS（Let’s Encrypt 自动证书或自有证书）。
底层逻辑主要定义在根目录的 `tgo.sh` 中的 `cmd_config`、`ensure_domain_config` 和相关脚本中。

## 配置域名

域名与基础配置保存在 `./data/.tgo-domain-config` 文件中，可以通过以下命令写入：

在仓库根目录执行：

```bash
./tgo.sh config web_domain www.example.com
./tgo.sh config widget_domain widget.example.com
./tgo.sh config api_domain api.example.com
```

效果：

- 在 `./data/.tgo-domain-config` 中写入或更新：
  - `WEB_DOMAIN`
  - `WIDGET_DOMAIN`
  - `API_DOMAIN`
- 该配置文件会被后续的 Nginx 生成脚本使用，将不同域名反向代理到对应服务（web、widget、api）。

如果短期内只需要 HTTP（不启用 SSL），可以显式设置：

```bash
./tgo.sh config ssl_mode none
./tgo.sh config apply
```

- `ssl_mode none` 会在配置文件中记录 `SSL_MODE=none`；
- `config apply` 会调用 `scripts/generate-nginx-config.sh`，根据当前域名与 SSL 参数生成/更新 Nginx 配置。

## 启用 HTTPS（SSL）

### 方案 A：自动申请 Let’s Encrypt 证书（推荐）

前提条件：

- `WEB_DOMAIN` / `WIDGET_DOMAIN` / `API_DOMAIN` 均已配置；
- 这些域名的 DNS 已正确解析到当前服务器的公网 IP；
- 服务器能访问 Let’s Encrypt。

执行以下命令：

```bash
./tgo.sh config ssl_email your-email@example.com
./tgo.sh config setup_letsencrypt
./tgo.sh config apply
```

作用：

1. `ssl_email`：设置 Let’s Encrypt 注册邮箱；
2. `setup_letsencrypt`：
   - 调用 `scripts/setup-ssl.sh` 为上述所有域名申请证书；
   - 成功后将 `SSL_MODE` 更新为 `auto`；
3. `apply`：重新生成并应用 Nginx 配置，使 HTTPS 生效。

之后可以直接使用：

- `https://www.example.com`（Web）
- `https://widget.example.com`（Widget）
- `https://api.example.com`（API）

### 方案 B：使用已有证书（手动上传）

如果你已经从其他 CA 获取了证书（`.crt` / `.pem` 加 `.key`），可以使用：

```bash
./tgo.sh config ssl_manual /path/to/cert.pem /path/to/key.pem [domain]
./tgo.sh config apply
```

说明：

- 不指定 `domain` 时，脚本会为配置文件中所有域名（WEB / WIDGET / API）安装该证书；
- 指定 `domain` 时，只为该域名安装；
- 证书文件会被复制到：
  - `./data/nginx/ssl/<domain>/cert.pem`
  - `./data/nginx/ssl/<domain>/key.pem`
- 同时将 `SSL_MODE` 设置为 `manual`，`apply` 会据此生成带证书的 Nginx 配置。

## 查看当前域名与 SSL 状态

任何时候都可以执行：

```bash
./tgo.sh config show
```

查看 `./data/.tgo-domain-config` 当前内容，包括：

- 已配置的 `WEB_DOMAIN` / `WIDGET_DOMAIN` / `API_DOMAIN`；
- 当前 `SSL_MODE`（`none` / `auto` / `manual`）；
- Let’s Encrypt 邮箱等信息。

---

如果你需要了解 Nginx 配置生成脚本的具体行为，或对证书目录结构、自定义反向代理有更深入的需求，建议直接阅读根目录的 `tgo.sh`、`scripts/generate-nginx-config.sh` 和 `scripts/setup-ssl.sh` 源码。


