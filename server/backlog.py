"""锁定的官方 Backlog.md 运行时；不重写任务文件。"""
from pathlib import Path
import subprocess
import yaml
from .storage import Storage

INSTALL_ROOT=Path(__file__).resolve().parents[1]
STATES={'inbox':'Inbox','todo':'To Do','in_progress':'In Progress','review':'Review','blocked':'Blocked','done':'Done'}
TASK_TYPES=['bug','feature','improvement','investigation','idea']


class Backlog:
    def __init__(self,root):
        self.store=Storage(root)
        self.root=self.store.root
        self.binary=INSTALL_ROOT/'vendor/backlog-runtime/backlog'
        if not self.binary.is_file():
            raise ValueError('Backlog.md 运行时未构建，请按安装文档执行 scripts.build_backlog')

    def verify_config(self):
        cfg=self.store.yaml('backlog/config.yml',{})
        if not cfg.get('filesystem_only') or cfg.get('auto_commit') or cfg.get('remote_operations') or cfg.get('check_active_branches'):
            raise ValueError('Backlog 必须保持无 Git、本机文件模式')
        if cfg.get('on_status_change') or cfg.get('onStatusChange'):
            raise ValueError('本任务库不允许状态改变时执行命令')
        if cfg.get('backlog_directory') not in [None,'backlog']:
            raise ValueError('任务目录必须留在工作区 backlog 内')
        return cfg

    def run(self,*args):
        if self.store.safe('backlog/config.yml').exists():
            self.verify_config()
        try:
            result=subprocess.run([str(self.binary),*args],cwd=self.root,env={'PATH':'/usr/bin:/bin','BACKLOG_CWD':str(self.root),'NO_COLOR':'1'},capture_output=True,text=True,timeout=30)
        except subprocess.TimeoutExpired as error:
            raise ValueError('Backlog 调用超时，请查询结果后再决定是否重试，避免重复创建') from error
        if result.returncode:
            raise ValueError('Backlog 操作失败：'+(result.stderr or result.stdout).strip()[:1000])
        return result.stdout


def ensure_backlog(root):
    backend=Backlog(root)
    with backend.store.lock():
        if not backend.store.safe('backlog/config.yml').exists():
            if backend.store.safe('data').exists() and any(backend.store.safe('data').rglob('*.md')):
                raise ValueError('旧任务库非空，需先生成迁移清单并备份，不能创建新空库替代')
            backend.run('init','Project Inbox','--no-git','--defaults','--integration-mode','none','--auto-open-browser','false')
            cfg=backend.store.yaml('backlog/config.yml',{})
            cfg.update(statuses=list(STATES.values()),default_status=STATES['inbox'],types=TASK_TYPES,priorities=['P0','P1','P2','P3'],default_port=6420)
            backend.store.write('backlog/config.yml',yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),replace=True)
        backend.verify_config()
    return backend


def sync_projects(root,projects):
    backend=ensure_backlog(root)
    names=[p['name'] for p in projects]
    if len(set(n.casefold() for n in names))!=len(names):
        raise ValueError('项目显示名称重复，请先调整注册表名称')
    with backend.store.lock():
        cfg=backend.verify_config()
        # 不删除已配置值，避免原生页面创建的任务或缺失项目失去合法项目值。
        merged=list(dict.fromkeys(cfg.get('projects',[])+names))
        if cfg.get('projects',[])!=merged:
            cfg['projects']=merged
            backend.store.write('backlog/config.yml',yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),replace=True)
    return backend
