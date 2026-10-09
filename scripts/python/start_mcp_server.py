"""
Houdini MCP Server 启动脚本

用法：
    1) 在 Houdini GUI 的 Python Source Editor / Python Shell 中：
         import start_mcp_server
         start_mcp_server.start_in_houdini()

    2) 在命令行用 hython 启动（无 GUI 常驻）：
         "C:\\Program Files\\Side Effects Software\\Houdini X.Y.Z\\bin\\hython.exe" ^
             "I:\\Pangu\\Kaitian\\HouTools\\KaiTian\\scripts\\python\\start_mcp_server.py"

注意：必须使用 hython（或在 Houdini 内运行），普通 python.exe 缺少 hou 模块会失败。
"""

import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kt_houdini_agent")
LIB = os.path.join(ROOT, "lib")


def _setup_env():
    """设置 sys.path 和 DLL 搜索路径，确保本地依赖可以被正确导入。"""
    import importlib.util
    module_name = "_kaitian_agent_bootstrap"
    filename = os.path.join(ROOT, "bootstrap.py")
    bootstrap = sys.modules.get(module_name)
    if bootstrap is None or bootstrap.__file__ != filename:
        spec = importlib.util.spec_from_file_location(module_name, filename)
        bootstrap = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = bootstrap
        spec.loader.exec_module(bootstrap)
    bootstrap.prepare_runtime()


def _check_dependencies():
    """检查 hou 和 fastmcp 是否可用，不可用则抛出 ImportError。"""
    try:
        import hou  # type: ignore  # noqa: F401
    except ImportError:
        raise ImportError(
            "未找到 hou 模块。请使用 hython.exe 或在 Houdini 内运行此脚本。"
        )

    try:
        import fastmcp  # type: ignore  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"未能 import fastmcp: {e}\n"
            f"请确认依赖已安装到：{LIB}\n"
            "安装命令（使用 Houdini 自带 python）：\n"
            '  "<Houdini>/python311/python.exe" -m pip install --target "<此 lib 路径>" fastmcp'
        )


def start_in_houdini():
    """在 Houdini GUI 中启动 MCP 服务器（非阻塞）。

    适用于在 Houdini 的 Python Shell / Source Editor / shelf tool 中调用。
    服务器线程以 daemon 方式运行，由 Houdini GUI 事件循环维持生命周期。

    Returns:
        tuple[bool, str]: (是否成功, 描述信息)

    Example::

        import start_mcp_server
        ok, msg = start_mcp_server.start_in_houdini()
        print(ok, msg)
    """
    _setup_env()
    _check_dependencies()

    from houdini_agent.utils.mcp import (
        ensure_mcp_running,
        get_mcp_status,
    )

    ok, msg = ensure_mcp_running(auto_start=True)
    print(f"[MCP] start ok={ok} msg={msg}")

    status = get_mcp_status()
    print(f"[MCP] status={status}")

    if ok:
        print("[MCP] 在 Houdini GUI 中，服务器将在后台持续运行。")
    return ok, msg


def start_in_hython():
    """通过 hython.exe 启动 MCP 服务器（阻塞主线程）。

    适用于命令行通过 hython.exe 调用。主线程将持续阻塞，
    直到收到 Ctrl+C / KeyboardInterrupt 信号后优雅退出。

    Example::

        hython.exe start_mcp_server.py

    或者在 hython 交互式环境中::

        import start_mcp_server
        start_mcp_server.start_in_hython()  # 阻塞，Ctrl+C 退出
    """
    _setup_env()
    _check_dependencies()

    from houdini_agent.utils.mcp import (
        ensure_mcp_running,
        stop_mcp_server,
        get_mcp_status,
    )

    ok, msg = ensure_mcp_running(auto_start=True)
    print(f"[MCP] start ok={ok} msg={msg}")

    status = get_mcp_status()
    print(f"[MCP] status={status}")

    if not ok:
        sys.exit(2)

    print(f"[MCP] 服务器已启动：http://{status['host']}:{status['port']}/mcp/")
    print("[MCP] 按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MCP] 收到退出信号，正在停止...")
        ok2, msg2 = stop_mcp_server(timeout=5.0)
        print(f"[MCP] stop ok={ok2} msg={msg2}")


# ---------------------------------------------------------------------------
# 直接运行入口：自动检测环境选择合适的启动方式
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _setup_env()
    _check_dependencies()

    import hou  # type: ignore

    in_houdini_gui = bool(getattr(hou, "isUIAvailable", lambda: False)())

    if in_houdini_gui:
        start_in_houdini()
    else:
        start_in_hython()
