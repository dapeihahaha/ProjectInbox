"""从固定本地来源提取路径与活动时间，不读取会话正文。"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

MAX_ENTRIES = 20000


def timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = value / 1000 if value > 100000000000 else value
        return datetime.fromtimestamp(value, timezone.utc)
    if isinstance(value, str):
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('会话时间缺少时区')
        return result.astimezone(timezone.utc)
    raise ValueError('无效会话时间')


def read_activity(settings):
    sources = settings.get('activity_sources', {})
    home = Path.home()
    locations = {
        'codex': Path(sources.get('codex', home/'.codex/state_5.sqlite')).expanduser(),
        'claude': Path(sources.get('claude', home/'.claude/sessions')).expanduser(),
        'pi': Path(sources.get('pi', home/'.pi/agent/sessions')).expanduser(),
    }
    rows, report = [], []

    def add(source, cwd, stamp, basis):
        if not isinstance(cwd, str) or not cwd or len(cwd) > 4096:
            return
        try:
            time = timestamp(stamp)
        except (ValueError, OverflowError, OSError):
            return
        rows.append(dict(source=source, path=cwd, last_active=time.isoformat(), time_basis=basis))

    for source, path in locations.items():
        before = len(rows)
        status = dict(source=source, available=False, records=0)
        try:
            if source == 'codex':
                if not path.is_file() or path.is_symlink():
                    raise ValueError('索引文件不存在或是符号链接')
                conn = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True, timeout=3)
                try:
                    conn.execute('PRAGMA query_only=ON')
                    columns = {r[1] for r in conn.execute('PRAGMA table_info(threads)')}
                    field = 'updated_at_ms' if 'updated_at_ms' in columns else 'updated_at'
                    if not {'cwd', field} <= columns:
                        raise ValueError('会话索引字段不兼容')
                    query = f'SELECT cwd, {field} FROM threads ORDER BY {field} DESC LIMIT {MAX_ENTRIES + 1}'
                    result = conn.execute(query).fetchall()
                    if len(result) > MAX_ENTRIES:
                        raise ValueError('会话索引超过条数限制')
                    for cwd, stamp in result:
                        add(source, cwd, stamp, field)
                finally:
                    conn.close()
            else:
                if not path.is_dir() or path.is_symlink():
                    raise ValueError('会话目录不存在或是符号链接')
                files = sorted(path.glob('*.json' if source=='claude' else '*/*.jsonl'))
                if len(files)>MAX_ENTRIES:
                    raise ValueError('会话文件超过条数限制')
                for file in files:
                    if file.is_symlink() or file.parent.is_symlink():
                        continue
                    try:
                        with file.open() as stream:
                            # Claude 为独立会话元数据；Pi 只读取第一行 session 头。
                            raw = stream.read(65537) if source=='claude' else stream.readline(16385)
                        if len(raw) > (65536 if source=='claude' else 16384):
                            continue
                        data = json.loads(raw)
                        if not isinstance(data, dict):
                            continue
                        if source=='claude':
                            add(source, data.get('cwd'), data.get('updatedAt', data.get('startedAt')), 'live_session_metadata')
                        elif data.get('type')=='session':
                            add(source, data.get('cwd'), file.stat().st_mtime, 'session_file_mtime')
                    except (OSError, UnicodeError, ValueError):
                        continue
            status['available'] = True
        except (OSError, ValueError, sqlite3.Error):
            status['limitation'] = '来源不可用、格式不兼容或超出读取限制'
        status['records'] = len(rows)-before
        if source=='claude':
            status['scope'] = '仅当前会话元数据，不代表完整历史'
        if source=='pi':
            status['scope'] = '会话文件最后写入时间，非项目目录修改时间'
        report.append(status)
    return rows, report
