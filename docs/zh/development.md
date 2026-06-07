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

下面的检查项在打 tag 之前必须全部通过。每一项都对应一类历史上确实出过错的问题，跳过其中任何一项都曾经让 regression 漏出去。

### 代码与依赖

1. 修改 `pyproject.toml` 里的版本号。
2. 更新[更新日志](changelog.md)。根目录 `CHANGELOG.md` 与 `docs/en/changelog.md`、`docs/zh/changelog.md` 保持一致。
3. 运行 `uv lock` 并提交生成的 `uv.lock`。

### 静态检查

4. 运行 `uv run pytest -q`。
5. 运行 `uv run ruff check .`。
6. 运行 `uv run --group docs mkdocs build --strict`。

### 跨入口一致性

7. **包版本与 plugin manifest 保持一致。** Claude plugin manifest（`plugins/nber-cli/.claude-plugin/plugin.json`）、Codex plugin manifest（`plugins/nber-cli/.codex-plugin/plugin.json`）以及 marketplace 文件（`.claude-plugin/marketplace.json`、`.agents/plugins/marketplace.json`）的 `version` 必须与 `pyproject.toml` 完全一致。下面这条简单的 shell 循环就够用：
   ```bash
   grep -H '"version"' pyproject.toml \
     plugins/nber-cli/.claude-plugin/plugin.json \
     plugins/nber-cli/.codex-plugin/plugin.json \
     .claude-plugin/marketplace.json
   ```
8. **marketplace 文件和 skill 路径要被 Git 跟踪。** 运行 `git ls-files plugins/ .claude-plugin/ .agents/ | sort`，确认文档里引用的所有路径都在里面。在大小写敏感的 Linux checkout 上，`plugins/nber-cli/skills/nber-cli/SKILL.md`（小写）**不存在**；被跟踪的路径是 `plugins/nber-cli/skills/NBER-CLI/SKILL.md`。
9. **文档里的顶层导入都是真实可用的。** `docs/en/` 与 `docs/zh/` 中的 `from nber_cli import ...` 与 `import nber_cli.x as ...` 示例，必须指向 `nber_cli.__all__` 中的名字，或指向文档登记过的模块级辅助函数。运行下面的命令并确认输出为空：
   ```bash
   uv run python -c "from nber_cli import __all__; import re, pathlib; missing=[]; [missing.append((p, m)) for p in pathlib.Path('docs').rglob('*.md') for m in re.findall(r'(?:from nber_cli import|import nber_cli\.)\s*([A-Za-z0-9_]+)', p.read_text()) if m not in __all__ and not m.startswith('nber_cli.')]; print(missing)"
   ```
10. **公共 `__all__` 中的名字要有文档。** `nber_cli.__all__` 中的每个名字都应该出现在 `docs/en/python-api.md` 和 `docs/zh/python-api.md` 中。将来可以用上面的命令反向找出未登记的名字。
11. **CLI 帮助文本和 MCP 工具 schema 是健康的。** 运行 `uv run nber-cli --help`，并扫一遍每个子命令的 `--help`。MCP 工具的 schema 来自 `src/nber_cli/mcp.py` 的类型注解和 docstring；修改该文件后，请与 `docs/en/mcp.md` 和 `docs/zh/mcp.md` 对照。

### 构建与冒烟测试

12. 运行 `uv build`，确认 `dist/*.whl` 和 `dist/*.tar.gz` 都生成。
13. **在临时环境里安装构建产物并跑冒烟测试。** 这能发现 dev 安装里看不到的打包问题：
    ```bash
    uv venv /tmp/nber-cli-smoke
    /tmp/nber-cli-smoke/bin/pip install dist/*.whl
    /tmp/nber-cli-smoke/bin/nber-cli --version
    /tmp/nber-cli-smoke/bin/nber-cli info cache
    /tmp/nber-cli-smoke/bin/nber-cli mcp-server --help
    ```
14. **在发布分支上运行 `git diff --check`。** 这一步能抓到其他检查漏掉的行尾空白与冲突标记。

### 发布

15. 创建并发布 GitHub release。`publish.yml` workflow 会构建包并上传到 PyPI；发布时刻 `pyproject.toml` 里的版本就是被发布的版本——这也是步骤 1 不可省略的原因。

### 可选但推荐

- 把 `git ls-files docs/ | sort` 与 `mkdocs.yml` 声明的导航对照一遍。
- 在大小写敏感的文件系统（Linux CI 即可）上做一次 clean checkout，运行 `uv sync --dev --group docs` 与 `uv run nber-cli --help`，确认没有大小写敏感的路径或导入问题。

## 代码风格

- Python 代码目标版本是 Python 3.11 或更高。
- 变量名遵循 PEP 8，并使用清晰的英文名称。
- 代码注释使用英文。
- CLI 行为保持适合脚本：稳定退出码、可读错误、以及在自动化场景中可用的 JSON 输出。
