#!/usr/bin/env python3
"""生成入口：从 settings.yaml 指定会话元数据生成 config/projects.yaml。"""
from server.cli import main
import sys
if __name__=='__main__':
    sys.argv=[sys.argv[0], 'refresh']
    sys.exit(main())
