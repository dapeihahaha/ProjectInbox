import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


def git(path, *args):
    return subprocess.check_output(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-C', str(path), *args], text=True).strip()


def repo(path):
    path.mkdir()
    git(path, 'init', '-q')
    git(path, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-q', '--allow-empty', '-m', 'fixture')
    return path


@pytest.fixture
def system(tmp_path):
    from server.task_manager import TaskManager
    from server.project_registry import Registry
    root = tmp_path / 'inbox'
    root.mkdir()
    (root / 'config').mkdir()
    scan = tmp_path / 'scan'
    scan.mkdir()
    from tests.test_activity import setup_activity
    setup_activity(root, scan)
    projects = [dict(id=x, name=x, aliases=[], keywords=['上传'], description='', path=str(scan/x), worktrees=[], enabled=True, missing=False) for x in ['editr', 'other']]
    (root / 'config/projects.yaml').write_text(yaml.safe_dump({'projects': projects}))
    return TaskManager(root), Registry(root), scan


def test_minimal_bug_and_global_inbox(system):
    manager, _, _ = system
    t = manager.create_task(title='上传异常')
    assert t['type'] == 'bug' and t['priority'] == 'P2' and t['status'] == 'inbox'
    assert t['project'] is None and '/backlog/tasks/' in t['path']
    assert manager.get_task(t['id'])['title'] == '上传异常'
    assert manager.search_tasks(query='上传')[0]['id'] == t['id']
    assert manager.create_task()['title'] == '待整理任务'


def test_update_archive_and_markdown(system):
    manager, _, _ = system
    t = manager.create_task(project_id='editr', title='列表错序', reproduction_steps='选择两个文件')
    changed = manager.update_task(t['id'], status='done', priority='P1', commits=['abc1234'])
    assert changed['created_at'] == t['created_at'] and changed['status'] == 'done'
    moved = manager.update_task(t['id'], project_id=None, status='todo')
    assert moved['project'] is None
    raw = Path(moved['path']).read_text()
    assert yaml.safe_load(raw.split('---', 2)[1])['priority'] == 'p1'
    assert '选择两个文件' in raw and 'abc1234' in raw
    archived = manager.archive_task(t['id'])
    assert archived['id'] == t['id'] and '/backlog/archive/tasks/' in archived['path']
    assert not Path(t['path']).exists()
    assert manager.search_tasks(status='archived')[0]['id'] == t['id']
    with pytest.raises(ValueError, match='归档'):
        manager.update_task(t['id'], status='todo')


def test_duplicates_and_project_scope(system):
    manager, _, _ = system
    t = manager.create_task(project_id='editr', title='上传多个文件顺序异常')
    manager.create_task(project_id='other', title=t['title'])
    found = manager.find_duplicates(title=t['title'], project_id='editr')
    assert len(found) == 1 and found[0]['id'] == t['id']
    assert manager.find_duplicates(title=t['title'], project_id=None) == []


def test_match_ambiguity_explicit_and_unknown(system):
    _, registry, _ = system
    assert registry.match_project('上传错误')['ambiguous']
    assert registry.match_project('editr 上传错误')['candidates'][0]['id'] == 'editr'
    assert registry.match_project('editr 和 other 都有问题')['ambiguous']
    assert registry.match_project('完全无关的话题')['level'] == 'unrecognized'
    assert registry.match_project('myeditrclone')['level'] == 'unrecognized'


def test_discovery_worktree_clone_merge_and_custom_fields(system):
    _, registry, scan = system
    p = repo(scan/'alpha')
    (p/'README.md').write_text('# Alpha\n\nA synthetic local project.\n')
    git(p, 'remote', 'add', 'origin', 'https://user:secret@example.invalid/alpha.git?token=secret')
    git(p, 'worktree', 'add', '-q', '-b', 'fixture-wt', str(scan/'alpha-wt'))
    subprocess.run(['/usr/bin/git', 'clone', '-q', str(p), str(scan/'alpha-copy')], check=True)
    git(scan/'alpha-copy', 'remote', 'set-url', 'origin', 'https://example.invalid/alpha.git')
    ignored=scan/'node_modules'; ignored.mkdir(); repo(ignored/'ignored')
    outside=repo(scan.parent/'outside'); (scan/'linked').symlink_to(outside, target_is_directory=True)
    from tests.test_activity import add_activity
    for path in [p, scan/'alpha-wt', scan/'alpha-copy', ignored/'ignored', scan/'linked']:
        add_activity(registry.root, path)
    result=registry.refresh_projects()
    assert len([x for x in result if x['name']=='alpha']) == 1
    alpha=next(x for x in result if x['name']=='alpha')
    assert str(scan/'alpha-wt') in alpha['worktrees'] and str(scan/'alpha-copy') in alpha['worktrees']
    assert 'synthetic' in alpha['description']
    assert all(x['name'] not in ['ignored','outside'] for x in result)
    regpath=registry.root/'config/projects.yaml'
    assert 'secret' not in regpath.read_text()
    data=yaml.safe_load(regpath.read_text())
    a=next(x for x in data['projects'] if x['id']==alpha['id'])
    a.update(aliases=['自定义'], description='人工简介', keywords=['自定词'], enabled=False)
    regpath.write_text(yaml.safe_dump(data))
    p.rename(scan/'renamed')
    add_activity(registry.root, scan/'renamed', 1700000010000)
    refreshed=registry.refresh_projects()
    a=next(x for x in refreshed if x['id']==alpha['id'])
    assert a['description']=='人工简介' and a['aliases']==['自定义'] and a['keywords']==['自定词'] and not a['enabled']
    assert next(x for x in refreshed if x['id']=='editr')['missing']


@pytest.mark.parametrize('kwargs', [dict(project_id='../outside'),dict(type='oops'),dict(priority='P9'),dict(title='x'*501),dict(tags=['x']*51)])
def test_invalid_inputs(system, kwargs):
    manager, _, _=system
    with pytest.raises(ValueError): manager.create_task(**kwargs)


def test_traversal_symlinks_and_integrity(system, tmp_path):
    manager, _, _=system
    with pytest.raises(ValueError): manager.get_task('../../outside')
    t=manager.create_task(title='../../title is text')
    external=tmp_path/'external'; external.mkdir()
    directory=manager.root/'backlog/tasks'
    directory.rename(tmp_path/'original-tasks')
    directory.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError): manager.create_task(project_id='editr', title='blocked')
    assert not list(external.iterdir())
    directory.unlink()
    (tmp_path/'original-tasks').rename(directory)
    Path(t['path']).write_text('broken')
    result=manager.check_integrity()
    assert not result['ok'] and result['issues']
    with pytest.raises(ValueError): manager.search_tasks()


def test_duplicate_id_detected(system):
    manager, _, _=system
    t=manager.create_task()
    archive=manager.store.mkdir('backlog/archive/tasks')
    (archive/Path(t['path']).name).write_text(Path(t['path']).read_text())
    assert not manager.check_integrity()['ok']
    with pytest.raises(ValueError): manager.update_task(t['id'], title='no ambiguous overwrite')


def _create_many(root):
    from server.task_manager import TaskManager
    manager=TaskManager(Path(root))
    return [manager.create_task(title='concurrent')['id'] for _ in range(8)]


def test_process_concurrency(system):
    manager, _, _=system
    with ProcessPoolExecutor(max_workers=4) as pool:
        groups=list(pool.map(_create_many, [str(manager.root)]*4))
    ids=[x for g in groups for x in g]
    assert len(set(ids))==32 and len(manager.search_tasks(limit=100))==32
    assert manager.check_integrity()['ok']


def test_edit_preserves_extra_markdown(system):
    manager, _, _=system
    t=manager.create_task()
    path=Path(t['path']); path.write_text(path.read_text()+'\n## 手工备注\n保留此处。\n')
    manager.update_task(t['id'], priority='P1')
    assert '保留此处。' in path.read_text()


def test_stdio_cli_roundtrip(system):
    import asyncio
    from server.verify import verify_roundtrip
    manager, _, _=system
    result=asyncio.run(verify_roundtrip(manager.root))
    assert result['ok'] and len(result['tools'])==10
