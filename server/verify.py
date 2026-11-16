"""在调用方提供的隔离目录验证 MCP 与 CLI 的真实进程调用。"""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def verify_roundtrip(root):
    params=StdioServerParameters(command=sys.executable,args=['-m','server.main','--home',str(root)],cwd=str(Path(root).parent),env={'PATH':'/usr/bin:/bin'})
    async with Client(params,read_timeout_seconds=15) as client:
        tools=await client.list_tools()
        names=[t.name for t in tools.tools]
        async def call(name,args):
            result=await client.call_tool(name,args)
            if result.is_error:
                raise AssertionError(str(result.content))
            data=result.structured_content
            if data is None:
                data=json.loads(result.content[0].text)
            if isinstance(data,dict) and set(data)=={'result'}:
                return data['result']
            return data
        created=await call('create_task',{'title':'隔离验证：上传顺序异常'})
        task_id=created['id']
        cli=subprocess.run([sys.executable,'-m','server.cli','--home',str(root),'done',task_id],capture_output=True,text=True,check=True)
        assert json.loads(cli.stdout)['status']=='done'
        got=await call('get_task',{'task_id':task_id})
        assert got['status']=='done'
        archived=await call('archive_task',{'task_id':task_id})
        assert archived['status']=='archived'
        template=await call('get_handoff_template',{})
        assert template['version']=='handoff/v1'
        locked=await client.call_tool('update_task',{'task_id':task_id,'changes':{'status':'in_progress'}})
        assert locked.is_error and '状态不能用 update_task' in locked.content[0].text
        bad=await client.call_tool('get_task',{'task_id':'../../outside'})
        assert bad.is_error
        assert '无效任务 ID' in bad.content[0].text
    return {'ok':True,'tools':names,'cli_mcp_shared_task':True,'path_traversal_rejected':True,'status_locked_for_agents':True}
