# 2026-10-14 Backlog.md 底座与正式看板

## What was done

- 用户选择采用 Backlog.md 底座，授权调整任务格式和 MCP 适配。切换前旧 26 项测试通过，旧任务实际 0 条；备份源码、配置、旧空库与文档到 work/legacy-before-backlog-2026-10-14，未删除原 data。
- 锁定 backlog.md 1.53.0 与 Bun 1.4.3，安装禁用生命周期脚本。上游源码固定 commit，保留 MIT 许可证；增加校验清单、最小归档编号补丁与可重建入口。
- 原版会复用已 archive 的编号，先以回归测试复现重复 ID，再在原生分配器中纳入归档 ID。补丁产物为 1.53.0-project-inbox.1，前端沿用官方源码。
- 改写任务适配，保留原十个 MCP 名称及 CLI，写操作交给 Backlog 原生 CLI。全局 TASK-N 编号、原生项目名、UTC 分钟时间与大小写优先级经过映射。completed/archive 均可查且适配层只读；仅一套 backlog 任务数据。
- 增加 board 命令、固定运行时入口与双击启动器；正式看板在 127.0.0.1:6420，保持无 Git、无回调、无 remote、无自启部署。项目注册表同步十个项目选项，未在业务仓库初始化。
- Cherry 工作智能体继续用 Pi/Qwen38、无业务工作目录，更新工作提示词；隔离演示库中真实完成模型创建、看板编辑、模型重新查询。随后恢复 MCP 到正式工作区，确认已连接和 10 工具，留下空白工作会话。
- 打开正式看板并保留页面，保存截图 work/verification/project-inbox-board.jpg。核对仍为 0 条任务、10 项项目筛选和补丁版本。
- 更新 README、启动需求的当前约定说明、调研决策、接入、恢复、编码协作、Cherry 配置与自动生成报告。停止本轮 6421 评估和 6422 隔离看板，保留 6420 正式看板。

## Testing

- 当前完整测试：35 passed in 23.61s，XML 在 work/verification/backlog-tests.xml。覆盖双向修改、并发原生/包装层编号、归档不复用、归档读取与只读、Done 收起、字段保留、旧非空库阻止切换、回调拒绝以及原有发现/边界。
- scripts.verify_install 成功：真实 stdio 初始化、10 工具、MCP 创建 → CLI 完成 → MCP 重读/归档、路径遍历拒绝；正式库完整性通过且 0 任务。结果 backlog-install.json。
- scripts.build_backlog 已实际构建，版本与源码哈希核对；backlog-build.json 记录二进制 SHA。报告生成器对当前二进制再次核对。
- 实际 UI：Cherry 的 match_project、find_duplicates、create_task 成功卡片；演示 TASK-1 在看板可见，页面改为 In Progress/P1，Qwen 重新读取 in_progress/P1。GUI 观察记录 backlog-cherry-gui.json。
- 浏览器原生 Archive Task 按钮的自动化交互超时，未观察到归档完成；拖拽未完成验收，不能宣称已验证。归档 MCP/CLI 测试已通过。尝试检查 Codex 原生窗口被 Computer Use 权限拒绝，未重试或绕过。
- compileall、JSON/YAML 解析、本地文档链接、交付文件存在且非空检查通过。部署报告已用当前证据重新生成。

## Notes

Changed files：server/backlog.py（新增）、server/task_manager.py、server/main.py、server/cli.py、scripts/build_backlog.py（新增）、scripts/build_deployment_report.py、tests/test_backlog.py（新增）、tests/test_system.py、tests/test_boundaries.py、package.json / package-lock.json、patches/ 下清单与补丁、bin/backlog 和 bin/打开看板.command（新增）、prompts/cherry_studio_work_system_prompt.md、.gitignore、README.md、docs/ 下相关文档。运行数据/产物为 backlog/、node_modules/、vendor/、work/；项目级依赖与缓存不写业务仓库。

Rollback：先停本库 MCP/看板和写入，备份当前 backlog/config；旧实现快照可用于复核。产生新任务后不能直接恢复旧格式程序；先清点并设计导出迁移，由用户确认真实文件覆盖。新版无旧 .history 自动快照，需备份整个 backlog 和 config。本轮未提交、推送或切换分支，当前目录无 Git 元数据。

状态：正式入口已配置，35 项测试与核心实际双向流程通过；GUI 归档确认/拖拽的验证缺口如上。页面英文、任务和助手中文。未更改模型服务、凭证、其他助手或业务仓库内容。
