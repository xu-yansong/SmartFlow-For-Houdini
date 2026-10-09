"""KaiTian entry point for the packaged Houdini Agent.

第三方依赖全部随包放在 lib/ 下，用户机器只要有一个 64 位 Python 3.10+ 就行：
在 Houdini 里点菜单、或者在外部跑 launcher.bat / launcher.py，都走同一套代码，
都不需要用户自己装库、也不需要联网。
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent
_agent_window = None


def _module(name):
    """导入本包内的模块（包内导入 / 顶层脚本两种加载方式都支持）。"""
    if __package__:
        return importlib.import_module(__package__ + "." + name)
    if str(_ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(_ROOT_DIR))
    return importlib.import_module(name)


def _bootstrap():
    return _module("bootstrap")


def _lib_deps():
    return _module("lib_deps")


def detect_dcc():
    try:
        import hou
        return "houdini"
    except ImportError:
        return None


def launch_houdini_agent(ui=None):
    """Open Qt6 in its own process by default; never silently show the old UI."""
    _bootstrap().prepare_runtime()
    selected_ui = (ui or os.environ.get("HAGENT_UI", "external")).strip().lower()
    if selected_ui not in ("external", "qml", "legacy"):
        raise ValueError("HAGENT_UI must be external, qml or legacy")
    if selected_ui == "legacy":
        previous_ui = os.environ.get("HAGENT_UI")
        os.environ["HAGENT_UI"] = "legacy"
        try:
            from houdini_agent import main
            return main.show_tool()
        finally:
            if previous_ui is None:
                os.environ.pop("HAGENT_UI", None)
            else:
                os.environ["HAGENT_UI"] = previous_ui

    from houdini_agent.bridge.server import start_bridge
    bridge = start_bridge()
    if bridge is None:
        raise RuntimeError("Houdini Bridge 启动失败，无法连接新版界面。")
    if selected_ui == "qml":
        from houdini_agent.qt_compat import PYSIDE_VERSION
        if PYSIDE_VERSION >= 6:
            from houdini_agent.ui_qml import app
            return app.show_tool()
        print("[KaiTian Houdini-Agent] Qt5 host detected; launching external Qt6 UI.")

    deps = _lib_deps()
    missing = deps.missing_modules(deps.required_modules())
    if missing:
        print("[KaiTian Houdini-Agent] 警告：lib/ 里找不到 %s；"
              "如果外部解释器也没有这些库，新版界面会起不来。\n%s"
              % (", ".join(missing), deps.diagnose()))
    return _module("external_launcher").launch(_ROOT_DIR, bridge.server_address[1])


def _restart_with_usable_python(reason):
    """当前解释器跑不了 Qt6 界面时，换一个能跑的重启一次。"""
    external = _module("external_launcher")
    command = external.find_python(
        external.clean_environment(), _ROOT_DIR, windowless=False)
    print("[KaiTian Houdini-Agent] 当前解释器不可用（%s），改用 %s 重启"
          % (reason, command[0]))
    environment = os.environ.copy()
    environment["HAGENT_ENV_REEXEC"] = "1"
    return subprocess.call(list(command) + [str(_ROOT_DIR / "launcher.py")],
                           env=environment)


def launch_external_agent():
    """不带 Houdini 时在本进程开窗口：依赖全部来自包内 lib/。"""
    deps = _lib_deps()
    deps.apply()
    problem = deps.interpreter_problem()
    missing = deps.missing_modules(deps.required_modules())
    if (problem or missing) and not os.environ.get("HAGENT_ENV_REEXEC") \
            and not os.environ.get("HAGENT_EXTERNAL_PYTHON"):
        return _restart_with_usable_python(problem or ("缺少 " + ", ".join(missing)))
    deps.require(deps.required_modules(),
                 hint="依赖应随包放在 lib/ 下；可用 tools/fetch_lib.py 补齐。")
    _bootstrap().prepare_runtime(include_dependencies=False)
    from houdini_agent.ui_qml import external_app
    return external_app.main()


def launch(ui=None):
    if detect_dcc() == "houdini":
        return launch_houdini_agent(ui=ui)
    return launch_external_agent()


def show_tool(ui=None):
    global _agent_window
    _agent_window = launch(ui=ui)
    return _agent_window


if __name__ == "__main__":
    show_tool()
