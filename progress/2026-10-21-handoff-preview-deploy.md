# 2026-10-21 交接指令：本地预览、新会话收尾与「完成后直接合并部署」勾选项

## What was done

- 背景：用户通常在合并部署后于生产验收，验收间隔长；回原会话收尾因缓存过期耗额度。
- `server/handoff.py`：
  - 默认指令要求完成后以后台常驻方式启动本地预览，写明地址、要看的页面和停止命令；
  - 指令可在新会话中发送：先读 notes 历史和末尾验收意见，沿用已有工作区返工；
  - 验收卡新增「收尾指令」一行，让新会话不读旧对话即可合并部署；
  - 新参数 `deploy`：生成「合并部署（本次已授权）」一节，全量测试失败、冲突、数据库迁移、生产数据或密钥变更、项目要求审批、无明确部署方式时停下；部署后仍保持 review。
- `server/cli.py`：`handoff --deploy`。
- 看板（运行时升至 `1.53.0-project-inbox.7`）：任务详情和多选工具栏「复制给 Agent」旁新增「完成后直接合并部署」勾选项，默认不勾选，换任务或换选择复位；接口附加 `deploy=1`。改动并入 `patches/backlog-1.53.0-agent-handoff.patch`，更新 `patches/backlog-source.json` 输出 SHA；`server/task_manager.py` 版本字符串同步。
- 文档：README、`docs/backlog-integration.md`、`docs/coding-agent-integration.md`（新增「省额度的收尾方式」）。

## Testing

- `.venv/bin/python -m pytest -q`：57 passed（新增默认指令含本地预览与收尾、勾选后授权部署两项）。
- `bun test tests/web-localization.test.ts tests/web-handoff.test.tsx tests/web-batch-handoff.test.ts`：14 pass / 0 fail（新增详情与多选勾选项两项）。
- `tsc --noEmit`：退出码 0。
- 补丁重放：原始源码 + 中文补丁 + 新交接补丁，6 个文件与当前源码逐字节一致。
- `.venv/bin/python -m scripts.build_backlog`：成功，日志 `work/build/build-deploy-option-2026-10-21.log`；`scripts.verify_install`：ok=true，backend 1.53.0-project-inbox.7。
- 重启正式看板服务后，接口实测：不勾选 3014 字符、含本地预览与收尾指令、无授权；勾选 3709 字符、含「合并部署（本次已授权）」。
- 浏览器实测看板：勾选 TASK-73 → 勾选「完成后直接合并部署」→ 复制，生成文本含授权段；内置浏览器剪贴板受限，按设计显示手动复制框。TASK-73 状态保持 review。
- 未测：真实 Agent 按新指令执行（本地预览常驻、自动合并部署）的效果。

## Notes

Changed files:
- server/handoff.py、server/cli.py、server/task_manager.py
- tests/test_handoff.py、tests/web-handoff.test.tsx、tests/web-batch-handoff.test.ts
- vendor/backlog-source/src/server/index.ts、src/web/lib/api.ts、src/web/hooks/useAgentHandoff.ts、src/web/components/TaskDetailsModal.tsx、src/web/components/Board.tsx
- patches/backlog-1.53.0-agent-handoff.patch、patches/backlog-source.json、vendor/backlog-runtime/backlog（重建）
- README.md、docs/backlog-integration.md、docs/coding-agent-integration.md

Rollback:
- 备份在 `work/backup-2026-10-21-deploy-option/`（handoff.py、cli.py、补丁、清单、旧运行时 backlog、vendor 源码）。停止看板服务后复制回原位置，`server/task_manager.py` 版本字符串改回 `.6`，再 `launchctl kickstart -k gui/501/com.projectinbox.board`。测试文件中本轮新增的测试需一并删除。
