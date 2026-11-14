# 2026-10-18 多选任务交接超时修复（TASK-35）

## What was done

- 复现正式看板只读交接请求：6 条任务约 10 秒后连接被关闭，curl 返回 Empty reply，浏览器对应 Failed to fetch；另一次单条请求也因运行耗时波动被断开。
- 定位到交接生成逐条调用 get_task，每次都重新扫描整个任务库；6 条任务重复全库扫描 6 次。
- 交接生成改为校验所选编号后，一次读取完整任务库，再按原选择顺序提取；复用现有完整性检查和存储锁。保留去重、缺失或归档项整批拒绝及只读行为。
- 修复仅涉及 Python 交接逻辑，新请求即时加载。未重建二进制、重启服务、修改超时或监听配置。TASK-35 用于记录本次修复，验证后设为 review。

## Testing

- 新增 6 条合成任务回归测试，修复前失败（扫描次数 6，预期 1），修复后通过；同时检查倒序选择、每条读取指令及任务文件字节不变。
- `.venv/bin/python -m pytest -q`：55 passed。
- `node_modules/@oven/bun-darwin-aarch64/bin/bun test tests/web-batch-handoff.test.ts tests/web-handoff.test.tsx tests/web-localization.test.ts`：12 pass、0 fail。
- `.venv/bin/python -m scripts.verify_install`：ok=true，正式库 35 条任务完整性检查通过，CLI/MCP 隔离往返通过。
- 正式 6420 端点：单条返回 200，4.041 秒；6 条返回 200，4.644 秒，所选编号读取指令齐全。请求前后全库任务 Markdown 的路径及内容哈希一致。证据 `work/handoff-timeout/http-verification.json` 仅记录数量、状态码、耗时及布尔校验结果，不含真实任务内容。
- 原界面流程由现有 DOM 测试覆盖；未额外手动操作真实浏览器剪贴板。本轮未改前端，无需界面构建。

## Notes

Changed files：server/handoff.py、tests/test_handoff.py、docs/backlog-integration.md、本日志；TASK-35 的状态与 notes 由共享业务层回填。

Rollback：本轮修改前源码位于 `work/handoff-timeout/before/handoff.py` 和 `test_handoff.py`，恢复相应源码即可；回退后会恢复重复扫描问题。无需恢复任务库快照或修改用户任务。本目录无 Git 元数据，无 Git 写操作。
