# GitHub Actions - 选择性构建指南

## 概述

GitHub Actions 工作流现已支持三种方式来选择要构建的服务：

1. **手动选择** (workflow_dispatch) - 最灵活
2. **Tag 前缀** (push tags) - 自动化友好
3. **自动发现** (通用 tag) - 构建所有服务

## 优先级

服务发现按以下优先级进行：

```
优先级 1: workflow_dispatch 手动指定 (最高)
    ↓
优先级 2: Tag 前缀 (tgo-*-v*)
    ↓
优先级 3: 自动发现所有服务 (最低)
```

---

## 方式 1: 手动选择 (workflow_dispatch)

### 使用场景
- 快速测试单个服务
- 紧急修复和部署
- 开发调试

### 操作步骤

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择 **Build and push service images to multiple registries**
4. 点击 **Run workflow** 按钮
5. 在 "Services to build" 输入框中输入服务名称
6. 点击 **Run workflow**

### 输入格式

| 输入 | 效果 |
|------|------|
| `tgo-api` | 只构建 tgo-api |
| `tgo-api,tgo-web` | 构建 tgo-api 和 tgo-web |
| `tgo-api, tgo-web, tgo-rag` | 构建三个服务（支持空格） |
| 留空 | 构建所有服务 |

### 示例

**只构建 tgo-api**:
```
tgo-api
```

**构建多个服务**:
```
tgo-api,tgo-web,tgo-platform
```

---

## 方式 2: Tag 前缀 (自动化)

### 使用场景
- CI/CD 自动化流程
- 服务独立版本管理
- 生产环境部署

### Tag 格式

```
tgo-<service-name>-v<version>
```

### 示例

**只构建 tgo-api v1.0.0**:
```bash
git tag tgo-api-v1.0.0
git push origin tgo-api-v1.0.0
```

**只构建 tgo-web v2.1.0**:
```bash
git tag tgo-web-v2.1.0
git push origin tgo-web-v2.1.0
```

**只构建 tgo-rag v1.5.0**:
```bash
git tag tgo-rag-v1.5.0
git push origin tgo-rag-v1.5.0
```

### 支持的服务

任何 `repos/` 目录下有 `Dockerfile` 的服务都支持：
- `tgo-api-v*`
- `tgo-web-v*`
- `tgo-widget-app-v*`
- `tgo-rag-v*`
- `tgo-ai-v*`
- `tgo-platform-v*`
- 等等...

---

## 方式 3: 通用 Tag (构建所有)

### 使用场景
- 完整版本发布
- 所有服务同步更新
- 主版本发布

### Tag 格式

```
v<version>
```

### 示例

**构建所有服务 v1.0.0**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

**构建所有服务 v2.1.0**:
```bash
git tag v2.1.0
git push origin v2.1.0
```

---

## 工作流日志

### 查看构建日志

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择最新的工作流运行
4. 查看 **discover-services** 任务的输出

### 日志示例

**手动选择服务**:
```
=== Service Discovery ===
Trigger: workflow_dispatch
Ref: main

✓ Using manually specified services: tgo-api,tgo-web
Services to build: ["tgo-api","tgo-web"]
```

**Tag 前缀**:
```
=== Service Discovery ===
Trigger: push
Ref: tgo-api-v1.0.0

✓ Tag prefix detected: tgo-api-v1.0.0
✓ Building specific service: tgo-api
```

**自动发现**:
```
=== Service Discovery ===
Trigger: push
Ref: v1.0.0

✓ Auto-discovering all services...
Discovered services: ["tgo-api","tgo-web","tgo-rag","tgo-ai","tgo-platform","tgo-widget-app"]
```

---

## 常见问题

### Q: 如何同时构建多个服务？

**A**: 使用逗号分隔的列表：
```
tgo-api,tgo-web,tgo-rag
```

### Q: 如何构建所有服务？

**A**: 三种方式都可以：
1. workflow_dispatch 中留空
2. 使用通用 tag: `git tag v1.0.0`
3. 自动发现（默认行为）

### Q: Tag 前缀是否区分大小写？

**A**: 是的，tag 区分大小写。使用小写服务名称：
- ✅ `tgo-api-v1.0.0`
- ❌ `TGO-API-v1.0.0`
- ❌ `tgo-API-v1.0.0`

### Q: 如何查看构建进度？

**A**: 
1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择正在运行的工作流
4. 查看实时日志

### Q: 构建失败了怎么办？

**A**: 
1. 查看工作流日志找出错误原因
2. 修复问题后重新运行
3. 可以点击 **Re-run failed jobs** 重新运行失败的任务

---

## 最佳实践

### 1. 开发阶段
使用 workflow_dispatch 快速测试：
```
tgo-api
```

### 2. 服务发布
使用 tag 前缀自动化：
```bash
git tag tgo-api-v1.0.0
git push origin tgo-api-v1.0.0
```

### 3. 完整发布
使用通用 tag：
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 4. 多服务更新
使用 workflow_dispatch：
```
tgo-api,tgo-web,tgo-platform
```

---

## 工作流配置

### 触发条件

```yaml
on:
  push:
    tags:
      - 'v*'              # 通用 tag: v1.0.0
      - 'tgo-*-v*'        # 服务 tag: tgo-api-v1.0.0
  workflow_dispatch:      # 手动触发
    inputs:
      services:
        description: 'Services to build (comma-separated, or leave empty for all)'
        required: false
        default: ''
```

### 服务发现逻辑

```bash
# 优先级 1: workflow_dispatch 指定
if [ -n "${{ github.event.inputs.services }}" ]; then
  # 使用指定的服务
fi

# 优先级 2: Tag 前缀
if [[ $tag =~ ^(tgo-[a-z-]+)-v ]]; then
  # 使用匹配的服务
fi

# 优先级 3: 自动发现
# 发现所有有 Dockerfile 的服务
```

---

## 相关文件

- `.github/workflows/build-and-push.yml` - 工作流定义
- `repos/*/Dockerfile` - 服务 Dockerfile

## 更多信息

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Workflow Dispatch](https://docs.github.com/en/actions/using-workflows/manually-running-a-workflow)
- [Git Tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

