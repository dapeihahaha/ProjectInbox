# 2026-10-15 中文界面与 Cherry 实际记录

## What was done

- 按用户要求将常用看板界面改为中文：导航、状态列、任务类型、筛选、详情、常用按钮、列表、设置和相对日期。沿用原布局，无新增翻译服务或运行依赖；项目名、用户正文、任务编号、持久化状态和类型保持原值。
- 增加 patches/backlog-1.53.0-zh-cn.patch，覆盖 37 个上游界面文件，包含独立的枚举显示标签函数。保留之前的编号补丁，运行时更新为 1.53.0-project-inbox.2。
- 扩展固定源码清单与构建脚本：验证中文补丁前后逐文件 SHA；先编译 .building、验证版本再原子替换。完整重建并重启本轮拥有的 6420 看板，未停止其他业务服务。
- 通过 Cherry Studio「工作 → Project Inbox」实际输入用户指定需求。观察 match_project、list_projects、find_duplicates、search_tasks 及最终 create_task 成功卡片；首次 create_task 有错误，模型随后调整调用成功。未把失败卡片当作保存成功证据。
- 正式库得到 TASK-1，一条真实需求；项目未匹配时进入全局收件箱并标记待归类。两种方案保留待定，未代选实现方案或启动开发。业务正文仅保存在任务库，不复制进日志或测试夹具。
- 在中文看板打开 TASK-1，核对内容与类型显示正确，保留详情页。截图位于 work/verification/project-inbox-zh-task.jpg，GUI 记录 zh-ui.json。
- 更新 README、Backlog 接入、Cherry 配置、部署报告生成器和当前报告。历史进度记录未修改，无 Git 操作。

## Testing

- Python 后端：35 passed in 13.69s，work/verification/backlog-tests.xml。
- 前端：5 pass、0 fail、13 断言，入口为原生 Bun test tests/web-localization.test.ts；日志 work/localization/tests.txt。
- 回归检查曾发现中文标签误入详情类型与批量移动 option 的 value。先补测试得到 3 pass / 2 fail，修正标签使用位置后 5 项全部通过；同时恢复传入状态列组件与样式逻辑的 canonical 值。未通过界面保存错误值，正式任务原生 feature / Inbox 保持不变。
- TypeScript：固定源码 tsc --noEmit 通过，日志 work/localization/typecheck.txt；Python compileall 通过。
- 中文补丁从未改动的源码回放，37 个补丁文件的生成结果与清单 SHA 全部一致，原有归档 ID 补丁仍通过后端回归。
- scripts.verify_install 成功，正式库完整性通过且 tasks=1；隔离 MCP/CLI 互操作通过。最新运行时 SHA 写入 backlog-build.json，部署报告生成器与实际文件再次核对。
- 实际界面观察：中文导航、五个状态列、中文类型、今天、详情按钮和任务内容；详情类型选中“功能需求”，原始 value 为 feature。没有通过测试更改真实任务状态或优先级。

## Notes

Changed files：patches/backlog-1.53.0-zh-cn.patch（新增）、patches/backlog-source.json、scripts/build_backlog.py、server/task_manager.py（版本标识）、tests/web-localization.test.ts（新增）、README.md、docs/backlog-integration.md、docs/cherry-studio-setup.md、scripts/build_deployment_report.py、docs/deployment-report.md。生成产物与证据在 vendor/、work/localization/ 和 work/verification/；正式需求仅写入 backlog/。

Rollback：中文修改前的界面源码保留在 work/localization/web-before，旧运行时为 work/localization/backlog-runtime-before-zh。需回滚时先停止本看板，核对并备份当前运行时与 backlog/config；旧运行时保留编号补丁，可读取当前同格式任务。本次没有覆盖或迁移真实任务文件，回滚界面不应移除本次用户授权创建的需求。

限制：部分第三方编辑器帮助与复杂异常消息可能保留上游原文。页面拖拽与归档确认仍未完整端到端验收，沿用上轮报告边界。未新增 Hub 注册项或擅自绑定其他本地项目。
