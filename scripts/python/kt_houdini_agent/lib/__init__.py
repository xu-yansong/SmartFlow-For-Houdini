# -*- coding: utf-8 -*-
"""
本地依赖库目录
包含 requests 及其依赖，用于在没有安装这些库的环境中运行

包含的库：
- requests: HTTP 请求库
- urllib3: URL 处理
- certifi: SSL 证书
- charset_normalizer: 字符编码检测
- idna: 国际化域名

此目录中的库会被强制使用，不会使用系统安装的版本。
"""

import os
import sys

# 强制将 lib 目录添加到 sys.path 最前面
_lib_dir = os.path.dirname(os.path.abspath(__file__))

# 移除已存在的路径（如果有），然后添加到最前面
if _lib_dir in sys.path:
    sys.path.remove(_lib_dir)
sys.path.insert(0, _lib_dir)

