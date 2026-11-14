# 前端调研与 Cherry 工作入口

## What was done

- 按用户要求通过 agent-reach 的 gh 后端查询官方 GitHub 仓库、README、发行版和 npm 元信息，比较 Backlog.md、Vibe Kanban、Plane、kanban-mcp 等方案。
- 在 /tmp/project-inbox-backlog-evaluation 安装 backlog.md@1.53.0（非全局，ignore-scripts），初始化无 Git、无 Agent 配置改写的隔离样例，启动仅监听 127.0.0.1:6421 的临时评估看板。
- Cherry Studio 新建“工作 → Project Inbox”，使用 Pi 运行模式与现有 Qwen38，启用原 MCP；关闭新智能体的浏览器、文件读写与 Shell，旧对话入口保留。
- 输出 docs/2026-10-14-frontend-research.md，包含来源链接、真实验证、两条路线、推荐与切换影响；同步 README、接入说明，保存工作智能体提示词。
- 已就成熟底座复用或保留当前底座自建前端发起一个方案选择。未实施正式任务库迁移或替换 MCP。

## Testing

- 实际 npm 包及二进制版本为 1.53.0；CLI 合成任务创建、JSON 项目筛选结果、类型与 P0–P3 配置有效。
- 官方 MCP 真实 stdio 初始化、工具列举、task_list 按数组项目参数筛选、task_edit 状态更新成功。初次传字符串项目参数被 schema 拒绝，按实际 schema 修正后通过。
- 评估看板真实显示 Inbox / To Do / In Progress / Blocked / Done、项目/类型/优先级筛选；MCP 改为 In Progress 后界面同步显示。尚未逐项测试拖拽、全部编辑表单和归档。
- Cherry 工作入口实际 search_tasks 只读请求成功，已核对成功工具卡片；正式 Project Inbox check 通过，任务数为 0。
- 本轮不修改 Python 业务代码，复用此前 26 项测试证据；对新文档、提示词、链接和隔离配置进行静态检查。

## Notes

- Changed files：README.md、docs/cherry-studio-setup.md、docs/2026-10-14-frontend-research.md、prompts/cherry_studio_work_system_prompt.md、本日志；其余文档仅补充新阶段状态指引。
- 外部变更：新增 Cherry 工作智能体与只读验收会话；/tmp 下的评估包、合成 Markdown 与回环 Web 进程。未替换正式数据、未改 Agent 全局配置、未修改业务仓库或执行 Git 操作。
- Rollback：可停止本次评估进程（本轮启动时 PID 76846，后续必须核对进程身份），保留或移走 /tmp 下样例；Cherry 中停用新增工作智能体即可继续使用旧对话入口。正式任务库无需回滚。
- 推荐采用 Backlog.md，但该路线涉及任务格式、ID、时区、归档语义及 MCP 接口适配，需用户确认核心方案后再实施；不把临时演示当成正式前端上线。
