# 调研交接流程改造

## What was done

- 将 Agent 交接拆为 `execute`（执行）和 `research`（只读调研）两种模式。
- 在任务详情和看板批量选择工具栏增加「先调研」按钮；原「复制给 Agent」继续生成执行指令。
- 调研指令要求保留原始需求，只读调查项目现状，记录证据、事实、假设、待确认问题、执行边界和验收标准，并把报告追加到原任务 notes 后设为 `review`。
- 更新 Cherry Studio 提示词、README、看板接入和 Agent 协作文档，说明先记录、后调研、再执行的使用方式。
- 重建 Backlog.md 运行时为 `1.53.0-project-inbox.8`，新增可重放的调研交接补丁和源码哈希校验。

## Testing

- `.venv/bin/python -m pytest -q`：60 passed。
- `node_modules/@oven/bun-darwin-aarch64/bin/bun test tests`：17 passed。
- `vendor/backlog-source/node_modules/typescript/bin/tsc --noEmit -p vendor/backlog-source/tsconfig.json`：通过。
- 调研补丁在执行交接、待验收补丁之后的源码快照上重放，5 个源码文件哈希全部匹配。
- `.venv/bin/python scripts/build_backlog.py`：成功生成并校验 `vendor/backlog-runtime/backlog`，版本 `1.53.0-project-inbox.8`。
- `.venv/bin/python scripts/verify_install.py`：完整性通过，工具清单和隔离回归通过。
- 重启本机 `com.projectinbox.board` 后，实际请求 `GET /api/tasks/TASK-1/handoff?mode=research` 返回只读调研指令，默认接口返回执行指令；TASK-1 状态仍为 `inbox`。
- 实际打开本机看板的 TASK-1 详情看到「先调研」按钮，点击后显示「已复制 1 项（只读调研指令）」；未触发任务修改。

## Notes

- Changed files：`server/handoff.py`、`server/cli.py`、`server/task_manager.py`、`scripts/build_backlog.py`、`patches/backlog-source.json`、`patches/backlog-1.53.0-research-handoff.patch`、看板源码与前端测试、Cherry/README/协作文档，以及本日志。
- Rollback：停止看板服务后，用上一版 `vendor/backlog-runtime/backlog` 和对应源码补丁清单恢复；任务 Markdown 未迁移、覆盖或删除。
