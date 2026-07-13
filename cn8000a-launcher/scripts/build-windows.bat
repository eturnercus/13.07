@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
set "DIST=%ROOT%dist\CN8000A-KVM-Portable-Win64"
set "CACHE=%ROOT%.cache"

if not exist "%CACHE%" mkdir "%CACHE%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\download-runtime.ps1"
if errorlevel 1 exit /b 1

if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%DIST%"
mkdir "%DIST%\app"

copy /Y "%ROOT%launcher.py" "%DIST%\app\" >nul
copy /Y "%ROOT%cn8000_client.py" "%DIST%\app\" >nul
xcopy /E /I /Y "%ROOT%resources" "%DIST%\app\resources" >nul
xcopy /E /I /Y "%ROOT%runtime" "%DIST%\app\runtime" >nul

> "%DIST%\CN8000A-KVM.bat" (
  echo @echo off
  echo setlocal
  echo set "APP_DIR=%%~dp0app"
  echo set "PYTHONPATH=%%APP_DIR%%"
  echo cd /d "%%APP_DIR%%"
  echo start "" "%%APP_DIR%%\runtime\bin\pythonw.exe" "%%APP_DIR%%\launcher.py" 2^>nul ^|^| py -3 "%%APP_DIR%%\launcher.py"
)

echo Built portable Windows folder: %DIST%
echo Run: %DIST%\CN8000A-KVM.bat
