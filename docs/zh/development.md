# 开发

本页说明本地开发、测试、文档和发布准备流程。

## 仓库结构

```text
.
├── src/nber_cli/          # 包源码
├── tests/                 # Pytest 测试
├── docs/                  # MkDocs 文档源文件
├── .github/workflows/     # CI、发布和文档工作流
├── pyproject.toml         # 包元数据和依赖组
└── uv.lock                # 锁定依赖图
```

## 本地环境

```bash
uv sync --dev --group docs
```

从工作区运行 CLI：

```bash
uv run nber-cli --help
uv run nber-cli search "inflation"
```

## 测试

```bash
uv run pytest
```

运行特定测试文件：

```bash
uv run pytest tests/test_cli.py
```

## Lint

```bash
uv run ruff check .
```

## 文档

本地预览文档：

```bash
uv run --group docs mkdocs serve
```

严格模式构建文档：

```bash
uv run --group docs mkdocs build --strict
```

生成站点会写入 `site/`，不要提交该目录。

## GitHub Actions

项目使用独立工作流处理：

- 使用 Ruff 进行 lint。
- 运行 Pytest。
- 构建 MkDocs 文档。
- 在推送到 `master` 时部署文档到 GitHub Pages。
- 发布 GitHub release 时发布到 PyPI。

## 发布检查清单

1. 更新 `pyproject.toml` 中的版本号。
2. 更新 [更新日志](changelog.md)。
3. 运行 `uv lock`。
4. 运行 `uv run pytest`。
5. 运行 `uv run ruff check .`。
6. 运行 `uv run --group docs mkdocs build --strict`。
7. 创建并发布 GitHub release 以触发 PyPI 发布。

## 代码风格

- Python 代码目标版本是 Python 3.11 或更高。
- 变量名遵循 PEP 8，并使用清晰的英文名称。
- 代码注释使用英文。
- CLI 行为保持适合脚本：稳定退出码、可读错误、以及在自动化场景中可用的 JSON 输出。
