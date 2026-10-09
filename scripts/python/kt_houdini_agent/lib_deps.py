# -*- coding: utf-8 -*-
r"""随包分发的依赖目录（lib/）的路径解析与自检。

策略
----
所有第三方依赖都放在包内 lib/ 随包分发：用户机器上只要有一个 64 位 Python 3.10+，
不装任何库、不联网、不跑 pip 就能用 —— Houdini 里点菜单、或者外部跑
launcher.bat / launcher.py 都一样。

目录约定
--------
lib/            版本无关的依赖。
                PySide6 / shiboken6 是 cp310-abi3 轮子，一份就能跑 Python 3.10~3.14。
lib/py3.12/     按小版本编译的依赖（numpy 这类没有 abi3 的），
                按当前解释器选择性加入 sys.path —— 免得 Python 3.11 去加载 cp312 的 numpy。
                `tools/fetch_lib.py` 会自动往这里装。
"""

import contextlib
import functools
import importlib.util
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = ROOT / "lib"
# 依赖清单：lib/ 里该有哪些包只写在这一处，tools/fetch_lib.py 也读它
MANIFEST = ROOT / "tools" / "requirements-lib.txt"

# PySide6 6.11 的 abi3 下限
MIN_PYTHON = (3, 10)

_ANNOTATION = re.compile(r"#\s*(.*)$")
_IMPORT_NAME = re.compile(r"import\s*:\s*([A-Za-z0-9_.]+)")
_VERSION_MARK = re.compile(r"^\s*\[ver\]\s*")


@functools.lru_cache(maxsize=None)
def manifest_entries(path=None):
    """解析依赖清单 -> ((pip 需求, 导入名, 是否可选), ...)。

    解析不出来就返回空元组（清单缺失时自检会明确报出来，不静默通过）。
    """
    try:
        text = Path(path or MANIFEST).read_text(encoding="utf-8")
    except OSError:
        return ()
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        annotation = ""
        match = _ANNOTATION.search(line)
        if match:
            annotation = match.group(1)
            line = line[:match.start()]
        found = _IMPORT_NAME.search(annotation)
        if found is None:
            continue
        entries.append((_VERSION_MARK.sub("", line).strip(),
                        found.group(1),
                        "optional" in annotation.lower()))
    return tuple(entries)


def required_modules():
    """清单里没标 optional 的导入名 —— 少了界面/agent 跑不起来。"""
    return tuple(name for _spec, name, optional in manifest_entries() if not optional)


def optional_modules():
    """清单里标了 optional 的导入名 —— 缺了只影响增强功能。"""
    return tuple(name for _spec, name, optional in manifest_entries() if optional)


def python_tag(version_info=None):
    version_info = version_info or sys.version_info
    return "py%d.%d" % (version_info[0], version_info[1])


def version_lib(version_info=None):
    """版本专属依赖目录（lib/py3.12）。"""
    return LIB / python_tag(version_info)


def runtime_paths(version_info=None):
    """外部进程要加进 sys.path 的目录，顺序：版本专属目录 -> lib。"""
    paths = []
    version_dir = version_lib(version_info)
    if version_dir.is_dir():
        paths.append(version_dir)
    if LIB.is_dir():
        paths.append(LIB)
    return paths


def houdini_paths(version_info=None):
    """Houdini 进程内的 sys.path 追加项（pywin32 的既有布局要保持）。"""
    paths = []
    for relative in ("win32/lib", "win32", "pythonwin"):
        candidate = LIB / relative
        if candidate.is_dir():
            paths.append(candidate)
    paths.extend(runtime_paths(version_info))
    return paths


def dll_directories():
    """需要 add_dll_directory 的目录（pywin32 的 DLL）。"""
    directory = LIB / "pywin32_system32"
    return [directory] if directory.is_dir() else []


_dll_handles = []


def apply(include_houdini_extras=False):
    """把依赖目录挂进 sys.path（已存在的挪到最前），返回挂上的目录。"""
    paths = houdini_paths() if include_houdini_extras else runtime_paths()
    for directory in reversed(paths):
        entry = str(directory)
        sys.path[:] = [
            item for item in sys.path
            if os.path.normcase(os.path.abspath(item)) != os.path.normcase(entry)
        ]
        sys.path.insert(0, entry)
    if include_houdini_extras and not _dll_handles and hasattr(os, "add_dll_directory"):
        for directory in dll_directories():
            try:
                _dll_handles.append(os.add_dll_directory(str(directory)))
            except OSError:
                continue
            search = os.environ.get("PATH", "").split(os.pathsep)
            if str(directory) not in search:
                os.environ["PATH"] = os.pathsep.join([str(directory)] + search)
    importlib.invalidate_caches()
    return paths


@contextlib.contextmanager
def _lib_on_path():
    """临时把依赖目录挂上做探测，结束后还原 sys.path。"""
    original = list(sys.path)
    try:
        apply()
        yield
    finally:
        sys.path[:] = original
        importlib.invalidate_caches()


def interpreter_problem(version_info=None):
    """当前解释器为什么不满足要求；满足返回 None。"""
    version_info = tuple(version_info or sys.version_info)[:2]
    if sys.maxsize <= 2 ** 32:
        return "需要 64 位 Python（当前是 32 位，PySide6 只有 win_amd64 轮子）"
    if version_info < MIN_PYTHON:
        return ("需要 Python %d.%d 及以上（PySide6 6.11 的 abi3 下限），当前是 %d.%d"
                % (MIN_PYTHON[0], MIN_PYTHON[1], version_info[0], version_info[1]))
    return None


def missing_modules(names):
    """names 里哪些模块 import 不到（探测时临时挂上 lib，报错信息才准）。"""
    with _lib_on_path():
        missing = []
        for name in names:
            try:
                found = importlib.util.find_spec(name)
            except (ImportError, ValueError):
                found = None
            if found is None:
                missing.append(name)
        return missing


def diagnose():
    """依赖自检报告，用在报错信息里。"""
    version_dir = version_lib()
    lines = [
        "解释器    : %s (%s)" % (sys.executable,
                                 "64 位" if sys.maxsize > 2 ** 32 else "32 位"),
        "Python    : %s" % sys.version.split()[0],
        "依赖目录  : %s%s" % (LIB, "" if LIB.is_dir() else "（不存在！）"),
        "版本目录  : %s%s" % (version_dir,
                              "" if version_dir.is_dir() else "（不存在，只影响 numpy 这类按版本编译的包）"),
        "依赖清单  : %s%s" % (MANIFEST,
                              "" if MANIFEST.is_file() else "（缺失！无法自检）"),
    ]
    for label, names in (("必需", required_modules()), ("可选", optional_modules())):
        missing = missing_modules(names)
        lines.append("%s    : %s" % (label, "齐全" if not missing else "缺少 " + ", ".join(missing)))
    problem = interpreter_problem()
    if problem:
        lines.append("版本      : " + problem)
    return "\n".join(lines)


def require(names, hint=""):
    """确认 names 能 import，否则抛带自检报告的 RuntimeError。"""
    missing = missing_modules(names)
    if not missing:
        return
    message = ("缺少依赖：%s\n%s" % (", ".join(missing), diagnose()))
    if hint:
        message += "\n" + hint
    raise RuntimeError(message)
