# 2026-10-18 待验收（review）状态与验收工作流

## What was done

- 新增状态 `review`（看板「待验收」，紫色），顺序 Inbox → To Do → In Progress → Review → Blocked → Done。
- 交接提示词：按组内最小编号建 `task-<编号>` 分支并在 git worktree 中改动；完成后只设 review、不运行 done；验证须跑已有测试和构建并写入 notes，未测要说明；最终报告须说明在哪个页面怎么看到改动，尽量附前后截图。原有 blocked、notes 追加、不提交/推送/部署规则保留。
- `~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 末尾追加「Project Inbox 验收约定」（仅追加）。
- 重建看板运行时为 `1.53.0-project-inbox.6`。
- 正式库 `backlog/config.yml` 尚未加入 Review，正式看板服务尚未重启（等待用户确认）。

## Testing

- `.venv/bin/python -m pytest -q`：54 passed。
- `bun test tests/web-localization.test.ts tests/web-handoff.test.tsx tests/web-batch-handoff.test.ts`：12 pass / 0 fail。
- `tsc --noEmit -p vendor/backlog-source/tsconfig.json`：退出码 0。
- `.venv/bin/python -m scripts.verify_install`：ok=true，正式库完整性无问题。
- 演练库 `work/verification/drill-review-2026-10-18`：合成任务 TASK-1 走 inbox → in_progress → review → （show 确认 review）→ notes 追加「用户验收通过」→ done；演练看板 6431 端口截图 `1-review-column.jpg`、`2-after-accept-done.jpg`。
- 日志：`work/build/build-review-2026-10-18.log`、`work/build/test-review-2026-10-18.log`。
- 未测：真实 Agent 按新模板创建 worktree 的行为（取决于 Agent 执行，需在下一次真实任务中观察）。

## Notes

Changed files:
- server/backlog.py、server/task_manager.py、server/handoff.py
- vendor/backlog-source/src/web/components/TaskColumn.tsx、TaskList.tsx、src/web/utils/labels-zh.ts
- patches/backlog-1.53.0-review-status.patch（新增）、patches/backlog-source.json、scripts/build_backlog.py
- vendor/backlog-runtime/backlog（重建）
- tests/test_handoff.py、tests/test_backlog.py、tests/web-localization.test.ts
- README.md、docs/coding-agent-integration.md、docs/backlog-integration.md
- ~/.claude/CLAUDE.md、~/.codex/AGENTS.md（末尾追加）

Rollback:
- 备份：`work/backup-2026-10-18-review/`（project.tar.gz、claude-CLAUDE.md、codex-AGENTS.md）。
- 停止看板服务后从 project.tar.gz 解出上述文件覆盖；全局指令文件用备份副本覆盖或删除末尾「Project Inbox 验收约定」一节。

## 追加：正式看板启用（用户确认后）

### What was done
- 正式库 `backlog/config.yml` 的 statuses 在 In Progress 后加入 Review（仅此一行）。
- `launchctl kickstart -k gui/501/com.projectinbox.board` 重启正式看板服务。

### Testing
- `project-inbox check`：ok=true，34 个任务，无问题，backend 1.53.0-project-inbox.6。
- 浏览器打开 http://127.0.0.1:6420/board：六列为 收件箱/待办/进行中/待验收/受阻/已完成，待验收为紫色标签，页脚版本 v1.53.0-project-inbox.6。

### Notes
- Changed files：backlog/config.yml。
- Rollback：用 `work/backup-2026-10-18-review/config.yml.before-review` 覆盖 backlog/config.yml 后重启服务（若已有任务处于 Review，先改回其他状态）。
