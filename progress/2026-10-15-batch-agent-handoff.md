# 2026-10-15 多选任务一次交付给 Agent

## What was done

- 按用户要求支持一次交付多个 Task。在任务看板卡片左上角增加复选框，复用既有选择、范围选择及筛选清理逻辑；「已选 N 项」工具栏增加「复制给 Agent」。卡片正文仍打开详情，复选框及键盘空格不打开详情、不修改状态。
- `project-inbox handoff` 接受一个或多个任务编号，兼容原单条命令；按首次出现顺序去重，按项目分组，生成一段交接指令。明确要求通读任务、分析依赖/重复/冲突，同项目可共用实现和测试，逐条验收、保留旧 notes 并回填状态；不合并删除需求，不因部分完成将整批标记完成。跨项目分别在对应目录工作，未确定归属的组先确认。
- 增加只读批量 GET 端点，保留原单条端点，共用同一生成入口；空选择、非法编号、不存在和归档项拒绝整次交接。错误包含缺失/归档任务编号，便于调整选择，不返回部分指令。
- 单条详情和看板共用复制 Hook。选择改变、关闭详情或卸载后忽略旧请求结果；复制失败继续提供手动全选指令。复制只读任务，不启动 Agent、不改变记录。
- 更新累计交接补丁及六个文件的前后 SHA 校验（含新增 Hook），从原始上游源码重放验证后重建为 `1.53.0-project-inbox.4`，重新加载本机原看板服务。未修改监听、生产配置、任务格式或业务项目。
- 同步使用说明、构建说明、部署报告生成器与当前报告；无 Git 操作，无真实任务执行。正式任务校验快照仅记录路径哈希和内容哈希，不复制标题或正文。

## Testing

- 当前运行时下 `.venv/bin/python -m pytest -q --junitxml=work/batch-agent-handoff/backend-tests.xml`：42 passed；交接相关 7 项，新增同项目去重、跨项目/未关联分组、无效集合拒绝及多参数 CLI 测试。所有任务写入测试均使用隔离合成数据。
- `node_modules/@oven/bun-darwin-aarch64/bin/bun test tests/web-batch-handoff.test.ts tests/web-handoff.test.tsx tests/web-localization.test.ts`：12 pass、0 fail、38 断言。新增勾选精确清单且不开详情、变更选择丢弃旧请求、批量手动复制及清除反馈测试；原单条和中文界面验证继续通过。日志 `work/batch-agent-handoff/frontend-tests.txt`。
- 固定上游源码目录 `tsc --noEmit` 通过，Python compileall 通过；三个补丁从归档重放的最终源码 SHA 与清单一致。构建入口 `scripts.build_backlog` 成功，日志 `work/batch-agent-handoff/build.txt`，新运行时版本和 SHA 记录于 `build.json`。
- 编译后的隔离看板使用 6422 端口、合成任务，实际浏览器勾选并读回剪贴板：同项目两项只有一份目录且只包含所选编号；四项交接有两个明确项目目录和未关联提示；筛选后隐藏项被移除；键盘空格可勾选而不开详情；无修改请求，任务状态保持原值。原单条端点仍返回 200。
- 实测空集合、非法、缺失、归档集合均返回 400 且不返回部分 text，缺失/归档提示含相应编号。此检查先发现 CLI 把错误 JSON 写到 stderr，而旧服务只解析 stdout，导致预期业务错误显示为安装故障 500；核对 CLI 输出后按退出码解析对应流，重建并复测通过。
- 390px 窄屏使用现有「收起侧栏」后，勾选和复制按钮可用；模拟剪贴板拒绝后只读指令可全选复制。第一次窄屏检查因侧栏保持展开且卡片滚动位置导致按钮不在视区，使用已有收起操作并滚动后通过，未修改整体响应式布局。截图 `batch-desktop.png`、`batch-narrow-fallback.png` 已确认非空并目视检查。
- `scripts.verify_install` 成功，原 10 个 MCP 工具与隔离 CLI/MCP 往返通过；正式库完整性通过。正式 6420 的 `/api/version` 为 `.4`、`/board` 返回 200，任务 Markdown 哈希与本轮开始时一致。浏览器观察、安装结果、哈希与生成输入在 `work/batch-agent-handoff/`。
- 按请求范围逐段自查本轮实际差异和验证证据，未委派其他 Agent。当前部署报告入口仍为 `scripts.build_deployment_report`，使用本轮安装结果、测试 XML、构建与浏览器观察生成 `docs/deployment-report.md`，历史 Cherry 证据保留原有适用范围。

## Notes

Changed files：server/handoff.py、server/cli.py、server/task_manager.py（版本标识）、vendor/backlog-source/src/server/index.ts、vendor/backlog-source/src/web/lib/api.ts、vendor/backlog-source/src/web/components/Board.tsx、vendor/backlog-source/src/web/components/TaskCard.tsx、vendor/backlog-source/src/web/components/TaskDetailsModal.tsx、vendor/backlog-source/src/web/hooks/useAgentHandoff.ts（新增）、patches/backlog-1.53.0-agent-handoff.patch、patches/backlog-source.json、scripts/build_backlog.py、scripts/build_deployment_report.py、tests/test_handoff.py、tests/web-batch-handoff.test.ts（新增）、README.md、docs/coding-agent-integration.md、docs/backlog-integration.md、docs/deployment-report.md。生成运行时及证据位于 vendor/backlog-runtime/ 和 work/batch-agent-handoff/。

Rollback：停止本机原看板服务，保留当前运行时后，将 `work/batch-agent-handoff/backlog-runtime-before` 恢复为 `vendor/backlog-runtime/backlog`，再启动原 LaunchAgent，可恢复上一版单条交接界面。需撤回源码时，本轮原文件位于 `work/batch-agent-handoff/before/`，必须同时恢复 Python 交接入口、CLI、上游源码、补丁及构建清单并移走本轮新增 Hook；不能仅回滚 Python 而保留批量界面。无需改动任务数据，不能以旧快照覆盖用户新增记录。

限制：批量勾选入口在任务看板，「全部任务」列表未增加批量操作；本轮未实际发送给 Claude Code/Codex 或执行业务任务。复制内容适用于可访问本机目录的 Agent；Safari 未单独验收，剪贴板受限时使用手动复制。窄屏需使用现有收起侧栏操作。隔离验收进程已停止，正式看板继续运行。
