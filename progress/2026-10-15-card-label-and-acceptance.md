# 验收状态回填与卡片标签显示修复

## What was done

- 用户明确确认 TASK-3、TASK-4、TASK-5 均已验收通过。通过共享 CLI 将 TASK-3 更新为 done，保留原备注并追加人工验收来源；TASK-4、TASK-5 原已完成，未修改。
- 卡片顶部元信息允许换行，类型标签不参与宽度压缩；优先级保留在右上角。修复窄卡片“缺陷”仅显示“缺”的问题。
- 更新现有 Agent 交接补丁、卡片输出 SHA 和运行时版本为 1.53.0-project-inbox.5；本机看板已重建并恢复服务。
- 生成入口：`.venv/bin/python -m scripts.build_backlog`；输入：固定源码归档、依赖锁文件、`patches/backlog-source.json` 及其引用补丁；输出：`vendor/backlog-runtime/backlog`。依赖安装核对无变化。

## Testing

- 修改前浏览器复现：230px 卡片的类型文字可见宽度 11px，完整文字宽度 20px，存在裁切。
- 编译后的正式本机看板：五种类型分别测试 180/230/280/360px 卡片，共 20 场景通过；无类型裁切、无横向溢出，优先级保持顶部对齐。仅临时改变浏览器克隆节点，不写任务。证据：`work/card-label-fix/layout-verification.json`。
- 浏览器 API 核对三个任务均为 Done；状态回填仅更改 TASK-3，原备注保留。
- 前端测试 12 项通过；TypeScript 检查通过；后端测试 42 项通过；隔离安装验证通过。
- 三层补丁从原始归档回放，40 个最终源码 SHA 与清单一致。

## Notes

- Changed files：TASK-3 对应任务记录、`vendor/backlog-source/src/web/components/TaskCard.tsx`、`patches/backlog-1.53.0-agent-handoff.patch`、`patches/backlog-source.json`、`server/task_manager.py` 的版本报告、运行时、`README.md`、`docs/backlog-integration.md`、本日志及本轮 `work/card-label-fix/` 验证记录。
- Rollback：旧运行时保留在 `work/card-label-fix/backlog-before-fix`。先停止本库看板，再恢复旧运行时、卡片三行样式、对应补丁与输出校验、版本报告；恢复服务。任务验收状态独立保留，不回退任务库。
- 未执行 Git 提交、分支切换或业务应用构建安装。本轮仅修改任务面板。
