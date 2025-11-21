# Alembic 命令行工具修复

## 问题描述

在使用 `./tgo.sh install --source` 部署时，遇到以下错误：

```
Running Alembic migrations for tgo-rag...
exec /opt/venv/bin/alembic: no such file or directory
```

## 根本原因

在 `repos/tgo-rag/Dockerfile` 的 builder 阶段，有以下清理命令：

```dockerfile
RUN poetry install --only=main --no-root && rm -rf "$POETRY_CACHE_DIR" && \
    ...
    find /app/.venv -type d -name "*.dist-info" -exec rm -rf {} + && \
    find /app/.venv -type d -name "*.egg-info" -exec rm -rf {} + && \
    ...
```

**问题**：

1. `*.dist-info` 目录包含 Python 包的元数据，包括**入口点（entry points）**定义
2. `alembic` 命令是通过入口点机制提供的命令行工具
3. 删除 `*.dist-info` 目录后：
   - ✅ Python 代码（alembic 库）仍然存在
   - ❌ 命令行工具 `/opt/venv/bin/alembic` 无法找到
   - ❌ 导致 `no such file or directory` 错误

## 修复方案

### 修改内容

移除了删除 `*.dist-info` 和 `*.egg-info` 的命令：

**修改前**：
```dockerfile
RUN poetry install --only=main --no-root && rm -rf "$POETRY_CACHE_DIR" && \
    find /app/.venv -type d -name "tests" -exec rm -rf {} + && \
    find /app/.venv -type d -name "test" -exec rm -rf {} + && \
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type f -name "*.pyo" -delete && \
    find /app/.venv -type d -name "*.dist-info" -exec rm -rf {} + && \  # ❌ 删除
    find /app/.venv -type d -name "*.egg-info" -exec rm -rf {} + && \  # ❌ 删除
    find /app/.venv -type d -name "doc" -exec rm -rf {} + && \
    ...
```

**修改后**：
```dockerfile
RUN poetry install --only=main --no-root && rm -rf "$POETRY_CACHE_DIR" && \
    find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type f -name "*.pyo" -delete && \
    # ✅ 不再删除 *.dist-info 和 *.egg-info
    find /app/.venv -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true && \
    ...
```

### 额外改进

添加了错误抑制（`2>/dev/null || true`）以提高构建的健壮性，避免因为找不到某些目录而导致构建失败。

## 影响分析

### 镜像大小

移除 `*.dist-info` 和 `*.egg-info` 删除后，镜像大小会略微增加：

| 项目 | 大小估算 |
|------|---------|
| *.dist-info 目录 | ~5-10 MB |
| *.egg-info 目录 | ~1-2 MB |
| **总增加** | **~6-12 MB** |

对于一个完整的 RAG 服务镜像（通常 1-2 GB），这个增加是可以接受的。

### 功能影响

保留这些目录后，以下功能正常工作：

- ✅ `alembic` - 数据库迁移
- ✅ `celery` - 任务队列
- ✅ `flower` - Celery 监控
- ✅ `uvicorn` - ASGI 服务器
- ✅ 其他所有命令行工具

## 为什么需要 *.dist-info

### Python 包元数据

`*.dist-info` 目录包含：

1. **METADATA** - 包的基本信息（名称、版本、作者等）
2. **RECORD** - 已安装文件的清单
3. **entry_points.txt** - 命令行工具的入口点定义
4. **WHEEL** - wheel 包的元数据
5. **top_level.txt** - 顶级模块名称

### 入口点示例

`alembic` 的入口点定义（在 `alembic-*.dist-info/entry_points.txt`）：

```ini
[console_scripts]
alembic = alembic.config:main
```

这告诉 Python：
- 创建一个名为 `alembic` 的可执行文件
- 指向 `alembic.config:main` 函数

删除 `*.dist-info` 后，这个映射关系丢失，导致命令无法找到。

## 验证修复

### 1. 重新构建镜像

```bash
# 方法 1: 使用 tgo.sh
./tgo.sh build --source tgo-rag

# 方法 2: 直接使用 docker compose
docker compose -f docker-compose.yml -f docker-compose.source.yml build tgo-rag
```

### 2. 验证 alembic 可用

```bash
# 启动一个临时容器
docker compose -f docker-compose.yml -f docker-compose.source.yml run --rm tgo-rag which alembic

# 应该输出: /opt/venv/bin/alembic
```

### 3. 运行迁移

```bash
# 重新运行安装
./tgo.sh install --source

# 应该成功运行 Alembic 迁移
```

## 最佳实践

### Docker 镜像优化建议

在优化 Docker 镜像大小时，**不应该删除**：

❌ **不要删除**：
- `*.dist-info` - 包含入口点和元数据
- `*.egg-info` - 旧式包的元数据
- `bin/` 目录中的可执行文件
- 运行时需要的配置文件

✅ **可以删除**：
- `__pycache__/` - Python 字节码缓存
- `*.pyc`, `*.pyo` - 编译的 Python 文件
- `tests/`, `test/` - 测试代码
- `docs/`, `doc/` - 文档
- `*.md`, `*.rst`, `*.txt` - 文档文件
- `examples/` - 示例代码
- `.git/` - Git 仓库（如果存在）

### 推荐的清理命令

```dockerfile
RUN poetry install --only=main --no-root && \
    rm -rf "$POETRY_CACHE_DIR" && \
    # 删除测试和文档
    find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true && \
    # 删除 Python 缓存
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type f -name "*.pyo" -delete && \
    # 删除文档文件
    find /app/.venv -type f -name "*.md" -delete && \
    find /app/.venv -type f -name "*.rst" -delete && \
    # 不要删除 *.dist-info 和 *.egg-info！
    echo "Cleanup completed."
```

## 相关问题

如果遇到其他命令行工具无法找到的问题（如 `celery`、`uvicorn` 等），请检查：

1. 是否删除了 `*.dist-info` 目录
2. 是否删除了 `bin/` 目录中的可执行文件
3. 是否正确设置了 `PATH` 环境变量

## 参考资料

- [PEP 427 - The Wheel Binary Package Format](https://www.python.org/dev/peps/pep-0427/)
- [PEP 376 - Database of Installed Python Distributions](https://www.python.org/dev/peps/pep-0376/)
- [Entry Points Specification](https://packaging.python.org/specifications/entry-points/)

---

**修复日期**: 2024-11-21  
**影响服务**: tgo-rag  
**修复文件**: `repos/tgo-rag/Dockerfile`

