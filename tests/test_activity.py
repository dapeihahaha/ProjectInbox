import json
import os
from pathlib import Path
import sqlite3

from server.project_registry import Registry
import yaml


def setup_activity(root, scan):
    (root/'config').mkdir(parents=True, exist_ok=True)
    agent=root/'agents'
    (agent/'claude').mkdir(parents=True)
    (agent/'pi').mkdir()
    db=agent/'codex.sqlite'
    c=sqlite3.connect(db)
    c.execute('create table threads(cwd text, updated_at integer, updated_at_ms integer)')
    c.commit(); c.close()
    settings={'scan_roots':[str(scan)],'max_depth':4,'timezone':'America/Los_Angeles','activity_sources':{'codex':str(db),'claude':str(agent/'claude'),'pi':str(agent/'pi')}}
    (root/'config/settings.yaml').write_text(yaml.safe_dump(settings))
    return agent


def add_activity(root, path, stamp=1700000000000):
    settings=yaml.safe_load((root/'config/settings.yaml').read_text())
    db=settings['activity_sources']['codex']
    c=sqlite3.connect(db);c.execute('insert into threads values(?,?,?)',(str(path),stamp//1000,stamp));c.commit();c.close()


def test_three_sources_only_metadata(tmp_path):
    from server.activity import read_activity
    scan=tmp_path/'scan';scan.mkdir()
    root=tmp_path/'app';agent=setup_activity(root,scan)
    add_activity(root,scan/'codex')
    (agent/'claude/one.json').write_text(json.dumps({'cwd':str(scan/'claude'),'updatedAt':1700000001000}))
    p=agent/'pi/project';p.mkdir()
    f=p/'one.jsonl'; f.write_text(json.dumps({'type':'session','cwd':str(scan/'pi'),'timestamp':'2023-01-01T00:00:00Z'})+'\nDO NOT PARSE THIS BODY\n')
    os.utime(f,(1700000002,1700000002))
    rows,status=read_activity(Registry(root).settings())
    assert {r['source'] for r in rows}=={'codex','claude','pi'}
    assert all(s['available'] for s in status)
    assert next(r for r in rows if r['source']=='pi')['time_basis']=='session_file_mtime'


def test_modification_discovery_has_no_top_ten_limit(tmp_path):
    from tests.test_system import repo,git
    scan=tmp_path/'scan';scan.mkdir()
    root=tmp_path/'app';setup_activity(root,scan)
    for i in range(12):
        p=repo(scan/f'p{i:02}')
        add_activity(root,p,1700000000000+i*1000)
    git(scan/'p11','worktree','add','-q','-b','fixture-wt',str(scan/'p11-wt'))
    add_activity(root,scan/'p11-wt',1700000020000)
    outside=repo(tmp_path/'outside'); add_activity(root,outside,1700000090000)
    excluded=scan/'node_modules';excluded.mkdir();repo(excluded/'hidden');add_activity(root,excluded/'hidden',1700000100000)
    linked=scan/'link'; linked.symlink_to(outside);add_activity(root,linked,1700000110000)
    r=Registry(root);result=r.refresh_projects()
    assert len(result)==12
    assert str(scan/'p11-wt') in next(p for p in result if p['name']=='p11')['worktrees']
    assert not any(p['name'] in ['outside','hidden','link'] for p in result)
    assert [s['source'] for s in r.discovery_report['sources']]==['git','local_files']
    # 不依赖会话排名，并保留人工字段。
    data=yaml.safe_load((root/'config/projects.yaml').read_text()); data['projects'][0]['aliases']=['自定']
    (root/'config/projects.yaml').write_text(yaml.safe_dump(data))
    newer=repo(scan/'newer'); add_activity(root,newer,1700000900000)
    refreshed=r.refresh_projects()
    assert len(refreshed)==13
    assert next(p for p in refreshed if p['id']==data['projects'][0]['id'])['aliases']==['自定']


def test_unavailable_sources_do_not_erase_registry(tmp_path):
    scan=tmp_path/'scan';scan.mkdir();root=tmp_path/'app';agent=setup_activity(root,scan)
    (root/'config/projects.yaml').write_text('projects: []\n')
    (agent/'codex.sqlite').unlink()
    r=Registry(root)
    assert r.refresh_projects()==[]
    assert (root/'config/projects.yaml').read_text()=='projects: []\n'
