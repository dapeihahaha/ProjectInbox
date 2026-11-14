# Codex、Claude Code、Pi Agent 协作

三个编码 Agent 均可直接读取本机标准 Markdown，无需为它们安装 MCP。本次未改动任何业务项目的 AGENTS.md、CLAUDE.md、Agent 配置或分支。

## 从看板交付执行

任务交接分为“先调研”和“执行”两种模式。默认录入时只保存用户原话，不让录入助手替用户猜测项目现状。任务描述不完整、需要了解现有实现或担心需求偏差时，先在任务详情或看板批量选择中点击 **先调研**，把只读调研指令粘贴到新的 Agent 会话。调研 Agent 只读取项目、测试和运行结果，不创建 worktree、不修改业务项目；它把原始需求、当前状态、证据、事实、假设、待确认问题、执行边界和验收标准追加到原任务 notes，完成后将任务设为 `review`（待验收）。用户确认调研结论后，再点击 **复制给 Agent** 生成执行指令。目标明确、可逆且范围很小的任务可以跳过调研直接执行。

打开已保存任务，在详情顶部点击 **复制给 Agent**，将指令粘贴到 Claude Code、Codex 或 Pi 的本机项目会话后发送。按钮只读取任务并写入剪贴板，不启动 Agent，也不改变任务状态。

一次交付多条任务：在**任务看板**勾选卡片左上角的复选框，在「已选 N 项」工具栏点击 **复制给 Agent**，再粘贴到一个 Agent 会话发送。Ctrl/Cmd 点击卡片和 Shift 范围选择仍可使用；点击卡片正文继续打开详情。取消勾选、清除选择或筛选隐藏的任务不会随其他任务一起交付。复制过程中改变选择会丢弃旧结果，需按新选择重新复制。

同项目任务会归在同组并显示一次目录，要求 Agent 通读全部任务、分析依赖与冲突，再决定实施顺序；可以共用改动和测试解决多条相关需求。跨项目按目录分组；归属不明的组先确认。每条 Task 保留独立验收、notes 和状态，部分完成不能把整批标为完成，不自动合并或删除原任务。某条不存在、已归档或编号无效时，整次生成报错，调整选择后重新复制。

指令自动包含任务编号、当前标题、关联项目目录、工作分支（`task-<编号>`，同组多任务取最小编号，要求在 git worktree 中改动、不直接改主分支）、带绝对路径和 `--home` 的 CLI，以及实施、验证和状态回填要求。2026-10-20 起指令分六段（读取与定位、工作区、验收清单、验证、状态与 notes、最终汇报），要点：发送指令即视为批准创建该 worktree；改代码前为每条任务写 3–6 条「参照物 / 必须看到 / 不能破坏」验收清单并追加到 notes；验证须运行项目已有测试和构建并把命令与实际结果写入 notes，未测部分明确说明，另须按用户操作路径在本地从头到尾实际操作、用贴近真实形状的数据；截图存到本目录 `work/evidence/<任务编号>/`；每次追加 notes 先写不超过 10 行的「验收卡」（改了什么、在哪看及代码位置、清单逐条验证程度、假设与差异、截图）；完成后只设为 review（待验收），不运行 done，合并部署后仍保持 review，只对用户点名「验收通过」的任务执行 done；全程中文。告诉用户在哪个页面怎么看到改动、附前后截图。2026-10-21 起另要求：完成后以后台常驻方式启动本地预览并写明地址和停止命令；验收卡增加「收尾指令」，一句话即可让新会话不读旧对话完成合并部署；指令可在新会话中发送，Agent 先读 notes 中的历史记录和末尾验收意见，沿用已有工作区返工。复制时勾选「完成后直接合并部署」，指令改为授权 Agent 在全部任务验证并设为 review 后按项目约定提交、合并、推送、部署并做健康检查；全量测试失败、合并冲突、数据库迁移、生产数据或密钥变更、项目要求单独审批或没有明确部署方式时停下询问；部署后仍保持 review。CLI 等价参数为 `project-inbox handoff --deploy TASK-ID`；Agent 执行前重新读取最新任务与项目注册表。未关联、未注册或不可用的项目要求先确认归属与目录，不能靠标题猜测。指令适用于能访问本机安装与业务目录的会话。

先保存正在编辑的任务再复制。新建未保存任务、草稿、其他分支与收起记录不显示执行交接按钮。浏览器拒绝剪贴板访问时显示只读指令，点击文本框全选后手动复制；读取失败不会提示复制成功。

命令行也可生成相同指令，输出 JSON 的 `text` 字段：

```bash
project-inbox handoff TASK-ID
project-inbox handoff TASK-ID-1 TASK-ID-2
project-inbox handoff --mode research TASK-ID
project-inbox handoff --mode research TASK-ID-1 TASK-ID-2
```

生成入口为 `server/handoff.py`，输入为最新任务与 `config/projects.yaml`，输出为 CLI JSON 或浏览器剪贴板，不另建交付文档。`execute` 是默认执行模式，`research` 是只读调研模式；调研报告和状态仍经共享 CLI 回填，追加 notes 前先读取并保留旧内容。复制不包含任务正文副本，任务 Markdown 继续作为需求的唯一来源。

## 省额度的收尾方式

原会话间隔较久再回复时，缓存已过期，Agent 需要重读整段对话，收尾成本高。任务记录与工作区已保存全部进度，收尾不必回原会话：

- 验收通过：在看板手动标记完成即可，不需要 Agent。
- 合并部署：开新会话，粘贴该任务 notes 验收卡中的「收尾指令」；也可攒几条已验收的任务一次处理。简单收尾可选较便宜的模型或较低推理强度。
- 验收不通过：在看板任务详情的 notes 末尾写下意见，再点一次「复制给 Agent」粘贴到新会话，Agent 会读历史记录和意见，沿用原工作区返工。
- 想在生产验收、不想回头收尾：复制时勾选「完成后直接合并部署」，由 Agent 在同一会话里一次做完。

## 查询与读取

安装根目录为 `/Users/wangyichuan/selfapp/ProjectInbox/`。先用注册表确定项目 ID，名称和唯一别名也可用于 CLI 的 `--project`：

```bash
/Users/wangyichuan/.local/bin/project-inbox projects
/Users/wangyichuan/.local/bin/project-inbox list --project newn8nbase --status todo
/Users/wangyichuan/.local/bin/project-inbox list --project newn8nbase --status in_progress
/Users/wangyichuan/.local/bin/project-inbox list --project newn8nbase --status blocked
/Users/wangyichuan/.local/bin/project-inbox search "上传" --project newn8nbase
```

按任务 ID 读取时，把 `TASK-ID` 替换成实际完整 ID：

```bash
project-inbox show TASK-ID
```

也可在 `backlog/tasks/`、`backlog/completed/`、`backlog/archive/tasks/` 中读取原生 Markdown。编号为 TASK-1 形式，文件名还包含标题。归档不改变 ID，收起记录通过适配层只读。任务不会按项目分目录；项目是 Front Matter 字段。

搜索默认最多 50 条、最大 200 条；本版没有分页。若返回到达限制，应缩小项目或状态范围，不能宣称已经列出全部。

## 从记录到开发

1. 阅读完整任务和对应业务项目的根目录及子目录约定，确认关联项目、问题、预期与已知复现步骤。缺失信息标为待确认，不臆造。
2. 形成开发计划与可验证的验收条件。任务记录不等于授权修改所有相关系统；按用户当前授权范围实施。
3. 得到实施授权后，将任务标记为 in_progress，完成相关代码改动和必要测试。
4. 在 notes 中记录实际处理结果、验证命令及结果；需要保留原 notes 时先读取后合并，不能把旧内容覆盖掉。
5. 测试完成后标记 review（待验收），不运行 done；用户明确说「验收通过」且任务确为 review 时才运行 done，并在 notes 追加「用户验收通过」。用户说「验收不通过」时设回 in_progress，原文追加意见后继续修改。全局约定见 `~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 的「Project Inbox 验收约定」。仅在用户明确要求 Git 提交且提交实际存在时，把关联 commit 写入 commits；不得编造提交，也不得因本流程自动 commit 或 push。
6. 若受阻，标记 blocked 并记录原因。归档属于用户决定，不自动永久删除文件。

通过共享 CLI 更新，由 Backlog 原生写入；新版不提供旧版 .history 自动备份。以下内容均为合成占位示例，实际执行时替换 ID 和记录：

```bash
project-inbox update TASK-ID --changes '{"status":"in_progress"}'
project-inbox update TASK-ID --changes '{"notes":"处理结果：……；验证：……"}'
project-inbox update TASK-ID --changes '{"status":"review"}'
project-inbox done TASK-ID   # 仅在用户验收通过后
project-inbox update TASK-ID --changes '{"commits":["<实际提交哈希>"]}'
```

直接手工编辑 Markdown 仅用于停止其他写入后的离线整理，保留原生 YAML 字段与 DESCRIPTION / NOTES 区块。日常状态更新优先使用 CLI。原生入口仅使用本工作区 bin/backlog，避免原版二进制复用归档编号；相关补丁见 backlog-integration.md。

## 可选 Agent 指令模板

以下模板仅供复制，本次没有写入任何业务项目：

> 本项目任务收件箱位于 /Users/wangyichuan/selfapp/ProjectInbox。实施前通过 project-inbox 查询并读取用户指定任务；遵守本仓库约定和本轮授权。开始实施时标记 in_progress，完成后记录实际验证并标记 review，用户明确验收通过后才标记 done；受阻时标记 blocked。通过共享 CLI 更新，保留已有内容。不得因任务记录自动修改其他项目、提交或推送代码；commit 只记录实际存在且用户授权创建的结果。
