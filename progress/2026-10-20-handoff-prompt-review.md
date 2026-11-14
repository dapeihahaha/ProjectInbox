# 2026-10-20 「复制给 Agent」提示词复盘与优化

## What was done

- 扫描本项目上线后的 Agent 会话：Claude Code 10 个、Codex 19 个收到过交接指令（排除本会话与 Project Inbox 自身开发会话后，实际执行交接的约 25 个），并核对看板 79 条任务的状态与 notes。
- 发现的问题（证据见会话与任务 notes）：
  1. 任务正文普遍很短（如 TASK-73 仅一句、无预期行为），Agent 自定验收口径；多次「测试全过、实际走不通」：TASK-41 批量重发流程走不下去、TASK-53 测试样品按自然序而真实数据是字典序、TASK-72 漏 Markdown 表格、TASK-23 表格控件参照错。
  2. 越权 done：TASK-29、TASK-30 在用户只确认 TASK-34 时被一并标为完成。
  3. 22 条任务停在 review，部署后才验收，notes 未写明代码当前在工作区还是已上线。
  4. notes 过长（多数 3–12k 字，堆满命令、镜像哈希），不便人工验收。
  5. 截图常放 /tmp 或工作区，合并清理后失效。
  6. 交接要求建 worktree 与 newn8nbase「建之前先问」冲突，几乎每次多一轮确认。
  7. Claude Code 多次用英文汇报。
- 修改 `server/handoff.py` 生成的指令：分六段；发送即批准建该 worktree；先写「参照物 / 必须看到 / 不能破坏」验收清单；要求按用户操作路径实际走一遍、用贴近真实形状的数据；截图固定存 `work/evidence/<任务编号>/`；notes 先写 10 行内「验收卡」；部署不等于验收、done 只对点名任务执行；全程中文。原有规则（分组、分支命名、blocked、notes 追加、不提交推送部署）保留。
- 更新 `docs/coding-agent-integration.md` 对应说明及可选模板中过时的「标记 done」。

## Testing

- `.venv/bin/python -m pytest -q`：55 passed（`tests/test_handoff.py` 新增验收清单、验收卡、中文、截图目录、部署后保持 review 断言）。
- 正式看板接口 `GET http://127.0.0.1:6420/api/tasks/TASK-73/handoff`：返回新版指令 2669 字符，只读，无需重启服务。
- 未测：真实 Agent 按新指令执行的效果，需在下一批任务中观察。

## Notes

Changed files:
- server/handoff.py
- tests/test_handoff.py
- docs/coding-agent-integration.md

Rollback:
- 备份在 `work/backup-2026-10-20-handoff-prompt/`，将 handoff.py、test_handoff.py、coding-agent-integration.md 复制回原位置即可，无需重启看板。

## 更正（2026-10-21）

- 用户确认 TASK-29、TASK-30 是本人在看板上手动验收并标记完成的。上文「越权 done」一条不成立，状态无需改动。
- 用户补充的真实痛点：Agent 完成后不起本地预览，用户通常合并部署后在生产验收；验收间隔长，回到原会话收尾（含合并推送部署）因缓存过期很耗额度。后续方案待用户选择。
