#!/usr/bin/env python3
"""隔离 stdio/CLI 验证；正式安装只读取注册表和完整性。"""
import asyncio
import json
from pathlib import Path
import tempfile
from server.main import default_root
from server.project_registry import Registry
from server.task_manager import TaskManager
from server.verify import verify_roundtrip


def main():
    root=default_root()
    with tempfile.TemporaryDirectory(prefix='project-inbox-verify-') as tmp:
        result=asyncio.run(verify_roundtrip(Path(tmp)))
    result['installation']=str(root)
    result['registered_projects']=len(Registry(root).list_projects())
    result['integrity']=TaskManager(root).check_integrity()
    result['cherry_gui']='单独验证，不能由此脚本推断'
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['integrity']['ok'] else 1


if __name__=='__main__':
    raise SystemExit(main())
