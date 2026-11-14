# Project Inbox 当前部署结果

生成时间：2026-10-15T08:42:55-07:00（America/Los_Angeles）。本报告取代初次 Python 任务库的验收描述，包含 2026-10-15 中文界面与 Agent 交接更新。

## 已交付

在当前工作区完成 **Cherry 工作智能体 → Project Inbox MCP → Backlog.md 单一 Markdown 任务库 → 本地可编辑看板**。已注册 10 个近期活跃项目，42 项后端与 12 项界面测试通过。正式任务库当前 5 条，完整性检查通过。

- 日常入口：Cherry Studio 2.1.6 → 工作 → Project Inbox，Pi / Qwen38 | New API，无业务工作目录。
- 看板：http://127.0.0.1:6420/board；macOS launchd 用户后台服务，登录后自启、退出后自动恢复；`bin/打开看板.command` 只打开页面。只监听本机，管理方式见 background-service.md。
- 中文看板提供项目、类型、优先级筛选、列表、详情和编辑；五列收件箱 / 待办 / 进行中 / 受阻 / 已完成。状态改变不触发开发。
- 原十个 MCP 工具及 CLI 入口保留，写入交给 Backlog 原生 CLI。任务在 backlog/tasks、completed 和 archive/tasks 中，无双库同步。
- 已保存任务详情或看板勾选多条任务后可「复制给 Agent」，粘贴到一个本机 Agent 会话执行。同项目任务可共用改动与测试，跨项目按目录分组，逐条验收和回填。指令带编号、目录和最新读取命令；未关联项目先确认，复制本身不改变任务状态。剪贴板受限时提供手动复制。
- 使用 Backlog.md 1.53.0-project-inbox.4，上游 commit `fd20f71493fb4eda44b021aa89f257956f17fb71`，包含归档编号保留、中文显示与 Agent 交接补丁；MIT 许可证随运行时保留。
- 切换前旧库任务数 0，完整快照在 `work/legacy-before-backlog-2026-10-14/`；未删除旧 data，未在业务仓库初始化 Backlog，未执行 Git 操作。

## 验证证据

- pytest：42 项通过，0 失败、错误或跳过。包括原项目发现与边界、任务生命周期、CLI/MCP 互操作、原生双向修改、归档查询与只读、完成收起、并发编号、归档编号不复用、字段保留及配置限制。
- 安装脚本：真实 MCP stdio 子进程列出 10 个工具，MCP 创建 → CLI 完成 → MCP 重读与归档通过。写操作在隔离临时目录，正式库只检查。
- 运行时 SHA-256：`b07b3ffb5489c939018d16edcea2d3fca67ca5de0f75dc2ed5ee3729cba7ee4f`；报告生成器已与当前文件核对。
- 原版归档 ID 复用先被回归测试复现，固定源码加补丁后通过；实际构建脚本已运行成功。
- Cherry 界面验收记录属于人工式工具操作观察，不由 pytest 推断：隔离演示库真实调用 match_project → find_duplicates → create_task，产生 TASK-1；看板真实改为 In Progress / P1；随后 Qwen 重新 get_task 报告 in_progress / P1。
- 2026-10-14 隔离验收后恢复 MCP 到正式目录，当时正式库 0 条；2026-10-15 已通过 Cherry 实际保存用户指定的一条真实需求，中文详情核对成功。无匹配项目时保留全局收件箱与待归类标记。
- 中文界面 5 项测试与 TypeScript 类型检查通过；核对类型/批量移动 option value 保持原生值。中文补丁从原始源码回放并逐文件校验 37 项 SHA，当前运行时已重建。
- 交接相关 7 项后端测试与 7 项界面测试；合计 42 项后端与 12 项界面测试通过。编译后的隔离看板已实测单条/多选剪贴板复制、窄屏勾选、键盘勾选、筛选移除隐藏选择、拒绝剪贴板时手动全选、非法/缺失编号拒绝、跨项目分组及未关联项目提示。复制期间无修改请求、任务状态不变；正式任务 Markdown 哈希保持不变。未启动业务 Agent，也未声称完成业务任务。

## 已知限制

- 浏览器拖拽与 Archive Task 原生确认交互未完成端到端验收。归档通过 MCP / CLI 测试，日常可让助手执行；不宣称所有原生界面功能都已测试。
- 常用界面已中文化，项目名与用户正文保留原文；部分第三方编辑器帮助和复杂异常信息可能保留上游原文。关闭浏览器不影响后台看板或 MCP；维护时用 launchctl bootout 停止看板，单独杀进程会被自动拉起。
- 新版没有旧实现的 .history 自动快照，需备份整个 backlog 与 config。归档记录在适配层只读，恢复需单独核对。
- 本地单用户工具，无多用户鉴权、远程协作或云同步。任务在本机，发给模型的上下文仍使用既有 New API 服务的数据路径。
- 关联项目现按配置范围内最近三个月的 Git 提交或本地文件改动发现，纳入全部候选并保留已有记录；详细边界见 [项目发现](project-discovery.md)。轻量查重不是语义检索。
- 搜索默认 50、最多 200 条，无分页。原生页面手工改动配置、项目名称或描述小节时需保持接入约定；不支持随意改流程列后继续沿用旧映射。
- 本机补丁运行时针对 macOS Apple Silicon 构建；不要用未打补丁的官方二进制写库。升级需要重新验证编号、格式和适配测试。

## 生成与复核

生成入口：`.venv/bin/python -m scripts.build_deployment_report`。

输入：config/projects.yaml、当前库完整性、work/batch-agent-handoff/ 的 install.json、backend-tests.xml、build.json、browser-checks.json，以及 work/verification/ 的 backlog-cherry-gui.json、zh-ui.json；输出 docs/deployment-report.md。GUI 记录为独立观察，重新生成报告不会自动重跑界面验收。

操作与重建见 [接入说明](backlog-integration.md)、[Cherry 配置](cherry-studio-setup.md)、[备份恢复](storage-and-recovery.md)。
