"""Bind KaiTian entry points to the agent shipped in this package."""

import importlib
import os
import sys
from pathlib import Path

try:
    from . import lib_deps
except ImportError:  # 以顶层模块方式加载（launcher.py 把包目录挂在 sys.path 上）
    import lib_deps

ROOT = Path(__file__).resolve().parent


def _inside(filename, directory):
    if not filename:
        return False
    try:
        return Path(filename).resolve().is_relative_to(directory)
    except (OSError, ValueError):
        return False


def _foreign_modules(package_name):
    expected = ROOT / package_name
    result = []
    for name, module in tuple(sys.modules.items()):
        if name != package_name and not name.startswith(package_name + "."):
            continue
        filename = getattr(module, "__file__", None)
        paths = list(getattr(module, "__path__", ()))
        if filename:
            matches = _inside(filename, expected)
        else:
            matches = bool(paths) and all(_inside(path, expected) for path in paths)
        if not matches:
            result.append(name)
    return result


def _stop_foreign_agent():
    for name in ("houdini_agent.ui_qml.controller", "houdini_agent.core.main_window"):
        if name in sys.modules:
            raise RuntimeError(
                "另一份 Houdini-Agent 的界面已在此 Houdini 进程中加载。"
                "请保存场景并重启 Houdini，再从 KaiTian 菜单启动，避免混用 Qt 对象和会话。"
            )
    server = sys.modules.get("houdini_agent.utils.mcp.server")
    if server is not None:
        stopped, message = server.stop_mcp_server()
        if not stopped:
            raise RuntimeError("无法停止另一份 MCP 服务：" + message)
        try:
            import hou
            for callback in hou.ui.eventLoopCallbacks():
                if getattr(callback, "__module__", None) == server.__name__:
                    hou.ui.removeEventLoopCallback(callback)
        except (ImportError, AttributeError):
            pass
    bridge = sys.modules.get("houdini_agent.bridge.server")
    running = getattr(bridge, "_SERVER", None)
    if running is not None:
        running.shutdown()
        running.server_close()
        thread = getattr(bridge, "_THREAD", None)
        if thread is not None:
            thread.join(timeout=3)
            if thread.is_alive():
                raise RuntimeError("另一份 Houdini Bridge 尚未退出，请重启 Houdini。")
        bridge._SERVER = None
        bridge._THREAD = None


def prepare_runtime(include_dependencies=True):
    """Select one code root, including when an external Bridge imported first."""
    foreign_agent = _foreign_modules("houdini_agent")
    if foreign_agent:
        _stop_foreign_agent()
    for package_name in ("houdini_agent", "shared"):
        if not _foreign_modules(package_name):
            continue
        for name in tuple(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                del sys.modules[name]

    # 依赖都在包内 lib/，按当前 Python 版本挑好目录再挂上
    lib_deps.apply(include_houdini_extras=include_dependencies)
    root = str(ROOT)
    sys.path[:] = [
        entry for entry in sys.path
        if os.path.normcase(os.path.abspath(entry)) != os.path.normcase(root)
    ]
    sys.path.insert(0, root)
    importlib.invalidate_caches()
    agent = importlib.import_module("houdini_agent")
    if not _inside(getattr(agent, "__file__", None), ROOT / "houdini_agent"):
        raise RuntimeError("Houdini-Agent 加载路径错误：" + str(getattr(agent, "__file__", None)))
    print("[KaiTian Houdini-Agent] code root: " + str(ROOT))
    return ROOT
