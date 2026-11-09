@echo off
REM Builds GhostInstaller.exe on Windows. Needs Python 3.10+ from python.org (tick "Add Python to PATH").
cd /d "%~dp0"
python -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto fail
python -m PyInstaller --onefile --noconsole --name GhostInstaller --add-data "ghost-26.2.jar;." ghost_installer.py
if errorlevel 1 goto fail
echo.
echo Done. Your installer is dist\GhostInstaller.exe
pause
exit /b 0
:fail
echo.
echo Build failed. Make sure Python is installed and on PATH.
pause
exit /b 1
