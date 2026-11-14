# Cherry Studio 接入

## 当前入口

已配置 **Cherry Studio 2.1.6 → 工作 → Project Inbox**，使用 Pi 运行模式、现有 Qwen38 | New API、智能批准、不使用业务工作目录。Project Inbox MCP 已连接，保留 10 个工具。

该智能体的浏览器、文件读写、Shell 内置工具已关闭；保留 MCP 工具发现与编排。它负责记录和管理 Issue；改成“进行中”只改变记录，不授权编码或 Git 操作。提示词为 `prompts/cherry_studio_work_system_prompt.md`。

采用工作入口是按用户选定的日常工作流配置，并利用智能体持续调用 MCP 整理任务；看板在独立本机浏览器运行。旧“对话 → Project Inbox”助手及历史保留，日常使用工作入口即可。

## MCP 参数

| 项目 | 值 |
| --- | --- |
| 名称 / JSON 标识 | Project Inbox / project-inbox |
| 类型 | stdio |
| 命令 | `/Users/wangyichuan/selfapp/ProjectInbox/.venv/bin/python` |
| 参数，每项一行 | `-m`、`server.main`、`--home`、`/Users/wangyichuan/selfapp/ProjectInbox` |
| 工作目录 | 无需设置 |
| 环境变量 | `PROJECT_INBOX_HOME=/Users/wangyichuan/selfapp/ProjectInbox`、`PYTHONUNBUFFERED=1` |

配置文件为 `config/cherry-studio-mcp.json`。启动使用绝对路径，不依赖终端 PATH、uvx 或 npx；MCP 不依赖看板进程。

## 重建配置

1. 设置 → MCP，编辑已有 Project Inbox；缺失时从上述 JSON 导入，避免重复。
2. 确认“已连接”、工具页 10 项，保留其他 MCP 配置。
3. 工作 → 添加智能体，选择 Pi、现有 Qwen38，不指定业务目录。
4. 粘贴工作模式提示词，启用 Project Inbox MCP；关闭浏览器、文件读写、Shell，保留发现/编排 MCP 所需工具。
5. 新建工作会话，发送只读测试并检查实际工具成功卡片。

当前机器已完成，无需再次配置模型服务或凭证。MCP 使用正式工作区；2026-10-15 已按用户要求在工作会话完成一条真实需求的识别、查重和保存，并在中文看板复核。项目无匹配时进入全局收件箱，保留待归类标记。

## 实际验收

此前验证过对话与工作入口的 search_tasks 只读调用。切换 Backlog 后，在独立 `work/verification/cherry-e2e/` 库使用一个合成演示项目完成：

1. 向 Qwen 发送合成 Bug 记录；观察到 match_project、find_duplicates、create_task 三个成功工具卡片，保存 TASK-1。
2. 在隔离看板看到该 Issue，实际修改状态为 In Progress、优先级为 P1。
3. 要求 Qwen 重新调用 get_task，读取到 in_progress / P1，与页面最新值一致。
4. 验收结束后，将 Cherry MCP 的 --home 恢复到正式目录，观察到已连接和 10 个工具，并新建空白会话。正式任务数仍为 0。

浏览器拖拽与原生 Archive Task 确认交互未完整验收；归档通过隔离 MCP / CLI 和自动化测试验证。不要把模型文字声明单独视为写入成功证据。

## 日常使用

在工作会话中随手记录；助手会识别项目并查重，信息不明可留在全局 Inbox。保存成功应返回实际编号。看板由 launchd 登录自启，双击 `bin/打开看板.command` 直接打开页面，地址为 http://127.0.0.1:6420/board。更改任务后让模型重新查询，避免沿用旧上下文。

只读测试：

> 请实际调用 search_tasks，query 使用 __PROJECT_INBOX_READ_ONLY_CHECK__，然后简短报告结果，不创建或修改任务。

日常指令如「记一下某项目的上传 Bug」「列出某项目没解决的问题」「把实际编号的任务改为 P1」「将这条整理成 Codex 开发任务」。记录后需要了解项目现状时，先在看板任务详情点击「先调研」，不要在录入阶段让助手猜测完整规格；调研结论回填并验收后，再点击「复制给 Agent」进入开发。整理成开发任务本身不启动开发。

## 故障处理

- MCP 连接失败：检查设置中的日志、Python 绝对路径和虚拟环境；运行 project-inbox check。
- 包导入失败：在完整安装目录运行 uv sync --locked --reinstall-package project-inbox，再重开 MCP。
- 工具未出现：检查工作智能体已启用该服务和工具开关。
- 看板打不开：按后台服务文档检查 launchctl 状态与日志；正式地址为 6420，6421 为旧评估端口，不重复启动多个服务。
- 数据异常或调用超时：先查询、运行 check，避免重复创建；按恢复文档处理。
- 模型请求失败：保留实际错误，不猜测修改 New API、凭证或其他助手。
