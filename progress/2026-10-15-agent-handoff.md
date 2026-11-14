# 2026-10-15 任务交付给 Agent

## What was done

- 按用户确认的「复制给 Agent → 粘贴到本机 Agent 会话 → 读取最新任务执行 → 回填结果」方案，在已保存任务详情顶部增加复制按钮；沿用原界面样式，按钮组可换行。
- 新增 `project-inbox handoff TASK-ID`，从最新任务和注册表生成指令，含编号、标题、已关联项目目录、带固定安装入口与 `--home` 的 CLI，以及实施、验证、保留已有 notes、状态回填和审批边界。未关联、未注册或不可用项目先确认；归档任务拒绝执行交接。不复制任务正文，不创建交付文档副本。
- 本机只读 GET 端点使用固定 Python 模块和参数数组调用 CLI，不经过 Shell，不调用业务 Agent。复制成功提示粘贴发送；剪贴板拒绝时显示只读可全选指令；读取失败不会误报成功。新建、草稿、其他分支及收起记录不显示执行按钮；编辑中需先保存。
- 增加独立补丁与前后 SHA 校验，运行时重建为 `1.53.0-project-inbox.3`；重建前停止本机看板，随后恢复原 LaunchAgent。未改监听、启动配置、任务字段、MCP 工具和业务项目文件。
- 同步 README、协作说明、构建接入说明及部署报告生成器。未执行 Git 操作，未启动真实业务任务；正式任务 Markdown 前后 SHA 一致。

## Testing

- 当前新运行时下 `.venv/bin/python -m pytest -q --junitxml=work/agent-handoff/backend-tests.xml`：38 passed，包含 3 项交接测试。隔离验证最新标题与项目目录、CLI JSON、保留旧 notes 的交接要求、任务未修改、未关联/缺失项目提示及归档/非法 ID 拒绝。
- `node_modules/@oven/bun-darwin-aarch64/bin/bun test tests/web-handoff.test.tsx tests/web-localization.test.ts`：9 pass、0 fail、25 断言，记录 `work/agent-handoff/frontend-tests.txt`。覆盖复制、剪贴板拒绝回退、读取错误与禁用对象。首次测试因 JSX runtime 在根测试目录不能解析而失败，核对现有测试后改用同样的 React.createElement，未新增依赖。
- 上游源码目录的 `tsc --noEmit` 通过；Python compileall 通过。按 Systematic Debugging 定位测试加载问题；交付前按 Verification Before Completion 核对当前源码、运行时与验证证据。
- 三个补丁依次从固定上游归档重放，中文、交接与编号补丁文件的最终 SHA 均与清单一致。构建入口 `.venv/bin/python -m scripts.build_backlog` 成功，日志 `work/agent-handoff/build.txt`，版本与 SHA 在 `build.json`。
- 编译后运行时在隔离临时目录、6422 端口使用合成任务完成浏览器实测：实际剪贴板内容含编号、项目目录及最新读取命令；复制期间无 POST/PUT/PATCH/DELETE，任务保持 To Do；390px 窄屏按钮可见；模拟剪贴板拒绝后指令可手动全选；非法 DRAFT 编号返回 400；全局任务要求先确认项目。截图 `copy-desktop.png`、`copy-narrow-fallback.png` 已检查非空并目视检查，观察摘要 `browser-checks.json`。
- `.venv/bin/python -m scripts.verify_install` 成功，10 个既有 MCP 工具与隔离 CLI/MCP 往返通过，正式库完整性通过；输出 `work/agent-handoff/install.json`。正式 `/board` 返回 200、`/api/version` 返回新版本；任务 Markdown 哈希与 `task-hashes-before.json` 一致。
- 部署报告入口 `.venv/bin/python -m scripts.build_deployment_report` 使用当前 XML、安装验证、运行时 SHA、交接浏览器观察及已有 Cherry/中文界面证据生成 `docs/deployment-report.md`。历史 Cherry 验收未重新执行，不据此声称真实业务 Agent 已执行任务。

## Notes

Changed files：server/handoff.py（新增）、server/cli.py、server/task_manager.py（运行时版本标识）、vendor/backlog-source/src/server/index.ts、vendor/backlog-source/src/web/lib/api.ts、vendor/backlog-source/src/web/components/TaskDetailsModal.tsx、patches/backlog-1.53.0-agent-handoff.patch（新增）、patches/backlog-source.json、scripts/build_backlog.py、scripts/build_deployment_report.py、tests/test_handoff.py（新增）、tests/web-handoff.test.tsx（新增）、README.md、docs/coding-agent-integration.md、docs/backlog-integration.md、docs/deployment-report.md。生成产物与验证证据位于 vendor/backlog-runtime/、work/agent-handoff/。

Rollback：先停止本机看板，保留当前运行时后，将 `work/agent-handoff/backlog-runtime-before` 恢复为 `vendor/backlog-runtime/backlog`，再启动原 LaunchAgent，即可恢复之前的界面。变更前的三个上游源码文件在 `work/agent-handoff/before/`。回滚不需修改任务或注册表，不能拿旧任务副本覆盖用户的新记录；若还要回滚构建源码，需一并恢复补丁清单和构建脚本，避免新构建重新应用交接补丁。

限制：指令供可访问本机安装与业务目录的 Agent 使用，远端会话需另行传递访问方式。本轮没有新增自动派发、订阅监控或状态触发执行。浏览器剪贴板行为可能受权限影响，已提供手动复制回退；未在 Safari 单独验收。隔离 6422 验收进程已停止，正式 6420 看板继续运行。
