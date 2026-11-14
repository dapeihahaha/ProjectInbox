"""所有任务写入均通过锁定的官方 Backlog.md 可执行程序。"""
import json
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pytest
import yaml


def test_store_is_native_and_updates_are_bidirectional(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app')
    t=m.create_task(title='Synthetic native task',description='synthetic description')
    assert '/backlog/tasks/' in t['path'] and t['id'].startswith('TASK-')
    front=yaml.safe_load(Path(t['path']).read_text().split('---',2)[1])
    assert front['title']=='Synthetic native task' and 'created_date' in front
    native=json.loads(m.backend.run('task','view',t['id'],'--json'))
    assert native['task']['title']==t['title']
    m.backend.run('task','edit',t['id'],'--status=In Progress','--priority=p1')
    assert m.get_task(t['id'])['status']=='in_progress'
    assert m.get_task(t['id'])['priority']=='P1'
    m.update_task(t['id'],title='Updated through wrapper')
    native=json.loads(m.backend.run('task','view',t['id'],'--json'))
    assert native['task']['title']=='Updated through wrapper'
    assert not list((m.root/'data').glob('**/*.md')) if (m.root/'data').exists() else True


def test_archive_read_search_and_no_silent_restore(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');t=m.create_task(title='Synthetic archived issue')
    a=m.archive_task(t['id'])
    assert a['status']=='archived' and '/backlog/archive/tasks/' in a['path']
    assert m.get_task(t['id'])['id']==t['id']
    assert m.search_tasks(query='archived',status='archived')[0]['id']==t['id']
    with pytest.raises(ValueError,match='归档'):m.update_task(t['id'],status='todo')


def test_registry_sync_preserves_native_settings(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');cfg=m.root/'backlog/config.yml'
    before=yaml.safe_load(cfg.read_text());before['labels']=['manual-label'];cfg.write_text(yaml.safe_dump(before))
    from server.backlog import sync_projects
    sync_projects(m.root,[{'id':'demo-id','name':'Demo','enabled':True}])
    after=yaml.safe_load(cfg.read_text())
    assert after['projects']==['Demo'] and after['labels']==['manual-label']
    assert after['filesystem_only'] and not after['auto_commit'] and not after['remote_operations']


def test_legacy_nonempty_store_requires_migration(tmp_path):
    from server.task_manager import TaskManager
    root=tmp_path/'app';(root/'data/inbox').mkdir(parents=True)
    (root/'data/inbox/TASK-000001.md').write_text('synthetic legacy task')
    with pytest.raises(ValueError,match='旧'):TaskManager(root)
    assert not (root/'backlog/config.yml').exists()


def test_native_and_wrapper_concurrent_create_have_unique_ids(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app')
    def create(index):
        if index%2:
            m.backend.run('task','create','--plain','--',f'native-{index}')
        else:m.create_task(title=f'wrapper-{index}')
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(create,range(12)))
    found=m.search_tasks(limit=100)
    assert len(found)==12 and len({t['id'] for t in found})==12
    assert m.check_integrity()['ok']


def test_archiving_done_uses_native_complete_folder(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');t=m.create_task(title='Synthetic verified work')
    m.update_task(t['id'],status='done')
    t=m.archive_task(t['id'])
    assert t['status']=='archived' and '/backlog/completed/' in t['path']
    assert m.search_tasks(status='archived')[0]['id']==t['id']


def test_archived_id_is_never_reused_by_native_creation(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');first=m.create_task(title='Synthetic first')
    m.archive_task(first['id'])
    m.backend.run('task','create','--plain','--','Synthetic next from native')
    assert m.check_integrity()['ok']
    assert {t['id'] for t in m.search_tasks(limit=100)}=={'TASK-1','TASK-2'}


def test_fields_notes_labels_and_literal_option_titles(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app')
    t=m.create_task(title='--synthetic-title',description='d',expected_behavior='expected',reproduction_steps='steps',tags=['synthetic'])
    assert t['title']=='--synthetic-title' and t['expected_behavior']=='expected' and t['reproduction_steps']=='steps'
    t=m.update_task(t['id'],notes='synthetic notes',tags=[],commits=['abc1234'])
    assert t['notes']=='synthetic notes' and t['tags']==[] and t['commits']==['abc1234']


def test_callback_config_is_rejected_without_execution(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app');cfg=m.root/'backlog/config.yml'
    d=yaml.safe_load(cfg.read_text());d['onStatusChange']='must-never-run';cfg.write_text(yaml.safe_dump(d))
    with pytest.raises(ValueError,match='命令'):m.create_task()
    assert not list((m.root/'backlog/tasks').glob('*.md'))


def test_review_status_sits_between_progress_and_done(tmp_path):
    from server.task_manager import TaskManager
    m=TaskManager(tmp_path/'app')
    cfg=yaml.safe_load((m.root/'backlog/config.yml').read_text())
    assert cfg['statuses']==['Inbox','To Do','In Progress','Review','Blocked','Done']
    t=m.create_task(title='Synthetic review flow')
    for status in ['in_progress','review','done']:
        assert m.update_task(t['id'],status=status)['status']==status
    front=yaml.safe_load(Path(m.get_task(t['id'])['path']).read_text().split('---',2)[1])
    assert front['status']=='Done'
    m.update_task(t['id'],status='review')
    assert [x['id'] for x in m.search_tasks(status='review')]==[t['id']]
