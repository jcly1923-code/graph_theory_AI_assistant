@echo off
REM 打包前请在项目根目录执行: python utils/download.py（生成 local_models）
REM 详细说明见 readme.md「Windows 打包（PyInstaller）」
setlocal
cd /d "%~dp0"

where pyinstaller >nul 2>nul
if %errorlevel% equ 0 (
  pyinstaller -F ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "local_models;local_models" ^
    --hidden-import=flask ^
    --clean ^
    app.py
) else (
  python -m PyInstaller -F ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "local_models;local_models" ^
    --hidden-import=flask ^
    --clean ^
    app.py
)

if %errorlevel% neq 0 (
  echo.
  echo [ERROR] 打包失败。请确认当前 Python 环境已安装 PyInstaller。
)

pause