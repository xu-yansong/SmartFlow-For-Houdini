"""Isolated process entry point for the KaiTian Qt6 window."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import lib_deps

# 依赖全部来自包内 lib/，这个进程不需要装任何第三方库
lib_deps.apply()
lib_deps.require(lib_deps.required_modules())
optional = lib_deps.optional_modules()
if lib_deps.missing_modules(optional):
    print("[KaiTian Houdini-Agent] 未找到 %s（长期记忆/向量检索会不可用）；"
          "可用 tools/fetch_lib.py 为 Python %d.%d 补齐。"
          % (", ".join(optional), *sys.version_info[:2]),
          file=sys.stderr)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

from houdini_agent.ui_qml.external_app import main

if __name__ == "__main__":
    raise SystemExit(main())
