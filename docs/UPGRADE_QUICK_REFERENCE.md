# Upgrade Command - Quick Reference

## 基本用法

```bash
./tgo.sh upgrade [--source] [--cn]
```

## 核心概念

**智能参数记忆**：`upgrade` 命令会记住您在 `install` 时使用的参数，无需每次都指定。

**配置文件**：`./data/.tgo-install-mode`

## 常用场景

### 场景 1: 标准升级（使用保存的配置）

```bash
# 首次安装
./tgo.sh install --cn

# 后续升级（自动使用 --cn）
./tgo.sh upgrade
```

### 场景 2: 覆盖配置

```bash
# 之前使用 --cn 安装
./tgo.sh install --cn

# 这次想用源码模式升级
./tgo.sh upgrade --source
```

### 场景 3: 源码模式升级

```bash
# 首次安装
./tgo.sh install --source

# 升级（自动 git pull + rebuild）
./tgo.sh upgrade
```

## 升级流程对比

| 步骤 | Image 模式 | Source 模式 |
|------|-----------|------------|
| 1 | 拉取镜像 | 拉取代码 (git pull) |
| 2 | 停止服务 | 重新构建镜像 |
| 3 | 启动基础设施 | 停止服务 |
| 4 | 运行迁移 | 启动基础设施 |
| 5 | 启动所有服务 | 运行迁移 |
| 6 | - | 启动所有服务 |

## 参数说明

| 参数 | 说明 | 默认行为 |
|------|------|---------|
| 无参数 | 使用保存的配置 | 从配置文件读取 |
| `--cn` | 使用中国镜像源 | 覆盖配置 |
| `--source` | 从源码构建 | 覆盖配置 |
| `--cn --source` | 两者都用 | 覆盖配置 |

## 配置文件示例

```bash
# ./data/.tgo-install-mode
USE_SOURCE=false
USE_CN=true
```

## 快速命令

```bash
# 查看当前配置
cat ./data/.tgo-install-mode

# 标准升级
./tgo.sh upgrade

# 强制使用 CN 镜像升级
./tgo.sh upgrade --cn

# 强制使用源码升级
./tgo.sh upgrade --source

# 查看服务状态
docker compose ps

# 查看升级日志
docker compose logs -f
```

## 升级前检查清单

- [ ] 备份重要数据（可选）
- [ ] 查看更新日志
- [ ] 确保有足够的磁盘空间
- [ ] 在测试环境先测试（生产环境）

## 升级后验证

```bash
# 检查所有服务是否运行
docker compose ps

# 查看服务日志
docker compose logs -f tgo-api

# 测试 API 访问
curl http://localhost:8000/health
```

## 故障排除

### 问题：配置文件不存在

```bash
[WARN] No saved install mode found at ./data/.tgo-install-mode
```

**解决**：手动指定参数
```bash
./tgo.sh upgrade --cn
```

### 问题：git pull 失败

```bash
[WARN] git pull failed, continuing with existing code
```

**解决**：手动更新代码
```bash
git pull
git submodule update --init --recursive
./tgo.sh upgrade --source
```

### 问题：镜像拉取失败

**解决**：切换镜像源
```bash
# 切换到 CN 镜像
./tgo.sh upgrade --cn

# 或切换到国际镜像
./tgo.sh upgrade
```

## 最佳实践

1. **定期升级**：每周或每月执行一次
2. **升级前备份**：重要数据先备份
3. **查看更新日志**：了解新功能和变更
4. **测试环境先行**：生产环境前先测试
5. **监控升级过程**：使用 `docker compose logs -f`

## 相关文档

- 详细文档：`docs/UPGRADE_COMMAND.md`
- 权限问题：`docs/DATA_DIRECTORY_PERMISSIONS.md`
- Alembic 修复：`docs/ALEMBIC_FIX.md`

## 示例工作流

```bash
# 1. 首次部署（使用 CN 镜像）
./tgo.sh install --cn

# 2. 一周后升级
./tgo.sh upgrade

# 3. 切换到源码模式
./tgo.sh upgrade --source

# 4. 回到镜像模式
./tgo.sh upgrade

# 5. 查看配置
cat ./data/.tgo-install-mode
```

---

**快速参考版本**: 1.0  
**完整文档**: `docs/UPGRADE_COMMAND.md`

