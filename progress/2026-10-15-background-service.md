# 2026-10-15 macOS 常驻看板

## What was done

- 按用户“部署成系统常驻服务”的明确要求，将本机看板交给当前用户的 launchd LaunchAgent 管理；无需管理员权限，登录后自启、进程退出后自动恢复，后台启动不打开浏览器。
- Label com.projectinbox.board，加载域 gui/501；配置源 config/launchagents/com.projectinbox.board.plist，安装到 /Users/wangyichuan/Library/LaunchAgents/ 同名文件。
- 使用当前工作区 Python/CLI 及原生运行时，端口固定 6420，仅监听 127.0.0.1。RunAtLoad / KeepAlive=true，ThrottleInterval=10，日志到 ~/Library/Logs/ProjectInbox/。
- 新增 scripts/install_service.py：先检查固定路径和任务完整性；同名配置不同时拒绝覆盖；可重复安装已匹配配置，不重复拉起进程。
- 双击入口改为直接打开正式 URL，避免与后台进程争用端口。保留手动前台 board 命令供维护使用；Cherry MCP 继续由 Cherry 按需启动，未改模型、凭证或任务。
- 更新使用说明、维护/恢复的正确停止方式和部署报告；增加 docs/background-service.md，标明旧 6421 是评估端口。

## Testing

- 源与安装后的 plist 均通过 plutil -lint，逐字节一致；launchctl 状态 running，实际进程父 PID 为 1，独立于 Codex 工具会话。
- lsof 核对仅 127.0.0.1:6420 监听；GET /board、/api/tasks 均 200，正式任务数仍为 1。
- 核对进程身份后向本服务发送 SIGTERM，观察 PID 78806 → 79894，约 1.57 秒恢复 HTTP；launchd 自动恢复实测通过。
- 重复运行安装器后仍为同一正常运行 PID，没有重复进程。
- 前后任务 Markdown 哈希相同。验证记录仅保留路径摘要与内容摘要，不复制业务任务标题或正文；证据 work/verification/launchd-service.json。
- Python compileall、双击脚本 sh -n、文档本地链接检查通过；报告已重新生成。配置部署不增加业务行为，本轮未重跑与配置无关的全部业务测试；此前 35 后端 / 5 中文界面测试结果继续作为原功能证据。
- 登录自启由已安装 LaunchAgents 与 RunAtLoad 配置核对；未强制注销或重启用户机器。

## Notes

Changed files：config/launchagents/com.projectinbox.board.plist（新增）、scripts/install_service.py（新增）、bin/打开看板.command、README.md、docs/background-service.md（新增）、docs/backlog-integration.md、docs/cherry-studio-setup.md、docs/storage-and-recovery.md、scripts/build_deployment_report.py、docs/deployment-report.md。外部安装为 ~/Library/LaunchAgents/com.projectinbox.board.plist 与 ~/Library/Logs/ProjectInbox/；本轮日志与证据在 work/verification/。

Rollback：先 launchctl bootout gui/501/com.projectinbox.board 停止并卸载当前会话服务，再将该 LaunchAgents plist 移到备份位置，即取消下次登录自启；保留任务库。需要手动运行时执行 project-inbox board。维护前必须 bootout，只杀进程会被自动拉起。跨用户或移动安装位置须核对 UID/绝对路径再重新安装。

范围：当前用户登录后的常驻服务；注销或睡眠期间不保证页面可用，不是登录前的 root LaunchDaemon。未开放局域网或新增鉴权、网络代理、定时任务、Git 操作。
