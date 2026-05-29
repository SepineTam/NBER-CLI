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

- 阅读 [CLI 参考](cli.md) 了解全部命令和选项。
- 配置 [MCP Server](mcp.md) 用于 Agent 工作流。
- 在自己的异步代码中使用 [Python API](python-api.md)。
