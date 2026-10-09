"""Launch a separate Qt6 process without Houdini's Qt5/Python environment.

所有依赖随包放在 lib/ 下，所以只需要用户机器上有一个 64 位 Python 3.10+
（PySide6 6.11 是 abi3 轮子，一份管 3.10~3.14），不需要装任何库、不需要联网。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from . import lib_deps
except ImportError:  # 以顶层模块方式加载（launcher.py 直接把包目录挂上 sys.path）
    import lib_deps

_process = None
_python_command = None
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_PROBE = r"""
import importlib.util, sys
assert importlib.util.find_spec('hou') is None, 'this is Houdini python'
assert sys.maxsize > 2 ** 32, 'need 64-bit python'
assert sys.version_info[:2] >= (3, 10), 'need python >= 3.10'
for _path in reversed({paths!r}):
    sys.path.insert(0, _path)
from PySide6.QtQuickWidgets import QQuickWidget
import requests
print(sys.executable)
"""


def clean_environment():
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH",
                 "QT_QPA_PLATFORM_PLUGIN_PATH", "QML_IMPORT_PATH",
                 "QML2_IMPORT_PATH", "QT_API", "QT_QPA_PLATFORM",
                 "QT_QUICK_BACKEND"):
        environment.pop(name, None)
    houdini_root = environment.get("HFS", "")
    if houdini_root:
        prefix = os.path.normcase(os.path.abspath(houdini_root)) + os.sep
        environment["PATH"] = os.pathsep.join(
            entry for entry in environment.get("PATH", "").split(os.pathsep)
            if entry and not os.path.normcase(os.path.abspath(entry)).startswith(prefix)
        )
    return environment


def _candidates():
    override = os.environ.get("HAGENT_EXTERNAL_PYTHON")
    if override:
        yield [override]
        return
    if Path(sys.executable).name.lower() in ("python.exe", "pythonw.exe", "python"):
        yield [sys.executable]
    for name in ("python", "python3"):
        executable = shutil.which(name)
        if executable:
            yield [executable]
    if os.name == "nt":
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r"Software\Python\PythonCore") as registry:
                    versions = []
                    for index in range(winreg.QueryInfoKey(registry)[0]):
                        versions.append(winreg.EnumKey(registry, index))
                    for version in sorted(versions, reverse=True):
                        try:
                            with winreg.OpenKey(registry, version + r"\InstallPath") as key:
                                yield [str(Path(winreg.QueryValue(key, None)) / "python.exe")]
                        except OSError:
                            continue
            except OSError:
                continue
    python_launcher = shutil.which("py")
    if python_launcher:
        yield [python_launcher, "-3"]


def find_python(environment, root=None, windowless=True):
    """挑一个能跑 Qt6 界面的解释器（能 import lib/ 里的 PySide6 和 requests）。

    windowless=True 时优先用 pythonw.exe（外部界面没有控制台窗口）；
    自己重启时传 False，保留控制台方便看报错。
    """
    global _python_command
    if _python_command is not None:
        return list(_python_command)
    paths = [str(path) for path in lib_deps.runtime_paths()]
    probe = _PROBE.format(paths=paths)
    seen = set()
    for command in _candidates():
        identity = tuple(command)
        if identity in seen:
            continue
        seen.add(identity)
        try:
            result = subprocess.run(
                command + ["-I", "-c", probe], env=environment,
                capture_output=True, text=True, timeout=15, creationflags=_NO_WINDOW,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and result.stdout.strip():
            executable = Path(result.stdout.strip().splitlines()[-1])
            if windowless and os.name == "nt":
                quiet = executable.with_name("pythonw.exe")
                if quiet.is_file():
                    executable = quiet
            _python_command = [str(executable)]
            return list(_python_command)
    raise RuntimeError(
        "找不到能运行 Qt6 界面的 Python。需要 64 位 Python 3.10 及以上，"
        "依赖（PySide6 / shiboken6 / requests）已随包放在 lib/ 里，不用另外安装。\n"
        + lib_deps.diagnose()
        + "\n可用 HAGENT_EXTERNAL_PYTHON 指定 python.exe。"
    )


def launch(root, bridge_port):
    global _process
    if _process is not None and _process.poll() is None:
        print("[KaiTian Houdini-Agent] New UI already running, PID=" + str(_process.pid))
        return _process
    environment = clean_environment()
    command = find_python(environment, root)
    environment["HAGENT_BRIDGE_PORT"] = str(bridge_port)
    environment["HAGENT_KAITIAN_HOST_PID"] = str(os.getpid())
    log_directory = Path(environment.get("LOCALAPPDATA", str(Path.home()))) / "HoudiniAgent"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "kaitian-ui.log"
    with log_path.open("ab") as log_file:
        _process = subprocess.Popen(
            command + ["-I", str(root / "external_runner.py")],
            cwd=str(root), env=environment, stdout=log_file, stderr=subprocess.STDOUT,
            creationflags=_NO_WINDOW,
        )
    try:
        return_code = _process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        print("[KaiTian Houdini-Agent] Qt6 UI PID=%s, Bridge=%s, log=%s" %
              (_process.pid, bridge_port, log_path))
        return _process
    raise RuntimeError("新版界面退出，code=%s；请查看日志：%s" % (return_code, log_path))
