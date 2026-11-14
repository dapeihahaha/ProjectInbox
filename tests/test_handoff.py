"""交接使用合成任务，检查最新定位信息、审批边界和只读行为。"""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import pytest
import yaml
from tests.test_system import system
from server.handoff import agent_handoff


def test_handoff_reads_latest_task_and_project_without_changing_record(system):
    manager, _, scan = system
    task = manager.create_task(project_id='editr', title='Synthetic handoff')
    task = manager.update_task(task['id'], title='Updated synthetic task', notes='Keep synthetic notes')
    before = Path(task['path']).read_bytes()
    result = agent_handoff(manager.root, task['id'])['text']
    assert task['id'] in result and task['title'] in result
    assert str(scan/'editr') in result
    assert '--home ' + shlex.quote(str(manager.root)) in result
    assert 'in_progress' in result and 'blocked' in result
    assert '已有 notes 基础上追加' in result and '不自动提交、推送、部署' in result
    assert '工作分支：'+task['id'].lower() in result and 'git worktree' in result
    assert '"status":"review"' in result and ' done ' not in result
    assert '没有测试或无法构建的部分要明确写「未测」' in result
    assert '在哪个页面、怎么操作能看到改动' in result and '改动前后的截图' in result
    assert '验收清单' in result and '验收卡' in result and '全程用中文' in result
    assert str(manager.root.resolve()/'work/evidence') in result
    assert '部署后任务仍保持 review' in result
    assert Path(task['path']).read_bytes() == before
    assert manager.get_task(task['id'])['status'] == 'todo'


def test_global_or_unavailable_project_requires_confirmation(system):
    manager, _, _ = system
    task = manager.create_task(title='Synthetic unassigned task')
    assert '向我确认项目归属和工作目录' in agent_handoff(manager.root, task['id'])['text']
    task = manager.create_task(project_id='editr', title='Synthetic missing project')
    registry = manager.root/'config/projects.yaml'
    config = yaml.safe_load(registry.read_text())
    config['projects'][0]['missing'] = True
    registry.write_text(yaml.safe_dump(config))
    assert '向我确认项目归属和工作目录' in agent_handoff(manager.root, task['id'])['text']


def test_cli_handoff_and_archived_or_invalid_ids(system):
    manager, _, _ = system
    task = manager.create_task(title='Synthetic CLI handoff')
    command = [sys.executable, '-m', 'server.cli', '--home', str(manager.root), 'handoff', task['id']]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0 and task['id'] in json.loads(result.stdout)['text']
    manager.archive_task(task['id'])
    with pytest.raises(ValueError, match='归档任务只读'):
        agent_handoff(manager.root, task['id'])
    with pytest.raises(ValueError, match='无效任务 ID'):
        agent_handoff(manager.root, '../TASK-1')


def test_same_project_batch_deduplicates_ids_and_preserves_each_task(system):
    manager, _, scan = system
    first = manager.create_task(project_id='editr', title='Synthetic batch first')
    second = manager.create_task(project_id='editr', title='Synthetic batch second')
    before = {t['path']: Path(t['path']).read_bytes() for t in [first, second]}
    text = agent_handoff(manager.root, [second['id'], first['id'], second['id']])['text']
    assert '2 个任务' in text and text.count('项目目录：'+str(scan/'editr')) == 1
    assert text.index(second['title']) < text.index(first['title'])
    assert text.count('工作分支：') == 1 and '工作分支：'+first['id'].lower()+'（' in text
    assert '可以共用代码改动和测试' in text and '独立验收' in text
    assert '不得因部分完成将整批标为完成' in text
    for task in [first, second]:
        assert text.count(' show '+task['id']+'\n') == 1
        assert ' update '+task['id']+' --changes \'{"status":"review"}\'' in text
        assert ' done '+task['id'] not in text
        assert Path(task['path']).read_bytes() == before[task['path']]


def test_batch_groups_projects_and_separates_unknown_project(system):
    manager, _, scan = system
    tasks = [manager.create_task(project_id=project, title='Synthetic grouped '+str(index))
             for index, project in enumerate(['editr', 'other', None])]
    text = agent_handoff(manager.root, [t['id'] for t in tasks])['text']
    assert text.count('关联项目：') == 3
    assert str(scan/'editr') in text and str(scan/'other') in text
    assert '不混用工作目录' in text and '向我确认项目归属和工作目录' in text
    assert '其余明确项目可继续处理' in text


def test_batch_missing_or_archived_task_fails_without_partial_handoff(system):
    manager, _, _ = system
    first = manager.create_task(title='Synthetic batch valid')
    second = manager.create_task(title='Synthetic batch archive')
    manager.archive_task(second['id'])
    for ids, message in [([], '至少选择'), ([first['id'], 'TASK-999'], '任务不存在'),
                         ([first['id'], second['id']], '归档任务只读')]:
        with pytest.raises(ValueError, match=message):
            agent_handoff(manager.root, ids)
    assert manager.get_task(first['id'])['status'] == 'inbox'


def test_cli_accepts_multiple_task_ids(system):
    manager, _, _ = system
    tasks = [manager.create_task(title='Synthetic multi CLI '+str(i)) for i in range(2)]
    result = subprocess.run([sys.executable, '-m', 'server.cli', '--home', str(manager.root), 'handoff',
                             *[t['id'] for t in tasks]], capture_output=True, text=True)
    assert result.returncode == 0
    text = json.loads(result.stdout)['text']
    assert '2 个任务' in text and all(t['id'] in text for t in tasks)


def test_six_task_handoff_reads_the_task_library_once(system, monkeypatch):
    manager, _, _ = system
    tasks = [manager.create_task(title='Synthetic timeout regression '+str(i)) for i in range(6)]
    before = {t['path']: Path(t['path']).read_bytes() for t in tasks}
    scans = 0
    original = type(manager).scan

    def scan_once(self):
        nonlocal scans
        scans += 1
        return original(self)

    monkeypatch.setattr(type(manager), 'scan', scan_once)
    ids = [t['id'] for t in reversed(tasks)]
    text = agent_handoff(manager.root, ids)['text']
    assert '6 个任务：'+'、'.join(ids) in text
    assert scans == 1
    for task in tasks:
        assert text.count(' show '+task['id']+'\n') == 1
        assert Path(task['path']).read_bytes() == before[task['path']]


def test_default_handoff_asks_for_local_preview_and_handover_without_deploy(system):
    manager, _, _ = system
    task = manager.create_task(project_id='editr', title='Synthetic preview')
    text = agent_handoff(manager.root, task['id'])['text']
    assert '启动本地预览' in text and '停止命令' in text
    assert '收尾指令' in text and '新会话' in text and '验收意见' in text
    assert '不自动提交、推送、部署' in text and '本次已授权' not in text


def test_research_handoff_is_read_only_and_returns_to_review(system):
    manager, _, scan = system
    task = manager.create_task(project_id='editr', title='Synthetic research')
    before = Path(task['path']).read_bytes()
    text = agent_handoff(manager.root, task['id'], mode='research')['text']
    assert '先调研' in text and '只读调研' in text
    assert str(scan/'editr') in text
    assert '不创建 worktree，不修改项目文件' in text
    assert '原始需求' in text and '当前实际状态' in text and '已确认事实' in text
    assert '假设与待确认问题' in text and '建议执行边界' in text
    assert 'notes 末尾' in text and '设为待验收' in text
    assert 'git worktree' not in text
    assert '合并部署（本次已授权）' not in text
    assert '"status":"review"' in text
    assert Path(task['path']).read_bytes() == before
    assert manager.get_task(task['id'])['status'] == 'todo'


def test_research_handoff_rejects_deploy_authorization(system):
    manager, _, _ = system
    task = manager.create_task(title='Synthetic research deploy guard')
    with pytest.raises(ValueError, match='调研模式不支持'):
        agent_handoff(manager.root, task['id'], deploy=True, mode='research')


def test_cli_research_mode_is_explicit(system):
    manager, _, _ = system
    task = manager.create_task(title='Synthetic CLI research')
    result = subprocess.run([sys.executable, '-m', 'server.cli', '--home', str(manager.root), 'handoff',
                             '--mode', 'research', task['id']], capture_output=True, text=True)
    assert result.returncode == 0
    assert '只读调研' in json.loads(result.stdout)['text']


def test_deploy_option_authorizes_merge_and_deploy_but_keeps_review(system):
    manager, _, _ = system
    task = manager.create_task(project_id='editr', title='Synthetic deploy')
    before = Path(task['path']).read_bytes()
    text = agent_handoff(manager.root, task['id'], deploy=True)['text']
    assert '合并部署（本次已授权）' in text and '全量测试，失败则不合并' in text
    assert '数据库结构迁移' in text and '部署后任务仍保持 review' in text
    assert '不自动提交、推送、部署' not in text and ' done ' not in text
    command = [sys.executable, '-m', 'server.cli', '--home', str(manager.root), 'handoff', '--deploy', task['id']]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0 and '本次已授权' in json.loads(result.stdout)['text']
    assert Path(task['path']).read_bytes() == before
