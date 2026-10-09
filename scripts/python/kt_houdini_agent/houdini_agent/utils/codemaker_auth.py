# -*- coding: utf-8 -*-
"""
CodeMaker CLI 认证桥接模块。

CodeMaker CLI 的角色是纯认证中间件：
  - 检测/安装 CodeMaker CLI
  - 启动 CLI 让用户完成网页 OAuth 登录
  - CLI 将凭证写入 auth.json
  - 我们读 auth.json 获取 API Key，然后直连 OpenAI 兼容 API

所有函数均为同步阻塞调用；调用方应放在后台线程中执行以避免冻结 UI。
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


# ============================================================
# 常量
# ============================================================

CODEMAKER_API_URL = "https://api-code-maker.nie.netease.com/openai/v1/chat/completions"
CODEMAKER_DEFAULT_MODEL = "claude-opus-5"

# Windows PowerShell 安装命令
_INSTALL_PS1_URL = "https://codemaker.netease.com/package/codemaker-cli/install.ps1"
_INSTALL_SH_URL = "https://codemaker.netease.com/package/codemaker-cli/install.sh"


# ============================================================
# 路径辅助
# ============================================================


def _auth_json_path() -> Path:
    """auth.json 完整路径（跨平台）。

    Windows: %USERPROFILE%/.local/share/codemaker/auth.json
    *nix:    ~/.local/share/codemaker/auth.json
    """
    if os.name == "nt":
        user_profile = os.environ.get("USERPROFILE")
        base = Path(user_profile) if user_profile else Path.home()
    else:
        base = Path.home()
    return base / ".local" / "share" / "codemaker" / "auth.json"


def find_codemaker_exe() -> Optional[str]:
    """查找 codemaker 可执行文件，返回路径或 None。"""
    home = Path.home()

    if os.name == "nt":
        candidates = [
            home / ".codemaker" / "bin" / "codemaker.exe",
            home / ".local" / "share" / "codemaker" / "codemaker.exe",
            home / "AppData" / "Local" / "codemaker" / "codemaker.exe",
            home / "AppData" / "Roaming" / "npm" / "codemaker.cmd",
        ]
    else:
        candidates = [
            home / ".codemaker" / "bin" / "codemaker",
            home / ".local" / "share" / "codemaker" / "codemaker",
            home / ".local" / "bin" / "codemaker",
        ]

    for p in candidates:
        try:
            if p.exists():
                return str(p)
        except OSError:
            continue

    # 兜底：PATH 查找
    found = shutil.which("codemaker")
    return found


# ============================================================
# 读 auth.json
# ============================================================


def _read_auth_data() -> Optional[dict]:
    """读取并解析 auth.json，返回 dict 或 None。"""
    auth_path = _auth_json_path()
    if not auth_path.exists():
        return None
    try:
        return json.loads(auth_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def is_token_expired(data: Optional[dict] = None, skew_sec: int = 120) -> bool:
    """判断 auth.json 中的 access token 是否已过期（或临近过期）。

    依据 ["netease-codemaker"]["expire"]（毫秒）。缺失该字段时视为“未过期”，
    交由服务端判定。skew_sec 提前量避免边界抖动。
    """
    if data is None:
        data = _read_auth_data()
    if not data:
        return True
    node = data.get("netease-codemaker") or {}
    expire_ms = node.get("expire")
    if not expire_ms:
        return False
    try:
        now_ms = time.time() * 1000.0
        return now_ms >= (float(expire_ms) - skew_sec * 1000.0)
    except (TypeError, ValueError):
        return False


def refresh_codemaker_token(timeout: int = 40) -> bool:
    """用 refresh_key 静默刷新 token（不弹窗、不需浏览器）。

    通过运行 CodeMaker CLI 的只读命令（quota）触发 CLI 内部的 token 刷新，
    刷新后 CLI 会把新的 access_token/expire 写回 auth.json。

    返回是否刷新成功（returncode == 0）。
    """
    exe = find_codemaker_exe()
    if not exe:
        return False
    try:
        kwargs = {"capture_output": True, "text": True, "timeout": timeout}
        if os.name == "nt":
            # 避免弹出控制台窗口
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        result = subprocess.run([exe, "quota"], **kwargs)
        return result.returncode == 0
    except Exception:
        return False


def read_codemaker_api_key(auto_refresh: bool = True) -> Optional[str]:
    """从 CodeMaker CLI 的 auth.json 读取 API Key（必要时自动刷新）。

    路径: ~/.local/share/codemaker/auth.json
    字段: ["netease-codemaker"]["key"]

    token 过期时会尝试用 refresh_key 静默刷新一次；刷新失败且仍过期则返回 None
    （提示上层需要重新登录）。返回 None 表示未登录 / auth.json 缺失 / 已失效。
    """
    data = _read_auth_data()
    if not data:
        return None

    def _extract(d):
        node = (d or {}).get("netease-codemaker") or {}
        key = node.get("key") or node.get("access_token") or ""
        return key.strip() or None

    key = _extract(data)
    if not key:
        return None

    if auto_refresh and is_token_expired(data):
        if refresh_codemaker_token():
            data2 = _read_auth_data()
            key2 = _extract(data2)
            if key2 and not is_token_expired(data2):
                return key2
        # 刷新失败且仍过期 → 需要重新登录
        if is_token_expired(data):
            return None

    return key


# ============================================================
# 安装 CLI（同步阻塞）
# ============================================================


def install_codemaker_sync(timeout: int = 180) -> Tuple[bool, str]:
    """同步安装 CodeMaker CLI。返回 (成功, 信息/错误)。

    注意：会阻塞当前线程数十秒到几分钟。请放在 worker 线程调用。
    """
    try:
        if sys.platform == "win32":
            cmd = [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"irm {_INSTALL_PS1_URL} | iex",
            ]
        else:
            cmd = [
                "bash",
                "-c",
                f"curl -fsSL {_INSTALL_SH_URL} | bash",
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            err = (
                (result.stderr or "").strip()
                or (result.stdout or "").strip()
                or "Install command failed"
            )
            return False, err
        return True, "Installed"
    except subprocess.TimeoutExpired:
        return False, f"Install timed out after {timeout}s"
    except FileNotFoundError as e:
        return False, f"Missing required executable: {e}"
    except Exception as e:
        return False, str(e)


# ============================================================
# 启动 CLI 登录（阻塞，等待用户完成网页 OAuth）
# ============================================================


def launch_codemaker_login(exe_path: str, timeout: int = 300) -> Tuple[bool, str]:
    """启动 CodeMaker CLI，让用户在浏览器完成 OAuth 登录。

    CLI 会自动打开浏览器；登录成功后写入 auth.json，CLI 进程退出。
    本函数阻塞直到 CLI 退出或超时。

    返回 (成功, 信息/错误)。
    """
    try:
        if sys.platform == "win32":
            # 在新的 cmd 窗口中运行 codemaker，确保用户能看到 CLI 输出
            # /k 让窗口在 codemaker 退出后保持，便于查看错误信息
            cmd = ["cmd.exe", "/c", "start", "/wait", "cmd.exe", "/k", exe_path]
        else:
            cmd = [exe_path]

        result = subprocess.run(cmd, timeout=timeout)
        if result.returncode != 0:
            return False, f"CodeMaker exited with code {result.returncode}"
        return True, "Login finished"
    except subprocess.TimeoutExpired:
        return False, f"Login timed out after {timeout}s"
    except FileNotFoundError:
        return False, f"CodeMaker executable not found: {exe_path}"
    except Exception as e:
        return False, str(e)


# ============================================================
# 一键 Setup 流程（可选，给 UI 调用）
# ============================================================


def ensure_codemaker_ready(
    install_timeout: int = 180,
    login_timeout: int = 300,
    progress_cb=None,
) -> Tuple[bool, str, Optional[str]]:
    """完整流程：检测 -> 安装 -> 登录 -> 读 Key。

    Args:
        install_timeout: 安装超时秒数
        login_timeout: 登录超时秒数
        progress_cb: 可选的进度回调 callable(step_name: str)

    Returns:
        (success, message, api_key)
    """

    def _log(msg: str):
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception:
                pass

    # 快速路径：已登录
    key = read_codemaker_api_key()
    if key:
        _log("Already logged in")
        return True, "Already logged in", key

    # 检测安装
    _log("Locating CodeMaker CLI...")
    exe_path = find_codemaker_exe()

    if not exe_path:
        _log("CodeMaker CLI not found, installing...")
        ok, err = install_codemaker_sync(timeout=install_timeout)
        if not ok:
            return False, f"Install failed: {err}", None
        exe_path = find_codemaker_exe()
        if not exe_path:
            return (
                False,
                "Installed but executable not found, please restart terminal",
                None,
            )

    # 启动登录
    _log("Launching CodeMaker for login...")
    ok, err = launch_codemaker_login(exe_path, timeout=login_timeout)
    if not ok:
        return False, f"Login failed: {err}", None

    # 验证
    _log("Verifying auth.json...")
    key = read_codemaker_api_key()
    if not key:
        return False, "Login finished but API Key not found in auth.json", None

    return True, "Login successful", key
