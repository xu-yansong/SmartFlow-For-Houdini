@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo   Updating Git repository to latest...
echo ========================================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Current directory is not a git repository.
    goto :end
)

REM Record local changes before update
set "HAS_LOCAL_CHANGES="
for /f "delims=" %%i in ('git status --porcelain') do set "HAS_LOCAL_CHANGES=1"
if defined HAS_LOCAL_CHANGES (
    echo [INFO] Local uncommitted changes detected. They will be
    echo        auto-stashed before update and restored afterward.
    echo.
)

REM Record stash count before update (to detect leftover autostash on conflict)
set "STASH_BEFORE=0"
for /f %%c in ('git stash list ^| find /c /v ""') do set "STASH_BEFORE=%%c"

echo [1/3] Fetching remote changes...
git fetch --all --prune
if errorlevel 1 goto :fail

echo.
echo [2/3] Pulling latest changes (rebase + autostash)...
git pull --rebase --autostash
if errorlevel 1 goto :conflict

echo.
echo [3/3] Updating submodules (if any)...
git submodule update --init --recursive

REM Verify autostash was successfully restored
set "STASH_AFTER=0"
for /f %%c in ('git stash list ^| find /c /v ""') do set "STASH_AFTER=%%c"
if %STASH_AFTER% GTR %STASH_BEFORE% goto :stashleft

echo.
echo ========================================
echo   Update completed successfully!
if defined HAS_LOCAL_CHANGES echo   Your local changes were restored.
echo ========================================
goto :end

:conflict
echo.
echo ========================================
echo   [WARN] Update stopped due to a CONFLICT.
echo ========================================
echo   Your local changes are SAFE - nothing was lost.
echo.
echo   The rebase/restore hit a conflict. To recover:
echo     1. Run:  git status          (see conflicted files)
echo     2. Fix the conflicts by hand, then
echo        git add ^<files^> ^&^& git rebase --continue
echo     3. Or abort everything:  git rebase --abort
echo.
echo   If your changes were stashed, run:  git stash list
echo   to view them, and:  git stash pop   to restore.
goto :end

:stashleft
echo.
echo ========================================
echo   [WARN] Update done, but your local changes could NOT
echo          be auto-restored due to a conflict.
echo ========================================
echo   Your changes are SAFE in the stash - nothing was lost.
echo   Restore them manually:
echo     git stash list      (view saved changes)
echo     git stash pop       (re-apply and resolve conflicts)
goto :end

:fail
echo.
echo ========================================
echo   [ERROR] Fetch failed. Check network/remote and retry.
echo ========================================

:end
echo.
pause
endlocal
