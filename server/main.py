"""仅 stdio；不开放网络端口或任意文件 / Shell 工具。"""
import argparse
import os
from pathlib import Path
from typing import Literal
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from .project_registry import Registry
from .task_manager import TaskManager
from .backlog import sync_projects


def default_root():
    return Path(os.environ.get('PROJECT_INBOX_HOME',Path(__file__).resolve().parents[1]))


def invoke(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except ValueError as error:
        raise ToolError(str(error)) from error
    except OSError as error:
        raise ToolError('本地文件操作失败，请检查权限或运行 project-inbox check') from error


def build_server(root):
    tasks=TaskManager(root)
    registry=Registry(root)
    mcp=MCPServer('Project Inbox',instructions='本地项目任务收件箱。项目不明确可进入全局 inbox；先查重复再创建；不自动合并。',log_level='WARNING')

    @mcp.tool()
    def list_projects() -> list[dict]:
        """列出已注册项目及别名、简介、可用状态。"""
        return invoke(registry.list_projects)

    @mcp.tool()
    def match_project(text: str) -> dict:
        """按名称、别名、关键词匹配；有歧义时返回全部候选。"""
        return invoke(registry.match_project, text)

    @mcp.tool()
    def create_task(project_id: str | None=None,title: str='待整理任务',type: Literal['bug','feature','improvement','investigation','idea']='bug',description: str='',expected_behavior: str='',reproduction_steps: str='',priority: Literal['P0','P1','P2','P3']='P2',tags: list[str] | None=None) -> dict:
        """保存新任务，返回实际任务 ID。项目不明确传 null 进入全局 inbox。"""
        return invoke(tasks.create_task, project_id,title,type,description,expected_behavior,reproduction_steps,priority,tags)

    @mcp.tool()
    def search_tasks(query: str='',project_id: str | None=None,type: str | None=None,status: str | None=None,priority: str | None=None,limit: int=50) -> list[dict]:
        """搜索任务，含归档；返回精简结果。未解决需排除 done 和 archived。"""
        return invoke(tasks.search_tasks, query,project_id,type,status,priority,limit)

    @mcp.tool()
    def get_task(task_id: str) -> dict:
        """按 ID 读取完整任务。"""
        return invoke(tasks.get_task, task_id)

    @mcp.tool()
    def update_task(task_id: str,changes: dict) -> dict:
        """修改指定字段；changes 可含 title/description/status/priority/tags/project_id/type/expected_behavior/reproduction_steps/notes/commits。project_id=null 移至全局 inbox。"""
        return invoke(tasks.update_task, task_id,**changes)

    @mcp.tool()
    def find_duplicates(title: str,project_id: str | None=None,description: str='',limit: int=5) -> list[dict]:
        """查找同项目相似任务；不自动合并、修改或删除。"""
        return invoke(tasks.find_duplicates, title,project_id,description,limit)

    @mcp.tool()
    def archive_task(task_id: str) -> dict:
        """归档任务，保留 ID 和文件，不永久删除。"""
        return invoke(tasks.archive_task, task_id)

    @mcp.tool()
    def refresh_projects() -> dict:
        """纳入配置目录内最近三个月有 Git 提交或本地文件改动的全部项目，保留已有信息。"""
        projects=invoke(registry.refresh_projects)
        invoke(sync_projects,root,projects)
        return {'projects':projects,'discovery':registry.discovery_report}

    @mcp.tool()
    def get_project_tasks(project_id: str,status: str | None=None,limit: int=50) -> list[dict]:
        """列出项目任务，可按状态筛选。"""
        return invoke(tasks.get_project_tasks, project_id,status,limit)

    return mcp


def main():
    parser=argparse.ArgumentParser(description='Project Inbox stdio MCP Server')
    parser.add_argument('--home',type=Path,default=default_root())
    args=parser.parse_args()
    build_server(args.home).run(transport='stdio')


if __name__=='__main__':
    main()
