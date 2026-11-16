---
name: handoff
description: 把本次讨论整理成 ProjectInbox 交接单并提交到看板。用户说「/handoff」「交接」「整理成交接单」「放到看板」时使用。
---

把我们这次讨论整理成 ProjectInbox 交接单：

1. 拿空表：有 Project Inbox 的 MCP 工具就调用 get_handoff_template；没有就运行 `{{CLI}} handoff-template`。
2. 只根据本次对话填写。没聊到、没定下来的写进 open_questions，不要自己编。
3. 提交：MCP 调用 submit_handoff（author 填你自己的名字，例如 claude-code）；没有 MCP 就把交接单存成 YAML 文件，运行 `{{CLI}} submit-handoff --file <文件> --author <你的名字>`。
4. 被退回就按提示补齐，再交。不要绕过检查，也不要直接改看板文件。
5. 成功后告诉我卡片编号，以及它是进了待办，还是因为有待确认问题留在收件箱。然后结束，不要开始写代码。
