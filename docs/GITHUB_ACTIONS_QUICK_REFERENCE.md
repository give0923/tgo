# GitHub Actions - 快速参考

## 三种构建方式

### 1️⃣ 手动选择 (最快)

**场景**: 快速测试、紧急修复

**操作**:
1. GitHub → Actions → Build and push...
2. Run workflow
3. 输入服务名称: `tgo-api` 或 `tgo-api,tgo-web`
4. Run workflow

**示例**:
```
tgo-api              # 只构建 tgo-api
tgo-api,tgo-web      # 构建两个服务
                     # 留空 = 构建所有
```

---

### 2️⃣ Tag 前缀 (自动化)

**场景**: 服务独立发布、CI/CD 自动化

**命令**:
```bash
# 只构建 tgo-api v1.0.0
git tag tgo-api-v1.0.0
git push origin tgo-api-v1.0.0

# 只构建 tgo-web v2.1.0
git tag tgo-web-v2.1.0
git push origin tgo-web-v2.1.0

# 只构建 tgo-rag v1.5.0
git tag tgo-rag-v1.5.0
git push origin tgo-rag-v1.5.0
```

**格式**: `tgo-<service>-v<version>`

---

### 3️⃣ 通用 Tag (完整发布)

**场景**: 所有服务同步发布

**命令**:
```bash
# 构建所有服务 v1.0.0
git tag v1.0.0
git push origin v1.0.0

# 构建所有服务 v2.1.0
git tag v2.1.0
git push origin v2.1.0
```

**格式**: `v<version>`

---

## 常用命令速查

| 需求 | 方式 | 命令/操作 |
|------|------|---------|
| 快速测试 tgo-api | workflow_dispatch | 输入 `tgo-api` |
| 测试多个服务 | workflow_dispatch | 输入 `tgo-api,tgo-web` |
| 发布 tgo-api | Tag 前缀 | `git tag tgo-api-v1.0.0` |
| 发布 tgo-web | Tag 前缀 | `git tag tgo-web-v1.0.0` |
| 完整发布 | 通用 Tag | `git tag v1.0.0` |
| 构建所有 | workflow_dispatch | 留空输入框 |

---

## 查看构建状态

1. GitHub 仓库 → **Actions** 标签
2. 选择 **Build and push service images to multiple registries**
3. 查看最新运行
4. 点击 **discover-services** 查看服务发现日志

---

## 日志示例

### 手动选择
```
✓ Using manually specified services: tgo-api,tgo-web
Services to build: ["tgo-api","tgo-web"]
```

### Tag 前缀
```
✓ Tag prefix detected: tgo-api-v1.0.0
✓ Building specific service: tgo-api
```

### 自动发现
```
✓ Auto-discovering all services...
Discovered services: ["tgo-api","tgo-web","tgo-rag",...]
```

---

## 优先级

```
workflow_dispatch (最高)
    ↓
Tag 前缀
    ↓
自动发现 (最低)
```

如果同时满足多个条件，按优先级执行。

---

## 支持的服务

任何 `repos/` 下有 `Dockerfile` 的服务：

- tgo-api
- tgo-web
- tgo-widget-app
- tgo-rag
- tgo-ai
- tgo-platform
- 等等...

---

## 常见问题

**Q: 如何同时构建多个服务？**
```
tgo-api,tgo-web,tgo-rag
```

**Q: 如何构建所有服务？**
- workflow_dispatch 留空
- 或使用 `git tag v1.0.0`

**Q: 构建失败了？**
- 查看 Actions 日志
- 修复后点击 "Re-run failed jobs"

**Q: Tag 是否区分大小写？**
- 是的，使用小写: `tgo-api-v1.0.0` ✅

---

## 完整文档

详见: `docs/GITHUB_ACTIONS_SELECTIVE_BUILD.md`

