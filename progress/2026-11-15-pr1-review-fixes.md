# 2026-11-15 PR #1 评审问题修复

## What was done

在 PR #1 的分支 `claude/unified-contract-620zy8` 上修复评审发现的 8 个问题：

1. 汇报和验收都核对工作区是否停在任务分支上；提交放在别的分支会被拒收，避免「标完成但主分支没拿到改动」。
2. 汇报 `blocked` 后领取随之结束（工作区保留），补交接单后可回到待办并重新领取，不再卡死。
3. MCP `archive_task` 改走 `Flow.agent_archive`：带交接单且未完成的卡不能被 agent 归档。
4. 测试超时后读剩余输出最多再等 `DRAIN_SECONDS`（10 秒），脱离进程组的后台进程不会让汇报永久卡住。
5. `accept` 合并完成后删工作区失败时，卡片照常标完成，原因写进结果 `warning` 和 notes。
6. 领取时先改卡片状态再写领取记录，状态写入失败不会留下「待办 + 有效领取」的状态。
7. agent 不能改带交接单卡片的项目，也不能增删「交接单 / 待确认 / 已退回 / 已取消」这几个流程标签。
8. 命令行 `done` 对有工作区的卡等同 `accept --no-merge`（只标完成、不合并），与全局约定「验收通过运行 done」一致；之后仍可用 `accept` 补做合并。

## Testing

- 修复前基线：`uv run pytest -q` 84 passed。
- 修复后：`uv run pytest -q` 91 passed（新增 7 个回归测试覆盖全部 8 条，第 3 和第 7 条合在一个测试里）。
- 用旧版 `checks.py` 跑同样的后台进程场景，确认旧代码会一直等到后台进程退出（5 秒），新代码在限时后返回。
- 未运行前端 `bun test`（本轮没有改前端）。

## Notes

Changed files：`server/checks.py`、`server/workspace.py`、`server/flow.py`、`server/cli.py`、`server/main.py`、`tests/test_flow.py`、`docs/handoff-flow.md`、本日志。

Rollback：未提交前 `git restore` 上述文件即可；提交后 revert 对应提交。
