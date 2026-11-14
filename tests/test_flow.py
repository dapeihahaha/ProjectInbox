"""完整闭环：交接单 → 领取（程序建工作区）→ 汇报（程序核验）→ 验收 / 退回 / 取消。全部用合成仓库。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import pytest
import yaml
from tests.test_system import system, repo, git
from server.contract import EXAMPLE_HANDOFF, ContractError
from server.flow import Flow
from server.handoff import agent_handoff


def handoff(**changes):
    data = copy.deepcopy(EXAMPLE_HANDOFF)
    data.update(project='editr', verify={'tests': 'test -f feature.txt', 'screenshots': True})
    data.update(changes)
    return data


def report(task_id, **changes):
    data = dict(task=task_id, outcome='done', summary='加了 feature.txt。', acceptance={'A1': {'result': '实际操作验证'}, 'A2': {'result': '实际操作验证', 'screenshot': 'after.png'}, 'A3': {'result': '未测', 'note': '合成仓库没有界面'}, 'A4': '仅自动测试'}, screenshots=['after.png'], where_to_see='合成仓库根目录', deviations='无', visual_summary='flowchart LR\n  领取 --> 提交 --> 汇报')
    data.update(changes)
    return data


def commit(path, name='feature.txt', text='ok\n'):
    (Path(path) / name).write_text(text)
    git(path, 'add', name)
    git(path, '-c', 'user.name=Agent', '-c', 'user.email=agent@example.invalid', 'commit', '-q', '-m', 'agent change ' + name)


@pytest.fixture
def flow(system):
    manager, _, scan = system
    repo(scan / 'editr')
    return Flow(manager.root), scan / 'editr'


def shot(flow, task_id, name='after.png'):
    (flow.evidence_dir(task_id) / name).write_bytes(b'png')


def test_handoff_creates_ready_card_with_acceptance_boxes(flow):
    f, _ = flow
    result = f.submit_handoff(handoff(), 'claude-code')
    task = f.tasks.get_task(result['task_id'])
    assert task['status'] == 'todo' and '交接单' in task['tags'] and task['project'] == 'editr'
    assert [a['text'][:4] for a in task['acceptance']] == ['[A1]', '[A2]', '[A3]', '[A4]'] and not any(a['checked'] for a in task['acceptance'])
    assert '这次不做' in task['plan'] and 'claude-code' in task['plan']
    saved = yaml.safe_load((f.root / f"work/handoffs/{task['id']}.yaml").read_text())
    assert saved['author'] == 'claude-code' and saved['scope']['dont']


def test_handoff_refused_and_open_questions_wait_in_inbox(flow):
    f, _ = flow
    bad = handoff(scope={'do': ['x'], 'dont': []})
    with pytest.raises(ContractError, match='scope.dont'):
        f.submit_handoff(bad, 'codex')
    assert f.tasks.search_tasks() == []
    waiting = f.submit_handoff(handoff(open_questions=['颜色用橙色还是红色？']), 'codex')
    task = f.tasks.get_task(waiting['task_id'])
    assert task['status'] == 'inbox' and '待确认' in task['tags'] and waiting['waiting_for_confirmation']
    refused = f.claim_tasks('codex', [task['id']])
    assert not refused['claimed'] and '只有待办' in refused['refused'][0]['reason']
    again = f.submit_handoff(handoff(task_id=task['id'], open_questions=[]), 'codex')
    task = f.tasks.get_task(again['task_id'])
    assert task['id'] == waiting['task_id'] and task['status'] == 'todo' and '待确认' not in task['tags']


def test_cli_submit_handoff_uses_same_check(flow, tmp_path):
    f, _ = flow
    path = tmp_path / 'h.yaml'
    path.write_text(yaml.safe_dump(handoff(acceptance=EXAMPLE_HANDOFF['acceptance'][:2]), allow_unicode=True))
    base = [sys.executable, '-m', 'server.cli', '--home', str(f.root)]
    bad = subprocess.run(base + ['submit-handoff', '--file', str(path), '--author', 'pi'], capture_output=True, text=True)
    assert bad.returncode == 2 and '至少 3 条' in json.loads(bad.stderr)['error']
    path.write_text(yaml.safe_dump(handoff(), allow_unicode=True))
    good = subprocess.run(base + ['submit-handoff', '--file', str(path), '--author', 'pi'], capture_output=True, text=True)
    assert good.returncode == 0 and json.loads(good.stdout)['status'] == 'todo'


def test_claim_builds_workspace_and_blocks_double_claim(flow):
    f, project = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    plain = f.tasks.create_task(project_id='editr', title='没有交接单的旧卡')
    result = f.claim_tasks('codex', project_id='editr', limit=3)
    assert [c['task_id'] for c in result['claimed']] == [task_id]
    pack = result['claimed'][0]
    workspace = project / '.worktrees' / task_id.lower()
    assert pack['workspace'] == str(workspace.resolve()) and workspace.is_dir()
    assert git(workspace, 'symbolic-ref', '--short', 'HEAD') == task_id.lower()
    assert '/.worktrees/' in (project / '.git/info/exclude').read_text()
    assert git(project, 'status', '--porcelain') == ''
    assert pack['handoff']['acceptance'] and pack['rules'] and set(pack['report_template']['acceptance']) == {'A1', 'A2', 'A3', 'A4'}
    task = f.tasks.get_task(task_id)
    assert task['status'] == 'in_progress' and task['assignee'] == ['@codex'] and 'codex 领取' in task['notes']
    second = f.claim_tasks('claude-code', [task_id, plain['id']])
    reasons = {r['task_id']: r['reason'] for r in second['refused']}
    assert '已被 codex' in reasons[task_id] and '没有合格的交接单' in reasons[plain['id']]
    released = f.release_task(task_id, '缺少数据库权限', 'codex')
    assert released['status'] == 'todo' and workspace.is_dir()
    again = f.claim_tasks('claude-code', [task_id])['claimed'][0]
    assert again['workspace'] == str(workspace.resolve())
    with pytest.raises(ValueError, match='codex'):
        f.release_task(task_id, '不是我领的', 'codex')


def test_report_is_checked_by_program_then_review(flow):
    f, _ = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    workspace = Path(f.claim_tasks('codex', [task_id])['claimed'][0]['workspace'])
    with pytest.raises(ContractError, match='漏了 A2'):
        bad = report(task_id)
        del bad['acceptance']['A2']
        f.submit_report(bad, 'codex')
    first = f.submit_report(report(task_id), 'codex')
    assert not first['accepted'] and any('没有新提交' in p for p in first['problems']) and any('after.png' in p for p in first['problems'])
    commit(workspace, 'other.txt')
    (workspace / 'scratch.txt').write_text('not committed')
    shot(f, task_id)
    second = f.submit_report(report(task_id), 'codex')
    assert not second['accepted'] and any('没提交的改动' in p for p in second['problems'])
    (workspace / 'scratch.txt').unlink()
    third = f.submit_report(report(task_id), 'codex')
    assert not third['accepted'] and any('测试没过' in p for p in third['problems'])
    assert f.tasks.get_task(task_id)['status'] == 'in_progress' and '汇报被拒收' in f.tasks.get_task(task_id)['notes']
    commit(workspace)
    ok = f.submit_report(report(task_id), 'codex')
    assert ok['accepted'] and ok['status'] == 'review'
    task = f.tasks.get_task(task_id)
    assert task['status'] == 'review'
    assert [a['checked'] for a in task['acceptance']] == [True, True, False, True]
    assert '```mermaid' in task['final_summary'] and '程序在工作区重跑' in task['final_summary']
    assert yaml.safe_load((f.root / f'work/reports/{task_id}.yaml').read_text())['test']['passed'] is True


def test_blocked_report_skips_checks(flow):
    f, _ = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    f.claim_tasks('codex', [task_id])
    result = f.submit_report(dict(task=task_id, outcome='blocked', blocked_reason='需要你给测试账号', summary='做到一半', acceptance={a: {'result': '未测', 'note': '受阻'} for a in ['A1', 'A2', 'A3', 'A4']}, where_to_see='无', deviations='无'), 'codex')
    assert result['status'] == 'blocked' and '需要你给测试账号' in f.tasks.get_task(task_id)['final_summary']


def finished(f, workspace_root=None):
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    workspace = Path(f.claim_tasks('codex', [task_id])['claimed'][0]['workspace'])
    commit(workspace)
    shot(f, task_id)
    assert f.submit_report(report(task_id), 'codex')['accepted']
    return task_id, workspace


def test_accept_fast_forwards_and_removes_workspace(flow):
    f, project = flow
    with pytest.raises(ValueError, match='只有待验收'):
        f.accept(f.submit_handoff(handoff(), 'x')['task_id'])
    task_id, workspace = finished(f)
    result = f.accept(task_id)
    assert result['merged'] and result['workspace_removed'] and not workspace.exists()
    assert (project / 'feature.txt').read_text() == 'ok\n'
    assert git(project, 'rev-parse', '--verify', 'refs/heads/' + task_id.lower())
    assert f.tasks.get_task(task_id)['status'] == 'done'


def test_accept_refuses_when_main_moved(flow):
    f, project = flow
    task_id, workspace = finished(f)
    commit(project, 'main-only.txt')
    with pytest.raises(ValueError, match='没法快进合并'):
        f.accept(task_id)
    assert workspace.is_dir() and f.tasks.get_task(task_id)['status'] == 'review'


def test_reject_creates_rework_card_in_same_workspace(flow):
    f, _ = flow
    task_id, workspace = finished(f)
    result = f.reject(task_id, '橙色太刺眼，换成浅一点的')
    old = f.tasks.get_task(task_id)
    assert old['status'] == 'archived' and '已退回' in old['tags']
    new = f.tasks.get_task(result['rework_task'])
    assert new['status'] == 'todo' and new['title'].startswith('返工：') and '橙色太刺眼' in new['plan']
    pack = f.claim_tasks('claude-code', [new['id']])['claimed'][0]
    assert pack['workspace'] == str(workspace.resolve())
    shot(f, new['id'])
    same = f.submit_report(report(new['id']), 'claude-code')
    assert not same['accepted'] and any('返工后没有新的提交' in p for p in same['problems'])
    commit(workspace, 'feature.txt', 'lighter\n')
    assert f.submit_report(report(new['id']), 'claude-code')['accepted']


def test_cancel_removes_clean_workspace_keeps_branch(flow):
    f, project = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    workspace = Path(f.claim_tasks('codex', [task_id])['claimed'][0]['workspace'])
    (workspace / 'wip.txt').write_text('unsaved')
    with pytest.raises(ValueError, match='没提交的改动'):
        f.cancel(task_id, '不做了')
    assert workspace.is_dir() and f.tasks.get_task(task_id)['status'] == 'in_progress'
    (workspace / 'wip.txt').unlink()
    result = f.cancel(task_id, '不做了')
    assert result['workspace_removed'] and not workspace.exists() and result['branch_kept'] == task_id.lower()
    assert f.tasks.get_task(task_id)['status'] == 'archived'


def test_agents_cannot_move_status_or_overwrite_notes(flow):
    f, _ = flow
    task = f.tasks.create_task(project_id='editr', title='旧卡')
    f.tasks.update_task(task['id'], notes='第一条')
    with pytest.raises(ValueError, match='状态不能用 update_task'):
        f.agent_update(task['id'], {'status': 'done'})
    with pytest.raises(ValueError, match='只能往后追加'):
        f.agent_update(task['id'], {'notes': '覆盖'})
    assert f.agent_update(task['id'], {'notes': '第一条\n\n第二条'})['notes'].endswith('第二条')
    base = [sys.executable, '-m', 'server.cli', '--home', str(f.root)]
    done = subprocess.run(base + ['update', task['id'], '--changes', '{"status":"done"}'], capture_output=True, text=True)
    assert done.returncode == 2 and 'accept' in json.loads(done.stderr)['error']
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    f.claim_tasks('codex', [task_id])
    moved = subprocess.run(base + ['update', task_id, '--changes', '{"status":"review"}'], capture_output=True, text=True)
    assert moved.returncode == 2 and '领取中' in json.loads(moved.stderr)['error']
    assert subprocess.run(base + ['done', task_id], capture_output=True, text=True).returncode == 2
    research = subprocess.run(base + ['update', task['id'], '--changes', '{"status":"review"}'], capture_output=True, text=True)
    assert research.returncode == 0


def test_board_copy_gives_short_claim_text_for_handoff_cards(flow):
    f, _ = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    text = agent_handoff(f.root, task_id)['text']
    assert 'claim ' + task_id in text and 'submit-report' in text and 'git worktree' not in text
    assert len(text) < 1500
    legacy = f.tasks.create_task(project_id='editr', title='旧卡')
    assert 'git worktree' in agent_handoff(f.root, legacy['id'])['text']


def test_check_reports_inconsistent_cards(flow):
    f, _ = flow
    task_id = f.submit_handoff(handoff(), 'claude-code')['task_id']
    f.claim_tasks('codex', [task_id])
    f.tasks.update_task(task_id, status='todo')
    assert any('看板上被拖动' in w for w in f.consistency())


def test_install_skill_writes_claude_skill_without_overwriting(tmp_path):
    from scripts.install_skills import install
    home = tmp_path / 'user'
    first = install(['claude', 'codex'], home=tmp_path / 'inbox', user_home=home)
    skill = home / '.claude/skills/handoff/SKILL.md'
    assert [r['action'] for r in first] == ['已写入', '已写入']
    text = skill.read_text()
    assert text.startswith('---\nname: handoff') and 'submit_handoff' in text and '{{CLI}}' not in text and str((tmp_path / 'inbox').resolve()) in text
    assert not (home / '.codex/prompts/handoff.md').read_text().startswith('---')
    assert install(['claude'], home=tmp_path / 'inbox', user_home=home)[0]['action'] == '已是最新'
    skill.write_text('my own skill')
    assert '未覆盖' in install(['claude'], home=tmp_path / 'inbox', user_home=home)[0]['action'] and skill.read_text() == 'my own skill'
