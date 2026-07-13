@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
set "DIST=%ROOT%dist\CN8000A-KVM-Portable-Win64"
set "CACHE=%ROOT%.cache"

if not exist "%CACHE%" mkdir "%CACHE%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\download-runtime.ps1"
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $py='%ROOT%python-win'; if (-not (Test-Path \"$py\python.exe\")) { bash '%ROOT%scripts\download-python-runtime.sh' windows } }"
if not exist "%ROOT%python-win\python.exe" (
  echo Download python runtime first: scripts\download-python-runtime.sh windows
  exit /b 1
)

if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%DIST%"
mkdir "%DIST%\app"

copy /Y "%ROOT%launcher.py" "%DIST%\app\" >nul
copy /Y "%ROOT%cn8000_client.py" "%DIST%\app\" >nul
copy /Y "%ROOT%widgets.py" "%DIST%\app\" >nul
copy /Y "%ROOT%ui_theme.py" "%DIST%\app\" >nul
xcopy /E /I /Y "%ROOT%resources" "%DIST%\app\resources" >nul
xcopy /E /I /Y "%ROOT%runtime" "%DIST%\app\runtime" >nul
xcopy /E /I /Y "%ROOT%python-win" "%DIST%\app\python" >nul

> "%DIST%\CN8000A-KVM.bat" (
  echo @echo off
  echo setlocal
  echo set "APP_DIR=%%~dp0app"
  echo set "PYTHONPATH=%%APP_DIR%%"
  echo cd /d "%%APP_DIR%%"
  echo start "" "%%APP_DIR%%\python\pythonw.exe" "%%APP_DIR%%\launcher.py"
)

echo Built portable Windows folder: %DIST%
echo Run: %DIST%\CN8000A-KVM.bat
