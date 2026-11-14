"""使用合成项目验证修改记录筛选，不接触正式业务目录。"""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import pytest
import yaml

from server.project_registry import Registry, three_months_ago
from tests.test_system import git


@pytest.fixture
def discovery(tmp_path, monkeypatch):
    import server.project_registry as module
    now = datetime(2026, 10, 18, 12, tzinfo=ZoneInfo('America/Los_Angeles'))

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    monkeypatch.setattr(module, 'datetime', FixedDateTime)
    scan = tmp_path/'scan'
    scan.mkdir()
    root = tmp_path/'app'
    (root/'config').mkdir(parents=True)
    (root/'config/settings.yaml').write_text(yaml.safe_dump({
        'scan_roots': [str(scan)], 'max_depth': 4, 'timezone': 'America/Los_Angeles',
    }))
    return Registry(root), scan, now


def commit(path, stamp):
    git(path, 'add', 'source.txt')
    subprocess.run(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-C', str(path),
                    '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-q', '-m', 'synthetic fixture'], check=True,
                   env={**os.environ, 'GIT_AUTHOR_DATE': stamp, 'GIT_COMMITTER_DATE': stamp})


def make_repo(path, stamp='2026-01-01T12:00:00Z'):
    path.mkdir(parents=True)
    git(path, 'init', '-q')
    (path/'source.txt').write_text('synthetic original\n')
    commit(path, stamp)
    return path


def touch_at(path, stamp):
    value = datetime.fromisoformat(stamp).timestamp()
    os.utime(path, (value, value))


def test_calendar_month_boundary_and_old_session_does_not_count(discovery):
    registry, scan, now = discovery
    cutoff = three_months_ago(now).astimezone(timezone.utc)
    make_repo(scan/'at-boundary', cutoff.isoformat())
    make_repo(scan/'too-old', '2026-07-18T18:59:59Z')
    make_repo(scan/'future', '2026-11-01T00:00:00Z')
    found = registry.refresh_projects()
    assert [p['name'] for p in found] == ['at-boundary']
    assert registry.discovery_report['cutoff'] == '2026-07-18T19:00:00+00:00'
    assert three_months_ago(datetime(2026, 5, 31)).isoformat() == '2026-02-28T00:00:00'


@pytest.mark.parametrize('kind', ['unstaged', 'staged', 'untracked', 'deleted', 'dotfile'])
def test_recent_local_changes_without_recent_commit(discovery, kind):
    registry, scan, _ = discovery
    path = make_repo(scan/kind)
    changed = path/'source.txt'
    if kind == 'untracked':
        changed = path/'new.txt'
    elif kind == 'dotfile':
        changed = path/'.gitignore'
    if kind == 'deleted':
        changed.unlink()
        touch_at(path, '2026-10-01T12:00:00Z')
    else:
        changed.write_text('synthetic changed\n')
        touch_at(changed, '2026-10-01T12:00:00Z')
        if kind == 'staged':
            git(path, 'add', 'source.txt')
    found = registry.refresh_projects()
    assert [p['name'] for p in found] == [kind]
    assert found[0]['activity_sources'] == ['local_files']


def test_old_dirty_and_ignored_files_do_not_count(discovery):
    registry, scan, _ = discovery
    path = make_repo(scan/'old-dirty')
    (path/'source.txt').write_text('synthetic changed\n')
    touch_at(path/'source.txt', '2026-01-02T00:00:00Z')
    (path/'.git/info/exclude').write_text('generated.txt\n')
    (path/'generated.txt').write_text('synthetic ignored\n')
    touch_at(path/'generated.txt', '2026-10-01T00:00:00Z')
    assert registry.refresh_projects() == []


def test_non_git_project_and_excluded_generated_files(discovery):
    registry, scan, _ = discovery
    for name in ['source-change', 'only-generated']:
        path = scan/name
        path.mkdir()
        (path/'pyproject.toml').write_text('[project]\nname="synthetic"\n')
        touch_at(path/'pyproject.toml', '2026-01-01T00:00:00Z')
        source = path/'module.py' if name == 'source-change' else path/'node_modules/module.js'
        source.parent.mkdir(exist_ok=True)
        source.write_text('# synthetic\n')
        touch_at(source, '2026-10-01T00:00:00Z')
    found = registry.refresh_projects()
    assert [p['name'] for p in found] == ['source-change']
    assert found[0]['remotes'] == []


def test_stale_existing_project_and_manual_fields_are_preserved(discovery):
    registry, scan, _ = discovery
    path = make_repo(scan/'old-project')
    old = {'id': 'existing', 'name': '人工名称', 'path': str(path),
           'aliases': ['别名'], 'keywords': ['自定'], 'description': '人工简介', 'enabled': False}
    (registry.root/'config/projects.yaml').write_text(yaml.safe_dump({'projects': [old]}))
    assert registry.refresh_projects() == [dict(old, missing=False)]


def test_nested_repositories_and_depth_boundary(discovery):
    registry, scan, _ = discovery
    make_repo(scan/'outer', '2026-10-01T00:00:00Z')
    make_repo(scan/'outer/nested', '2026-10-01T00:00:00Z')
    make_repo(scan/'one/two/three/four/too-deep', '2026-10-01T00:00:00Z')
    assert {p['name'] for p in registry.refresh_projects()} == {'outer', 'nested'}


def test_non_git_components_use_the_parent_project_name(discovery):
    registry, scan, _ = discovery
    for component in ['api', 'desktop']:
        path = scan/'synthetic-app'/component
        path.mkdir(parents=True)
        (path/'package.json').write_text('{"description":"synthetic component"}')
        touch_at(path/'package.json', '2026-10-01T00:00:00Z')
    assert [p['name'] for p in registry.refresh_projects()] == ['synthetic-app']
