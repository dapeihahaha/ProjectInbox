# Project Inbox 前端与工作入口方案

日期：2026-10-14（America/Los_Angeles）。本轮目标是“随手记录 → 模型整理 → 本地 Issue → 看板查看与管理”。

## 调研结论

推荐优先复用 **Backlog.md**，由它承担任务存储、CLI、MCP 和 Web 看板；Project Inbox 保留本机项目发现、别名匹配及中文整理规则，避免维护两套任务数据。用户已选择路线 A，正式切换已完成；当前实施与编号兼容补丁见 [Backlog 接入说明](backlog-integration.md)。本页保留选型时的调研事实。

已完成独立的入口调整：Cherry Studio 新建 **工作 → Project Inbox** 智能体，Pi 运行模式、现有 Qwen38 模型、智能批准、不使用业务工作目录。启用原 Project Inbox MCP，关闭该新智能体的浏览器、文件读写与 Shell 内置工具，保留发现/编排 MCP 工具所需能力。旧“对话”入口保留，未删除历史。

## 已核对的开源项目

GitHub 数量与状态为调研时快照，不以 star 数单独判断可靠性。

| 项目 | 本轮观察 | 对当前需求的适配 |
| --- | --- | --- |
| [Backlog.md](https://github.com/MrLesk/Backlog.md) | 约 7,034 stars；MIT；最新发行版 v1.53.0；Markdown、MCP、CLI、本地 Web 看板 | 最接近：支持无 Git 模式、统一任务库、项目与类型筛选、自定义优先级和状态，已隔离实测 |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) | 约 28,371 stars；Apache-2.0；官方 README 已明确标注 sunsetting | 工作区、编码 Agent 执行、代码评审一体化可供参考；当前维护状态及自动执行范围不适合作为本次首选 |
| [Plane](https://github.com/makeplane/plane) | 约 60,862 stars；AGPL-3.0；完整 Issue / 项目协作产品，自托管提供 Docker / Kubernetes 路线 | 适合团队化产品管理，当前个人本机 Markdown 流程需承担更多部署与数据适配工作 |
| [kanban-mcp](https://github.com/multidimensionalcats/kanban-mcp) | 83 stars；MIT；SQLite / 可选 MySQL，MCP 与 Web UI | 架构贴近，但以数据库为事实来源；相对 Backlog.md，采用它需改变 Markdown 原生存储要求 |
| [carl-vibe-kanban](https://github.com/LearnPrompt/carl-vibe-kanban) | 1 star；MIT；文件型分支台账与静态 HTML | 有轻量文件渲染思路可参考，但重心是分支/worktree/PR 生命周期，不能直接等同于通用可编辑 Issue 看板 |

来源均为项目官方仓库、官方 README、发行版内容与 npm 包元信息；未将业务项目文件或会话内容发送至 GitHub。

## Backlog.md 发行版隔离验证

未只依据 main 分支文档判断。实际安装 npm **backlog.md@1.53.0** 到 `/tmp/project-inbox-backlog-evaluation/`，使用 `--ignore-scripts`，没有全局安装或修改本项目依赖。

初始化入口：`backlog init "Project Inbox Evaluation" --no-git --defaults --integration-mode none --auto-open-browser false`。注意 `--integration-mode none` 不可再组合 `--agent-instructions none`，发行版会明确拒绝该组合。

样例数据和配置均在 `/tmp/project-inbox-backlog-evaluation/sandbox/`。使用两个合成项目名，未复制真实注册表或任务。配置验证了：

- `projects`：项目筛选；`types`：bug、feature、improvement、investigation、idea。
- `priorities`：P0–P3；界面保留大写显示，Markdown / JSON 中规范化为小写，兼容层需要映射。
- 状态列：Inbox、To Do、In Progress、Blocked、Done；归档通过独立归档操作管理。
- `filesystem_only: true`、`remote_operations: false`、`auto_commit: false`、`check_active_branches: false`。
- CLI 创建合成任务成功，标准 Markdown 文件落盘；JSON 列表成功。
- 官方 MCP stdio 初始化及工具列举成功；task_list 按项目筛选成功，项目参数是数组；task_edit 更新状态成功。
- Web 看板启动在 **127.0.0.1:6421**；界面观察到任务从 Inbox 移到 In Progress，证明 CLI / MCP / Web 共用数据。
- 实际页面已核对项目、类型、优先级筛选与五个状态列。拖拽、完整表单编辑和归档的逐项交互尚未验收，不把官方功能描述当作本轮全部测试通过。

评估看板当时使用 6421，验收结束后停止；当前正式入口为 [本机看板](http://127.0.0.1:6420/board)，只监听回环地址，按需启动。

## 两条可选实施路线

### A. 采用 Backlog.md 作为底座（已选择并实施）

将正式看板和任务库集中放在当前 ProjectInbox 工作区，使用 filesystem-only 模式；不在十个业务仓库逐一 init，也不自动 Git 提交或访问 remote。

- Cherry 工作智能体负责自然语言拆分、分类、查重提示和确认规则。
- 项目注册表继续负责 Agent 活跃度发现、稳定标识、路径、别名与简介；仅把所需项目值同步到任务系统。
- Backlog.md 负责唯一一份任务文件、原生 MCP / CLI 和可编辑看板；全局 inbox 对应未关联项目的任务及 Inbox 状态。
- Project Inbox 保留必要的发现/匹配适配，不并行维护另一套任务写入逻辑。
- 看板提供项目/类型/优先级筛选、任务详情与编辑、状态流转、归档；之后单独验证“Cherry 新建 → 看板可见 → 看板修改 → Cherry 查询”。
- 打开看板时启动本地回环服务，不安装系统级常驻守护进程；退出时可停止，不开放局域网。
- 看板中改为进行中只改变记录状态，不启动编码 Agent 或执行业务仓库脚本。

需要核实和适配的差异包括 ID、任务路径、UTC 时间格式、优先级大小写、状态、归档语义与 MCP 工具名。不能把现有文件直接交给新程序假定兼容。切换前先清点与备份，保留旧 ID 映射和原始文件；不覆盖或删除旧库。现有 MCP/CLI 是否保留兼容入口，应在实施方案中明确。

### B. 保留当前 Python 底座，单独补前端

任务文件、MCP 与 CLI 接口保持现有约定，通过本机 HTTP 层调用共享 TaskManager，增加列表/看板、筛选、详情、编辑及状态流转；界面交互参考 Backlog.md 与常见 Issue 产品。

优点是兼容现有任务格式、无需切换事实来源；代价是需要自行维护前端、本机 Web 接口及浏览器写入保护，也要自行承担后续看板功能维护。采用此路线时不再把 Backlog.md 作为运行依赖。

## 实施结果

已采用路线 A，保留 Python 项目发现与十个 MCP 兼容工具，任务写入交给 Backlog 原生 CLI。正式库切换前任务为 0，原 data 和完整实现快照保留；没有真实任务迁移或删除。

正式看板、启动器、工作入口已接通；隔离库中完成 Cherry 新建 → 看板可见 → 页面更改状态与优先级 → Cherry 重新读取。35 项自动化测试通过。原版归档 ID 复用行为已通过固定版本源码的最小补丁处理；拖拽与页面归档确认尚未完整验收。见 [部署结果](deployment-report.md)。
