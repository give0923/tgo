# GitHub Actions - 选择性构建实现总结

## ✅ 实现完成

已成功实现 GitHub Actions 工作流的选择性构建功能，支持三种方式灵活选择要构建的服务。

---

## 📋 实现内容

### 1. 工作流配置更新

**文件**: `.github/workflows/build-and-push.yml`

**主要改进**:

#### 触发条件扩展
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

#### 智能服务发现
- **优先级 1**: workflow_dispatch 手动指定
- **优先级 2**: Tag 前缀自动识别
- **优先级 3**: 自动发现所有服务

#### 增强的日志输出
- 显示触发方式
- 显示服务发现过程
- 显示构建信息

---

## 🎯 三种使用方式

### 方式 1: 手动选择 (workflow_dispatch)

**场景**: 快速测试、紧急修复

**操作**: GitHub UI → Actions → Run workflow → 输入服务名称

**示例**:
```
tgo-api              # 单个服务
tgo-api,tgo-web      # 多个服务
                     # 留空 = 所有服务
```

### 方式 2: Tag 前缀 (自动化)

**场景**: 服务独立发布、CI/CD 自动化

**命令**:
```bash
git tag tgo-api-v1.0.0
git push origin tgo-api-v1.0.0
```

**格式**: `tgo-<service>-v<version>`

### 方式 3: 通用 Tag (完整发布)

**场景**: 所有服务同步发布

**命令**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

**格式**: `v<version>`

---

## 📊 优先级机制

```
┌─────────────────────────────────────────┐
│ workflow_dispatch 手动指定 (最高)        │
│ 示例: tgo-api,tgo-web                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Tag 前缀自动识别                         │
│ 示例: tgo-api-v1.0.0                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 自动发现所有服务 (最低)                  │
│ 示例: v1.0.0 或无指定                   │
└─────────────────────────────────────────┘
```

---

## 🔍 服务发现逻辑

```bash
# 优先级 1: workflow_dispatch 指定
if [ -n "${{ github.event.inputs.services }}" ]; then
  # 解析逗号分隔的服务列表
  # 支持空格: "tgo-api, tgo-web"
  # 输出: ["tgo-api", "tgo-web"]
fi

# 优先级 2: Tag 前缀
if [[ $tag =~ ^(tgo-[a-z-]+)-v ]]; then
  # 从 tag 中提取服务名称
  # 示例: tgo-api-v1.0.0 → tgo-api
  # 输出: ["tgo-api"]
fi

# 优先级 3: 自动发现
# 扫描 repos/ 目录
# 查找所有有 Dockerfile 的服务
# 输出: ["tgo-api", "tgo-web", "tgo-rag", ...]
```

---

## 📝 文档

### 快速参考
- **文件**: `docs/GITHUB_ACTIONS_QUICK_REFERENCE.md`
- **内容**: 三种方式速查表、常用命令

### 详细指南
- **文件**: `docs/GITHUB_ACTIONS_SELECTIVE_BUILD.md`
- **内容**: 完整使用说明、最佳实践、常见问题

### 实际示例
- **文件**: `docs/GITHUB_ACTIONS_EXAMPLES.md`
- **内容**: 10 个真实场景示例、排查指南

---

## 🚀 使用示例

### 快速测试
```bash
# GitHub UI: Actions → Run workflow → 输入 "tgo-api"
```

### 服务发布
```bash
git tag tgo-api-v1.0.0
git push origin tgo-api-v1.0.0
```

### 完整发布
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 多服务测试
```bash
# GitHub UI: Actions → Run workflow → 输入 "tgo-api,tgo-web,tgo-rag"
```

---

## ✨ 主要特性

✅ **灵活的服务选择**
- 手动选择单个或多个服务
- 自动识别 tag 前缀
- 自动发现所有服务

✅ **清晰的日志输出**
- 显示触发方式
- 显示服务发现过程
- 显示构建信息

✅ **向后兼容**
- 现有的 tag 方式仍然有效
- 自动发现功能保持不变

✅ **易于使用**
- 直观的 GitHub UI
- 简单的 git tag 命令
- 详细的文档和示例

---

## 📊 工作流对比

| 特性 | 手动选择 | Tag 前缀 | 通用 Tag |
|------|--------|--------|---------|
| 触发方式 | GitHub UI | git push | git push |
| 灵活性 | 最高 | 中等 | 最低 |
| 自动化 | 否 | 是 | 是 |
| 适用场景 | 开发测试 | 服务发布 | 完整发布 |
| 构建时间 | 快 | 中等 | 慢 |

---

## 🔧 技术细节

### 修改的文件
- `.github/workflows/build-and-push.yml` - 工作流定义

### 新增的文档
- `docs/GITHUB_ACTIONS_QUICK_REFERENCE.md`
- `docs/GITHUB_ACTIONS_SELECTIVE_BUILD.md`
- `docs/GITHUB_ACTIONS_EXAMPLES.md`
- `docs/GITHUB_ACTIONS_IMPLEMENTATION_SUMMARY.md`

### 支持的服务
任何 `repos/` 下有 `Dockerfile` 的服务都支持：
- tgo-api
- tgo-web
- tgo-widget-app
- tgo-rag
- tgo-ai
- tgo-platform
- 等等...

---

## 📚 相关文档

- **快速参考**: `docs/GITHUB_ACTIONS_QUICK_REFERENCE.md`
- **详细指南**: `docs/GITHUB_ACTIONS_SELECTIVE_BUILD.md`
- **实际示例**: `docs/GITHUB_ACTIONS_EXAMPLES.md`
- **工作流文件**: `.github/workflows/build-and-push.yml`

---

## ✅ 验证清单

- [x] 工作流配置更新
- [x] 服务发现逻辑实现
- [x] 优先级机制实现
- [x] 日志输出增强
- [x] 快速参考文档
- [x] 详细指南文档
- [x] 实际示例文档
- [x] 实现总结文档

---

## 🎉 下一步

1. **测试工作流**
   - 使用 workflow_dispatch 手动触发
   - 测试 tag 前缀功能
   - 验证自动发现功能

2. **验证镜像**
   - 检查镜像是否正确推送
   - 验证多架构支持
   - 检查镜像标签

3. **分享文档**
   - 与团队分享快速参考
   - 指导团队使用新功能
   - 收集反馈和改进建议

---

## 📞 支持

如有问题，请参考：
- `docs/GITHUB_ACTIONS_QUICK_REFERENCE.md` - 快速查找
- `docs/GITHUB_ACTIONS_SELECTIVE_BUILD.md` - 详细说明
- `docs/GITHUB_ACTIONS_EXAMPLES.md` - 实际示例

