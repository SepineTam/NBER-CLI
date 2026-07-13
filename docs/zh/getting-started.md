# 快速开始

本指南帮助你从一台新机器开始，完成 NBER 工作论文的搜索、查看和下载。

## 环境要求

- Python 3.11 或更高版本。
- 能访问 `https://www.nber.org`。
- 使用 `uv`、`pipx` 或 `pip` 安装。

最快的方式是使用 `uvx`，它会在隔离环境中运行包，不需要永久安装。

## 使用 uvx 运行

```bash
uvx nber-cli --version
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

如果提示命令不存在或报错，请先通过 `uvx nber-cli -v` 检查当前运行的版本。如果不是最新版本，可以通过如下命令将缓存更新至最新版本：

```bash
uvx --refresh nber-cli -v
```

## 安装为命令

如果希望 shell 中一直可用 `nber-cli` 命令，可以使用：

```bash
uv tool install nber-cli
nber-cli --version
```

也可以使用 `pipx`：

```bash
pipx install nber-cli
nber-cli --version
```

## 运行可选的本地 HTTP Server

FastAPI、Uvicorn 和 Alembic 不会进入普通 CLI 依赖集合。需要使用 NBER-CLI Desktop 的本地 API 时，通过 `server` extra 启动：

```bash
uvx --from "nber-cli[server]" nber-server --host 127.0.0.1 --port 31527
```

Server 默认只绑定 loopback 地址，启动时把本地数据库升级到 schema v3，并在 `/api/v1` 下提供接口。

## 以 Python 模块方式运行

包还提供了模块入口。当 `nber-cli` console script 不在你的 `PATH` 上时（例如从 checkout 的工作区直接运行，或者在没生成 wrapper 脚本的虚拟环境里）这个入口会很有用：

```bash
python -m nber_cli --version
python -m nber_cli search "labor economics"
python -m nber_cli info w25000
```

`python -m nber_cli` 与 `nber-cli` 命令在功能上完全一致——同样的参数、同样的退出码、同样的 stdout/stderr 合同。在工作区中你也可以通过 `uv` 跑它：

```bash
uv run python -m nber_cli --version
```

## 第一次搜索

```bash
nber-cli search "labor economics"
```

搜索可以接受标题、作者、摘要、关键词或论文编号。默认每页返回 20 条结果。

添加日期范围和结果数量：

```bash
nber-cli search "minimum wage" --start-date 2024-01-01 --end-date 2024-12-31 --per-page 50
```

为脚本返回 JSON：

```bash
nber-cli search "inflation" --format json
```

## 查看论文详情

```bash
nber-cli info w25000
```

论文编号可以带 `w` 前缀，也可以不带：

```bash
nber-cli info 25000
```

使用 `--all` 可以包含 NBER 暴露的相关字段和 published version 信息：

```bash
nber-cli info w25000 --all
```

## 用 Feed 缓存跟踪新论文

初始化本地数据库：

```bash
nber-cli db init
```

数据库是由 SQLModel/SQLAlchemy 管理的本地 SQLite 文件，默认位于 `~/.nber-cli/nber.db`；高级用户可以用 `nber-cli db init --db-path ...` 指定其他路径或 `sqlite:///...` URL。

获取 NBER 最新工作论文 RSS feed：

```bash
nber-cli feed fetch
```

第一次获取会把当前 RSS 条目写入缓存，并显示为新条目。后续获取默认只显示缓存中还没有出现过的条目。

限制输出数量，同时显示最新获取到的条目：

```bash
nber-cli feed fetch --max-items 5
```

清理旧缓存记录：

```bash
nber-cli feed clean --days 30
```

`feed clean` 删除缓存记录前会要求确认。

## 下载 PDF

下载到当前目录：

```bash
nber-cli download w34567
```

保存到指定目录：

```bash
nber-cli download w34567 --save-base ~/papers/nber
```

保存到指定文件路径：

```bash
nber-cli download w34567 --file ~/papers/nber/w34567.pdf
```

## 批量下载

```bash
nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
```

批量模式支持 `--save-base`，不支持 `--file`。

## 下一步

- 安装并使用 [Desktop 应用](desktop.md)。
- 通过[本地 HTTP API](http-api.md)进行集成。
- 阅读 [CLI 参考](cli.md) 了解全部命令和选项。
- 配置 [MCP Server](mcp.md) 用于 Agent 工作流。
- 在自己的异步代码中使用 [Python API](python-api.md)。
