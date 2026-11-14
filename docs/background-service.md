# macOS 常驻看板服务

2026-10-15 按用户要求将看板改为当前用户的 launchd LaunchAgent。服务随当前用户登录自动启动，进程退出后自动恢复；无需保留终端或打开 Cherry。退出用户登录后停止，机器睡眠时不会持续提供页面。此配置无需管理员权限，不在登录前运行。

## 入口与范围

正式地址：http://127.0.0.1:6420/board。6421 是之前的评估端口，不作为正式入口。

双击 `bin/打开看板.command` 现在只打开页面，不再重复创建服务。Cherry MCP 仍由 Cherry 按需启动 stdio 子进程，和常驻看板共用同一份任务库。服务启动不自动打开浏览器，不调用模型、不刷新业务项目、不执行开发或 Git 操作；仍只监听本机 127.0.0.1。

- Label：`com.projectinbox.board`，当前加载域 `gui/501`。
- 已安装配置：`/Users/wangyichuan/Library/LaunchAgents/com.projectinbox.board.plist`。
- 配置源：工作区 `config/launchagents/com.projectinbox.board.plist`。
- 启动：本工作区 `.venv/bin/python -m server.cli --home /Users/wangyichuan/selfapp/ProjectInbox board --port 6420 --no-open`。
- 日志：`/Users/wangyichuan/Library/Logs/ProjectInbox/board.stdout.log` 和 `board.stderr.log`。日志为本机普通文件，本次未增加自动轮转。
- RunAtLoad / KeepAlive 为 true，重启节流间隔 10 秒，后台进程类型。

## 安装与管理

在本工作区执行 `.venv/bin/python -m scripts.install_service`。安装器检查任务完整性、固定路径与 plist；发现同名不同配置时拒绝覆盖，已正确安装时可重复运行。

查看状态：

```bash
launchctl print gui/501/com.projectinbox.board
```

重启看板：

```bash
launchctl kickstart -k gui/501/com.projectinbox.board
```

维护前停止（只杀进程会被自动拉起）：

```bash
launchctl bootout gui/501/com.projectinbox.board
```

停止后再次启动：

```bash
launchctl bootstrap gui/501 /Users/wangyichuan/Library/LaunchAgents/com.projectinbox.board.plist
```

执行数据恢复、复制一致备份或重建运行时前，先 bootout 看板并停用 Cherry 的该 MCP，完成后再 bootstrap。不要与 `project-inbox board` 手动前台进程同时占用 6420。

若要永久取消自启，先 bootout，再移走该 LaunchAgents plist 保留为备份；不删除任务库。跨用户或移动目录时先核对 UID 和 plist 内的绝对路径，本页命令针对当前机器。

## 验证

已核对 launchctl 为 running、监听仅 127.0.0.1:6420、/board 与 /api/tasks 返回 200；实际终止本服务后，观察 launchd 分配新 PID 并恢复 HTTP。前后任务 Markdown 哈希一致，任务未修改。证据在 `work/verification/launchd-service.json`。

登录自启由 LaunchAgents 注册与 RunAtLoad 配置确认；未为测试强制注销或重启用户电脑。
