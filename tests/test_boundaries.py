from pathlib import Path
import subprocess
import sys

import pytest
import yaml
from tests.test_system import repo
from tests.test_activity import setup_activity, add_activity


def test_tied_modification_deterministic_and_missing_status(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    monkeypatch.setenv('GIT_AUTHOR_DATE',stamp)
    monkeypatch.setenv('GIT_COMMITTER_DATE',stamp)
    from server.project_registry import Registry
    scan=tmp_path/'scan';scan.mkdir();root=tmp_path/'app';agent=setup_activity(root,scan)
    for name in ['zeta','alpha']:
        path=repo(scan/name);add_activity(root,path)
    (agent/'pi').rmdir()
    r=Registry(root)
    found=r.refresh_projects()
    assert [p['name'] for p in found]==['alpha','zeta']
    assert [s['source'] for s in r.discovery_report['sources']]==['git','local_files']
    # 目录不再存在才标 missing；不依赖是否还有活动记录。
    (scan/'alpha').rename(tmp_path/'removed')
    found=r.refresh_projects()
    assert next(p for p in found if p['name']=='alpha')['missing']
    assert next(p for p in found if p['name']=='zeta')['missing'] is False


def test_atomic_failure_keeps_original(tmp_path,monkeypatch):
    from server.storage import Storage
    store=Storage(tmp_path/'app')
    store.write('data/task.md','original')
    def fail(*args): raise OSError('synthetic disk error')
    monkeypatch.setattr('server.storage.os.replace',fail)
    with pytest.raises(OSError):store.write('data/task.md','new',replace=True)
    assert store.read('data/task.md')=='original'
    assert not list(store.safe('data').glob('.pending-*'))
    with pytest.raises(FileExistsError):store.write('data/task.md','must not replace')
    assert store.read('data/task.md')=='original'


def test_external_launch_minimal_path(tmp_path):
    from server.verify import verify_roundtrip
    import asyncio
    previous=Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        result=asyncio.run(verify_roundtrip(tmp_path/'app'))
        assert result['ok']
    finally:
        os.chdir(previous)


def test_read_only_activity_database(tmp_path):
    from server.project_registry import Registry
    scan=tmp_path/'scan';scan.mkdir();root=tmp_path/'app';agent=setup_activity(root,scan)
    path=repo(scan/'alpha');add_activity(root,path)
    db=agent/'codex.sqlite';before=db.read_bytes()
    Registry(root).refresh_projects()
    assert db.read_bytes()==before


def test_invalid_update_and_unknown_project_leave_task_unchanged(tmp_path):
    from server.task_manager import TaskManager
    manager=TaskManager(tmp_path/'app');t=manager.create_task()
    before=Path(t['path']).read_bytes()
    for changes in [{'id':'TASK-000001'}, {'status':'invalid'}, {'project_id':'../../bad'}]:
        with pytest.raises(ValueError):manager.update_task(t['id'],**changes)
    assert Path(t['path']).read_bytes()==before
    assert not list((manager.root/'data/.history').rglob('*.md'))


def test_multi_agent_threads_preserve_updates(tmp_path):
    from server.task_manager import TaskManager
    from concurrent.futures import ThreadPoolExecutor
    root=tmp_path/'app';m=TaskManager(root);task=m.create_task()
    def update(changes):
        return TaskManager(root).update_task(task['id'],**changes)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(update,[{'description':'synthetic change'},{'priority':'P1'}]))
    result=m.get_task(task['id'])
    assert result['description']=='synthetic change' and result['priority']=='P1'
    assert m.check_integrity()['ok']


def test_malformed_update_returns_validation_error(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');t=m.create_task()
    with pytest.raises(ValueError):m.update_task(t['id'],status=[])


def test_metadata_size_is_bounded_even_if_file_grows(tmp_path):
    # 所有元信息读取应有硬性字节上限，而不是只依赖预先 stat。
    from server.project_registry import metadata
    p=tmp_path/'project';p.mkdir()
    (p/'README.md').write_text('x'*70000)
    assert metadata(p)==''
