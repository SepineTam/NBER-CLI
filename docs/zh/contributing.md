# 贡献指南

欢迎贡献。好的贡献会让 CLI 保持小、可预测，并持续服务研究工作流。

## 适合开始的贡献

- 改进文档示例。
- 为 CLI 边界情况添加测试。
- 改进网络和下载失败的错误信息。
- 为 NBER 暴露字段补充 formatter 覆盖。
- 提交包含可复现命令输出的问题。

## 提交 Pull Request 前

运行本地检查：

```bash
uv sync --dev --group docs
uv run pytest tests
uv run ruff check .
uv run --group docs mkdocs build --strict
```

## Pull Request 期望

- 保持变更聚焦。
- 行为变化时添加或更新测试。
- 用户可见行为变化时，同步更新英文和中文文档。
- 避免无关格式化改动。
- 在 PR 描述中说明兼容性影响。

## 文档变更

新增文档页时：

1. 在 `docs/` 下添加英文页面。
2. 在 `docs/zh/` 下添加简体中文页面。
3. 在 `mkdocs.yml` 中注册两个页面。
4. 运行 `uv run --group docs mkdocs build --strict`。

## Issue 报告

有用的问题报告应包含：

- 失败的命令。
- `nber-cli --version` 输出的已安装版本。
- 操作系统和 Python 版本。
- 完整错误输出。
- 同一篇论文是否能在浏览器中访问。
