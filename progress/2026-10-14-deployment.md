# Project Inbox 本机部署

## What was done

- 用户明确恢复执行后，在当前工作区完成任务存储、项目注册表、三类 Agent 活动元数据适配、十个 stdio MCP 工具及共享 CLI。
- 按三个授权根目录内可用会话活动选择首次前十，未全量遍历业务目录；注册表保存于 config/projects.yaml。保留人工字段、已有项目和 missing 状态。
- 使用工作区 .venv 与 uv.lock 锁定安装；创建工作区 bin 启动脚本，并添加 ~/.local/bin/project-inbox 指向本工作区的符号链接；未覆盖既有同名入口。
- 在 Cherry Studio 2.1.6 通过界面导入 Project Inbox MCP，创建同名对话助手，粘贴完整中文提示词并启用 MCP；沿用现有 Qwen38 / New API 服务。
- 编写 README、Cherry 接入、编码 Agent 协作、数据恢复和生成式部署报告；启动文档状态同步为已恢复执行。
- 按代码审查要求在本会话串行自查，无子代理、业务项目改动、Agent 配置改动或 Git 操作。

## Testing

- `.venv/bin/python -m pytest -q --junitxml=work/verification/tests.xml`：26 passed，0 失败 / 错误。
- `.venv/bin/python -m scripts.verify_install`：真实 stdio 初始化与工具列举、MCP 创建 → CLI 完成 → MCP 读取 / 归档通过；写操作在临时目录，正式库检查通过且 0 条任务。
- 从其他目录及最小 PATH 验证实际包导入、CLI 与 MCP 启动。首次 Cherry 连接曾因早于代码创建的 editable 安装缺少映射而失败；重新安装当前包后连接通过。
- MCP SDK 返回 ListToolsResult 与非结构化 JSON 文本的实际结构已核对，验证代码据此修正；预期的非法 ID 改用 SDK ToolError 返回明确错误。
- 活跃度排序、去重、路径与符号链接排除、元数据缺失、人工字段保留、掉出前十保留、只读索引均有隔离验证。
- 并发创建与并发更新、原子写入失败保留原文、任务读写生命周期、重复检查、非法字段、损坏与重复 ID 检测通过。
- Cherry Studio 实际 Qwen38 调用 search_tasks，工具卡片显示成功，参数为合成 smoke 查询，响应为空；只读界面测试未创建正式任务。写入流程在隔离 MCP / CLI 测试中验证。
- 文档及交付物存在、非空、内部链接、配置语法和 Python 编译检查通过。报告入口为 `scripts/build_deployment_report.py`，输入为注册表及 work/verification 下验收证据，输出为 docs/deployment-report.md。

## Notes

- Changed files：server/、scripts/、tests/、bin/、config/settings.yaml、config/projects.yaml（生成）、config/cherry-studio-mcp.json（生成）、prompts/cherry_studio_system_prompt.md、pyproject.toml、uv.lock、.python-version、.gitignore、README.md、docs/ 中接入 / 协作 / 恢复 / 部署结果文档及启动文档状态、本日志；运行数据目录与验收证据仅在本机。
- 外部安装项：~/.local/bin/project-inbox 符号链接；Cherry Studio 中新增的 Project Inbox MCP、对话助手及一条只读验收对话。
- Rollback：先在 Cherry 中停用本次新增的 Project Inbox MCP；保留 data/ 与 config/ 备份，再决定移除新增助手和配置。CLI 链接可单独移除，不影响业务仓库。工作区内本轮新增文件可按以上清单移走，保留最初启动文档及此前日志；不使用批量破坏性命令。
- 限制：Claude 仅当前会话元数据，Pi 活动依据 session 文件最后写入时间，非 Git 项目不纳入；文本相似度非语义检索；查询最大 200 条且无分页；跨目录移动极端中断需人工恢复；历史备份不自动清理。
- 最终界面复核：已关闭并重新开启本次新增的 MCP，日志显示最终代码版本连接成功，仍识别 10 个工具；返回 Project Inbox 助手并打开空白新对话，便于直接使用。原只读验收对话保留。
