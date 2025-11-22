# GitHub Actions - 实际使用示例

## 场景 1: 开发阶段 - 快速测试单个服务

### 需求
修改了 tgo-api 的代码，想快速构建测试。

### 操作步骤

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Build and push service images to multiple registries**
4. 点击 **Run workflow** 按钮
5. 在输入框输入: `tgo-api`
6. 点击 **Run workflow**

### 预期结果
- 只构建 tgo-api 镜像
- 推送到三个镜像仓库 (GHCR, Docker Hub, Alibaba Cloud)
- 构建时间: ~5-10 分钟

---

## 场景 2: 测试多个相关服务

### 需求
修改了 API 和前端，需要同时构建 tgo-api 和 tgo-web。

### 操作步骤

1. GitHub → Actions → Build and push...
2. Run workflow
3. 输入: `tgo-api,tgo-web`
4. Run workflow

### 预期结果
- 并行构建两个服务
- 每个服务都推送到三个镜像仓库
- 构建时间: ~10-15 分钟

---

## 场景 3: 服务独立发布

### 需求
tgo-api 完成了新功能，需要发布 v1.2.0 版本。

### 操作步骤

```bash
# 1. 确保代码已提交
git add .
git commit -m "feat: add new API features"

# 2. 创建 tag
git tag tgo-api-v1.2.0

# 3. 推送 tag
git push origin tgo-api-v1.2.0
```

### 预期结果
- GitHub Actions 自动触发
- 只构建 tgo-api 服务
- 镜像标签: `tgo-api:v1.2.0` 和 `tgo-api:latest`
- 构建时间: ~5-10 分钟

### 查看结果

```bash
# 查看本地 tag
git tag -l "tgo-api-*"

# 查看远程 tag
git ls-remote --tags origin | grep tgo-api

# 查看镜像
docker pull ghcr.io/tgoai/tgo/tgo-api:v1.2.0
```

---

## 场景 4: 多服务独立发布

### 需求
同时发布 tgo-api v1.2.0 和 tgo-web v2.1.0。

### 操作步骤

```bash
# 发布 tgo-api
git tag tgo-api-v1.2.0
git push origin tgo-api-v1.2.0

# 发布 tgo-web
git tag tgo-web-v2.1.0
git push origin tgo-web-v2.1.0
```

### 预期结果
- 两个工作流并行运行
- 分别构建两个服务
- 总构建时间: ~10-15 分钟

---

## 场景 5: 完整版本发布

### 需求
所有服务都准备好了，需要发布完整的 v1.0.0 版本。

### 操作步骤

```bash
# 1. 确保所有代码已提交
git add .
git commit -m "chore: release v1.0.0"

# 2. 创建通用 tag
git tag v1.0.0

# 3. 推送 tag
git push origin v1.0.0
```

### 预期结果
- GitHub Actions 自动触发
- 自动发现并构建所有服务
- 每个服务都标记为 `v1.0.0` 和 `latest`
- 总构建时间: ~30-45 分钟（取决于服务数量）

### 查看结果

```bash
# 查看所有镜像
docker pull ghcr.io/tgoai/tgo/tgo-api:v1.0.0
docker pull ghcr.io/tgoai/tgo/tgo-web:v1.0.0
docker pull ghcr.io/tgoai/tgo/tgo-rag:v1.0.0
```

---

## 场景 6: 紧急修复

### 需求
生产环境发现 bug，需要快速修复并发布 tgo-api。

### 操作步骤

```bash
# 1. 修复 bug
# ... 编辑代码 ...

# 2. 提交修复
git add .
git commit -m "fix: critical bug in API"

# 3. 创建 hotfix tag
git tag tgo-api-v1.2.1
git push origin tgo-api-v1.2.1
```

### 预期结果
- 立即触发构建
- 只构建 tgo-api
- 快速推送到镜像仓库
- 可以立即部署修复版本

---

## 场景 7: 构建所有服务

### 需求
需要构建所有服务的最新版本。

### 方式 A: 使用 workflow_dispatch

1. GitHub → Actions → Build and push...
2. Run workflow
3. 留空输入框
4. Run workflow

### 方式 B: 使用通用 tag

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 预期结果
- 自动发现所有服务
- 并行构建所有服务
- 总构建时间: ~30-45 分钟

---

## 场景 8: 查看构建日志

### 需求
想查看构建过程和结果。

### 操作步骤

1. GitHub 仓库 → **Actions** 标签
2. 选择 **Build and push service images to multiple registries**
3. 选择最新的工作流运行
4. 查看各个步骤的日志

### 关键日志位置

- **discover-services**: 查看发现了哪些服务
- **Display build information**: 查看构建信息
- **Build and push image**: 查看构建过程
- **Verify multi-architecture manifest**: 查看验证结果

---

## 场景 9: 重新运行失败的构建

### 需求
构建失败了，修复问题后想重新运行。

### 操作步骤

1. GitHub → Actions → 选择失败的工作流
2. 点击 **Re-run failed jobs** 按钮
3. 等待重新构建

### 或者重新推送 tag

```bash
# 删除本地 tag
git tag -d tgo-api-v1.2.0

# 删除远程 tag
git push origin :refs/tags/tgo-api-v1.2.0

# 重新创建并推送
git tag tgo-api-v1.2.0
git push origin tgo-api-v1.2.0
```

---

## 场景 10: 验证镜像

### 需求
构建完成后，验证镜像是否正确推送。

### 操作步骤

```bash
# 查看 GHCR 镜像
docker pull ghcr.io/tgoai/tgo/tgo-api:v1.2.0
docker inspect ghcr.io/tgoai/tgo/tgo-api:v1.2.0

# 查看 Docker Hub 镜像
docker pull tgoai/tgo-api:v1.2.0

# 查看 Alibaba Cloud 镜像
docker pull registry.cn-shanghai.aliyuncs.com/tgoai/tgo-api:v1.2.0

# 验证多架构支持
docker buildx imagetools inspect ghcr.io/tgoai/tgo/tgo-api:v1.2.0
```

---

## 常见问题排查

### 构建失败

1. 查看 Actions 日志
2. 查看具体错误信息
3. 修复问题
4. 重新运行或重新推送 tag

### 镜像未推送

1. 检查 GitHub Secrets 配置
2. 检查镜像仓库权限
3. 查看工作流日志中的登录步骤

### 多架构验证失败

1. 检查 Docker Buildx 配置
2. 查看构建日志中的平台信息
3. 确保两个架构都成功构建

---

## 最佳实践总结

| 阶段 | 方式 | 命令 |
|------|------|------|
| 开发测试 | workflow_dispatch | 输入 `tgo-api` |
| 服务发布 | Tag 前缀 | `git tag tgo-api-v1.2.0` |
| 完整发布 | 通用 Tag | `git tag v1.0.0` |
| 紧急修复 | Tag 前缀 | `git tag tgo-api-v1.2.1` |

