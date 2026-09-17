@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python verify.py
) else (
  py -3 verify.py
)
set QEL_REPLAY_EXIT=%errorlevel%
echo.
if not "%QEL_REPLAY_EXIT%"=="0" echo Replay failed. Review the message above; existing reports may be from an earlier run.
pause
exit /b %QEL_REPLAY_EXIT%
