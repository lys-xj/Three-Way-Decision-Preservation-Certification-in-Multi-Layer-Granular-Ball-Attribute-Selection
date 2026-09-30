@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  py -3.12 start.py
  goto finished
)
set "PAPER_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PAPER_PYTHON%" (
  "%PAPER_PYTHON%" start.py
  goto finished
)
python -c "import sys; assert sys.version_info >= (3,12)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 or later is required. Please install it and reopen this menu.
  goto finished
)
python start.py
:finished
pause
