# 开发

本页说明本地开发、测试、文档和发布准备流程。

更详细的 fixture 与 mock 布局见 [测试基础设施](testing.md)。运行时组件关系见 [系统架构](architecture.md)。

## 仓库结构

```text
.
├── src/nber_cli/          # CLI、MCP、核心逻辑、持久化和迁移
├── src/nber_server/       # 可选的本地 FastAPI 服务
├── desktop/               # React 前端和 Tauri/Rust 外壳
├── scripts/               # Desktop 构建、签名、产物与 smoke 工具
├── tests/                 # Python 和发布工具测试
├── docs/                  # MkDocs 文档源文件
├── .github/workflows/     # CI、发布、Desktop 和文档工作流
└── pyproject.toml         # 包元数据和依赖组
```

本地可以生成 `uv.lock`，但仓库当前会忽略它，不把它作为发布产物。

## 本地环境

```bash
uv sync --dev --extra server --group docs
```

从工作区运行 CLI：

```bash
uv run nber-cli --help
uv run nber-cli search "inflation"
uv run nber-server --help
```

开发 Desktop 时还需要安装 Node 依赖并启动 Tauri：

```bash
cd desktop
npm ci
npm run tauri dev
```

## 测试

```bash
uv run pytest tests
cd desktop
npm run test
```

运行特定测试文件：

```bash
uv run pytest tests/test_cli.py
```

## Lint

```bash
uv run ruff check .
cd desktop
npm run lint
cd src-tauri
cargo check
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
- 在 PR 和 push 上检查 React 前端。
- 在 `v*` tag 或手动触发时构建 macOS、Windows Desktop 安装包。
- 发布 GitHub release 时发布到 PyPI。

普通 PR 的 Desktop 检查目前会运行 Python、TypeScript、前端测试和 Vite build，但不会运行 `cargo check` 或完整 Tauri build。修改 Rust 时需要在本地执行 `cargo check`；完整平台构建只在 tag 或手动触发时运行。

## 发布检查清单

下面的检查项在打 tag 之前必须全部通过。每一项都对应一类历史上确实出过错的问题，跳过其中任何一项都曾经让 regression 漏出去。

### 代码与依赖

1. 同步修改 `pyproject.toml`、`desktop/package.json`、`desktop/package-lock.json`、`desktop/src-tauri/tauri.conf.json`、`desktop/src-tauri/Cargo.toml`、`desktop/src-tauri/Cargo.lock`、`tests/test_release_metadata.py`、Claude/Codex plugin manifest 和 `.claude-plugin/marketplace.json` 的版本。
2. 更新[更新日志](changelog.md)。根目录 `CHANGELOG.md` 与 `docs/en/changelog.md`、`docs/zh/changelog.md` 保持一致。
3. 运行 `uv run pytest tests/test_release_metadata.py -q`，确认所有发布版本一致。当前仓库策略会忽略 `uv.lock`，不要把它加入提交。

### 静态检查

4. 运行 `uv run pytest tests -q`。
5. 运行 `uv run ruff check .`。
6. 运行 `uv run --group docs mkdocs build --strict`。
7. 在 `desktop/` 运行 `npm ci`、`npm run lint`、`npm run test` 和 `npm run build`，然后在 `desktop/src-tauri/` 运行 `cargo check`。

### 跨入口一致性

8. **被跟踪的 plugin 文件和 skill 路径真实存在。** 运行 `git ls-files plugins/ .claude-plugin/ | sort`。在大小写敏感的 checkout 上，正确路径是 `plugins/nber-cli/skills/NBER-CLI/SKILL.md`。
9. **文档里的顶层导入都是真实可用的。** `docs/en/` 与 `docs/zh/` 中的 `from nber_cli import ...` 与 `import nber_cli.x as ...` 示例，必须指向 `nber_cli.__all__` 中的名字，或指向文档登记过的模块级辅助函数。运行下面的命令并确认输出为空：
   ```bash
   uv run python -c "from nber_cli import __all__; import re, pathlib; missing=[]; [missing.append((p, m)) for p in pathlib.Path('docs').rglob('*.md') for m in re.findall(r'(?:from nber_cli import|import nber_cli\.)\s*([A-Za-z0-9_]+)', p.read_text()) if m not in __all__ and not m.startswith('nber_cli.')]; print(missing)"
   ```
10. **公共 `__all__` 中的名字要有文档。** `nber_cli.__all__` 中的每个名字都应该出现在 `docs/en/python-api.md` 和 `docs/zh/python-api.md` 中。将来可以用上面的命令反向找出未登记的名字。
11. **CLI 帮助文本和 MCP 工具 schema 是健康的。** 运行 `uv run nber-cli --help`，并扫一遍每个子命令的 `--help`。MCP 工具的 schema 来自 `src/nber_cli/mcp.py` 的类型注解和 docstring；修改该文件后，请与 `docs/en/mcp.md` 和 `docs/zh/mcp.md` 对照。
12. **HTTP 路由与公开契约一致。** 运行 `uv run pytest tests/test_server.py -q`，并把路由或 schema 变更与 `docs/en/http-api.md`、`docs/zh/http-api.md` 对照。

### 构建与冒烟测试

13. 在 clean checkout 中运行 `uv build`，确认 `dist/*.whl` 和 `dist/*.tar.gz` 都生成。
14. **安装前检查产物内容。** Wheel 必须同时包含 `nber_cli/` 和 `nber_server/`，并包含 `nber_cli/migrations/`。Sdist 不能包含本地数据库或日志、`.dev`、`.agents`、`.conductor`、`.superpowers`、`tmp`、`output`、`node_modules`、Rust `target` 或 sidecar 二进制。Sdist 体积异常时必须停止发布。
    ```bash
    unzip -l dist/*.whl | less
    tar -tzf dist/*.tar.gz | less
    ```
15. **在临时环境安装 wheel，并测试每一个 console entry point。** 这能发现 dev 安装里看不到的漏包问题：
    ```bash
    uv venv /tmp/nber-cli-smoke
    /tmp/nber-cli-smoke/bin/pip install dist/*.whl
    /tmp/nber-cli-smoke/bin/nber-cli --version
    /tmp/nber-cli-smoke/bin/nber-cli info cache
    /tmp/nber-cli-smoke/bin/nber-cli mcp-server --help
    /tmp/nber-cli-smoke/bin/nber-server --help
    /tmp/nber-cli-smoke/bin/nber-sidecar --help
    ```
16. 在每个发布平台运行 Desktop 产物检查和安装包 smoke test，并确认 macOS arm64/x64、Windows x64 产物均已上传。
17. **在发布分支上运行 `git diff --check`。** 这一步能抓到行尾空白与冲突标记。

### 发布

18. 创建 tag 前，确认计划使用的 tag 严格等于 `v` 加 `pyproject.toml` 版本。当前 workflow 会接受任意 `v*` tag，因此这仍是人工发布门禁。
19. Push 对应 tag，等待 Desktop workflow 创建或更新 draft GitHub Release；发布前逐个检查上传产物。
20. Draft 完整后再发布 GitHub Release。发布动作会触发 `publish.yml`，重新构建 wheel 与 sdist 并上传 PyPI。

### 可选但推荐

- 对照 `mkdocs.yml` 检查中英文公开文档；`docs/desktop/` 下的内部文件有意不加入公开导航。
- 在大小写敏感的文件系统（Linux CI 即可）上做一次 clean checkout，运行 `uv sync --dev --group docs` 与 `uv run nber-cli --help`，确认没有大小写敏感的路径或导入问题。

## 代码风格

- Python 代码目标版本是 Python 3.11 或更高。
- 变量名遵循 PEP 8，并使用清晰的英文名称。
- 代码注释使用英文。
- CLI 行为保持适合脚本：稳定退出码、可读错误、以及在自动化场景中可用的 JSON 输出。
