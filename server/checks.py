"""汇报时程序自己做的核验：截图在不在、提交在不在对的分支、测试是不是真过了。"""
import os
from pathlib import Path
import signal
import subprocess
import time
from . import workspace as ws

OUTPUT_TAIL = 4000


def evidence(evidence_dir, names, required):
    problems = []
    folder = Path(evidence_dir)
    for name in names:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            problems.append(f'截图 {name} 不在 {folder} 里。')
        elif path.stat().st_size == 0:
            problems.append(f'截图 {name} 是空文件。')
    if required and not names:
        problems.append(f'交接单要求截图，但 {folder} 里一张都没有登记。')
    return problems


def commits(workspace, base_commit, previous_head=''):
    """任务分支上要有新提交，工作区不能有没提交的改动。"""
    facts = ws.state(workspace, base_commit)
    problems = []
    if not facts['exists']:
        return [f'工作区 {workspace} 不存在：代码必须在程序分配的工作区里改。'], facts
    if not facts['commits']:
        problems.append('任务分支上没有新提交：先在工作区里 git commit，再汇报。')
    elif previous_head and facts['head'] == previous_head:
        problems.append('返工后没有新的提交：分支还停在上次汇报的位置。')
    if facts['dirty']:
        shown = '；'.join(facts['dirty'][:5])
        problems.append(f'工作区里还有 {len(facts["dirty"])} 处没提交的改动（{shown}）：提交或撤销后再汇报。')
    return problems, facts


def run_tests(workspace, command, timeout):
    """在工作区里限时重跑交接单写的测试命令，返回 (是否通过, 输出末尾, 用时秒数)。"""
    if command.strip().lower() == 'none':
        return None, '交接单写明项目没有测试（tests: none），跳过。', 0
    shell = os.environ.get('SHELL') or '/bin/bash'
    if not Path(shell).is_absolute() or not Path(shell).exists():
        shell = '/bin/bash' if Path('/bin/bash').exists() else '/bin/sh'
    started = time.monotonic()
    try:
        proc = subprocess.Popen([shell, '-lc', command], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, errors='replace', start_new_session=True)
    except OSError as error:
        return False, f'测试命令启动失败：{error}', 0
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        output, _ = proc.communicate()
        return False, f'测试超过 {timeout} 秒没跑完，已停止。\n' + (output or '')[-OUTPUT_TAIL:], round(time.monotonic() - started)
    return proc.returncode == 0, (output or '')[-OUTPUT_TAIL:], round(time.monotonic() - started)
