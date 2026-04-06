@echo off
:: ============================================================
:: GodotBuddy v2.0 - Launcher
:: All logic is in start_godotbuddy.py
:: ============================================================
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

python "%SCRIPT_DIR%\start_godotbuddy.py" %*
if %errorlevel% neq 0 pause
