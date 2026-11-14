# 扩充最近三个月有修改记录的关联项目

## What was done

- 用户明确选择按 Git 提交或本地文件改动筛选全部项目。将候选发现从会话活动前十改为配置目录内最近三个自然月的全部合格项目，沿用根目录、深度、符号链接与敏感目录边界。
- 覆盖本地各分支提交、暂存、未暂存及未跟踪文件；有项目标识的无 Git 目录按本地文件时间纳入，顶层项目的组件合并。保留已有 ID 与人工字段，较早项目不自动移除。
- 正式关联候选由 12 个增加到 44 个，新增 32 个，已同步到看板项目配置。原有项目人工信息保留，20 份任务 Markdown 在刷新前后逐文件哈希相同，其他看板配置值相同。
- 本机看板接口原仍返回 10 个项目。只读排查确认上游配置监听器拒绝已有 YAML 块列表格式，继续缓存旧配置；重启当前用户的看板服务后接口返回全部 44 个项目。未修改上游监听器。
- 生成入口：`.venv/bin/python -m server.cli refresh`；输入：`config/settings.yaml` 指定目录内的 Git 元数据、文件时间与项目简介；输出：`config/projects.yaml`、`backlog/config.yml`。配置备份与核验证据保存在 `work/verification/project-discovery-2026-10-18/`，文件均存在且非空。

## Testing

- 后端全套 53 项通过，覆盖自然月及起点边界、旧项目、未来时间、超过十个候选、工作树与克隆去重、暂存/未暂存/未跟踪/删除文件、忽略文件、无 Git 项目、组件归属、目录深度及人工字段保留。
- `.venv/bin/python -m scripts.verify_install` 通过：隔离 CLI / MCP 往返、10 个工具、路径边界、正式任务完整性均通过；未向正式库写入测试任务。
- 正式看板 `/api/config` 返回 200，项目名称集合与注册表的 44 个项目完全一致；`/board` 返回 200，正式任务完整性检查通过。证据：`work/verification/project-discovery-2026-10-18/verification.json`。
- 最后对同时间排序用固定提交时间消除秒边界偶发差异，并复测对应项目发现检查。

## Notes

- Changed files：`server/project_registry.py`、`server/main.py`、`tests/test_activity.py`、`tests/test_boundaries.py`、`tests/test_project_modifications.py`、`README.md`、`docs/project-discovery.md`、`docs/storage-and-recovery.md`、`docs/deployment-report.md`、`scripts/build_deployment_report.py`、`config/projects.yaml`、`backlog/config.yml`、本日志及本轮验证目录。
- Rollback：项目与看板配置的修改前副本为验证目录内 `projects-before.yaml` 和 `backlog-config-before.yml`；如需恢复，先停止本机看板并停止其他写入，再按副本恢复对应配置，重新启动服务并核对任务完整性。代码恢复本轮项目发现改动即可回到旧会话前十规则；不回退任务文件。
- 文件修改时间不能替代完整开发历史；删除文件以仍存在的父目录时间近似判断，复制或恢复也可能影响时间证据。普通无项目标识的资料目录不纳入候选。
- 未执行 Git 提交、推送、分支切换或业务项目代码修改。本次没有自动修改任务归属，也没有创建定期刷新任务。
