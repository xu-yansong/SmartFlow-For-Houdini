@echo off
REM ---------------------------------------------------------------
REM  KaiTian Houdini-Agent launcher.
REM  All third-party deps ship inside lib\, so the machine only needs
REM  a 64-bit Python 3.10+ -- nothing installed, no network, no pip.
REM  NOTE: this file is deliberately ASCII-only. cmd.exe reads .bat with
REM  the OEM codepage (cp936 here); UTF-8 Chinese would make a multi-byte
REM  char swallow the next ASCII byte and corrupt "else"/"errorlevel".
REM ---------------------------------------------------------------
cd /d "%~dp0"

set "HAGENT_BOOT="
set "HAGENT_BOOT_ARGS="

if defined HAGENT_PYTHON (
    set "HAGENT_BOOT=%HAGENT_PYTHON%"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "HAGENT_BOOT=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set "HAGENT_BOOT=py"
            set "HAGENT_BOOT_ARGS=-3"
        )
    )
)

if not defined HAGENT_BOOT (
    echo [ERROR] Python not found. Install a 64-bit Python 3.10 or newer,
    echo         or set HAGENT_PYTHON to a python.exe path.
    pause
    exit /b 1
)

echo [INFO] Launching Houdini Agent with "%HAGENT_BOOT%" %HAGENT_BOOT_ARGS%
"%HAGENT_BOOT%" %HAGENT_BOOT_ARGS% launcher.py %*
set "HAGENT_EXIT=%ERRORLEVEL%"
if not "%HAGENT_EXIT%"=="0" echo [ERROR] launcher.py exited with code %HAGENT_EXIT%

pause
exit /b %HAGENT_EXIT%