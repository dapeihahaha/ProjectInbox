"""命令行只转交共享业务层，不另外实现存储。"""
import argparse
import json
import os
from pathlib import Path
import sys
from .main import default_root
from .project_registry import Registry
from .task_manager import TaskManager


def main():
    p=argparse.ArgumentParser(description='本地项目任务收件箱（JSON 输出）')
    p.add_argument('--home',type=Path,default=default_root())
    sub=p.add_subparsers(dest='command',required=True)
    for name in ['list','search']:
        cmd=sub.add_parser(name)
        if name=='search':
            cmd.add_argument('query')
        cmd.add_argument('--project',dest='project_id')
        cmd.add_argument('--type');cmd.add_argument('--status');cmd.add_argument('--priority')
        cmd.add_argument('--limit',type=int,default=50)
    for name in ['show','done','archive']:
        sub.add_parser(name).add_argument('task_id')
    handoff=sub.add_parser('handoff',help='生成一个或多个任务的 Agent 交接指令')
    handoff.add_argument('--mode',choices=['execute','research'],default='execute',help='交接模式：execute 执行，research 只读调研')
    handoff.add_argument('task_ids',nargs='+')
    handoff.add_argument('--deploy',action='store_true',help='授权 Agent 完成后直接合并、推送、部署')
    create=sub.add_parser('create')
    create.add_argument('title',nargs='?',default='待整理任务')
    create.add_argument('--project',dest='project_id');create.add_argument('--type',default='bug')
    create.add_argument('--priority',default='P2');create.add_argument('--description',default='')
    create.add_argument('--expected-behavior',default='');create.add_argument('--reproduction-steps',default='')
    create.add_argument('--tag',dest='tags',action='append')
    update=sub.add_parser('update');update.add_argument('task_id');update.add_argument('--changes',required=True,help='JSON 对象，例如 {"status":"done"}')
    for name in ['refresh','projects','check']:
        sub.add_parser(name)
    board=sub.add_parser('board',help='启动本机 Backlog.md 看板，Ctrl+C 停止')
    board.add_argument('--port',type=int,default=6420)
    board.add_argument('--no-open',action='store_true')
    args=vars(p.parse_args());root=args.pop('home');command=args.pop('command')
    try:
        tasks=TaskManager(root);registry=Registry(root)
        if command in ['list','search']:
            result=tasks.search_tasks(**args)
        elif command=='show': result=tasks.get_task(**args)
        elif command=='handoff':
            from .handoff import agent_handoff
            result=agent_handoff(root,args['task_ids'],args['deploy'],args['mode'])
        elif command=='create': result=tasks.create_task(**args)
        elif command=='done': result=tasks.update_task(args['task_id'],status='done')
        elif command=='archive': result=tasks.archive_task(**args)
        elif command=='update':
            changes=json.loads(args['changes'])
            if not isinstance(changes,dict): raise ValueError('changes 必须是 JSON 对象')
            result=tasks.update_task(args['task_id'],**changes)
        elif command=='refresh':
            result={'projects':registry.refresh_projects(),'discovery':registry.discovery_report}
            from .backlog import sync_projects
            sync_projects(root,result['projects'])
        elif command=='projects': result=registry.list_projects()
        elif command=='board':
            if not 1024<=args['port']<=65535:raise ValueError('端口需在 1024–65535 之间')
            if not tasks.check_integrity()['ok']:raise ValueError('先恢复数据完整性，再启动看板')
            launch=[str(tasks.backend.binary),'browser','--port',str(args['port'])]
            if args['no_open']:launch.append('--no-open')
            os.chdir(tasks.root)
            os.execve(tasks.backend.binary,launch,{'PATH':'/usr/bin:/bin','BACKLOG_CWD':str(tasks.root)})
        else: result=tasks.check_integrity()
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if command=='check' and not result['ok']: return 1
        return 0
    except (ValueError,OSError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
