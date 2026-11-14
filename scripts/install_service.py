"""安装当前用户的 launchd 看板服务；不更改 MCP 或任务内容。"""
from pathlib import Path
import os
import plistlib
import subprocess
from server.task_manager import TaskManager


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'config/launchagents/com.projectinbox.board.plist'
    data=source.read_bytes()
    config=plistlib.loads(data)
    if config['WorkingDirectory']!=str(root) or not Path(config['ProgramArguments'][0]).is_file():
        raise ValueError('服务路径与当前安装不一致，请先更新 plist')
    if not TaskManager(root).check_integrity()['ok']:
        raise ValueError('任务完整性检查失败，拒绝启动服务')
    target=Path.home()/'Library/LaunchAgents'/source.name
    if target.is_symlink() or (target.exists() and target.read_bytes()!=data):
        raise ValueError('已有不同服务配置，拒绝覆盖：'+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    logs=Path(config['StandardOutPath']).parent
    logs.mkdir(parents=True,exist_ok=True,mode=0o700)
    if not target.exists():
        with target.open('xb') as out:out.write(data)
    subprocess.run(['/usr/bin/plutil','-lint',str(target)],check=True)
    domain=f'gui/{os.getuid()}'
    service=domain+'/'+config['Label']
    subprocess.run(['/bin/launchctl','enable',service],check=True)
    loaded=subprocess.run(['/bin/launchctl','print',service],capture_output=True)
    if loaded.returncode:
        subprocess.run(['/bin/launchctl','bootstrap',domain,str(target)],check=True)
    print('Installed:',target)
    print('Service:',service)
    print('Board: http://127.0.0.1:6420/board')


if __name__=='__main__':main()
