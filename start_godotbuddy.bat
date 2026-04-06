@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ============================================================
:: GodotBuddy v2.0 - 统一启动入口
::   支持两种模式：
::     1. 项目分析 (Project Analysis) - 分析 GDScript 游戏项目
::     2. 源码分析 (Source Analysis)   - 分析 Godot 引擎 C++ 源码
:: ============================================================

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   GodotBuddy v2.0
echo   + Project Analyzer: GDScript game project analysis
echo   + Source Analyzer : Godot Engine C++ source analysis
echo   + Web Viewer      : Interactive report browser
echo ============================================================
echo.

:: 解析命令行参数
set "MODE=project"
set "ARGS="

:parse_args
if "%~1"=="" goto done_parse
if /i "%~1"=="--source" (
    set "MODE=source"
    shift
    goto re_parse
)
if /i "%~1"=="-src" (
    set "MODE=source"
    shift
    goto re_parse
)
if /i "%~1"=="--web" (
    set "MODE=web"
    shift
    goto re_parse
)
if /i "%~1"=="-w" (
    set "MODE=web"
    shift
    goto re_parse
)
if /i "%~1"=="--help" (
    goto show_help
)
if /i "%~1"=="-h" (
    goto show_help
)
set "ARGS=!ARGS! %1"
:re_parse
shift
goto parse_args

:done_parse

:: 分派到对应模式
if "%MODE%"=="project" goto mode_project
if "%MODE%"=="source" goto mode_source
if "%MODE%"=="web" goto mode_web

:: ============================================================
:: 模式 1: GDScript 项目分析（原始功能）
:: ============================================================
:mode_project
echo [Mode] GDScript Project Analysis
echo.
python "%SCRIPT_DIR%\Scripts\godotbuddy.py" !ARGS!
goto end

:: ============================================================
:: 模式 2: Godot 引擎源码分析（新功能）
:: ============================================================
:mode_source
echo [Mode] Godot Engine Source Code Analysis
echo.
python "%SCRIPT_DIR%\Scripts\godot_source_analyzer.py" !ARGS!
goto end

:: ============================================================
:: 模式 3: Web 展示平台
:: ============================================================
:mode_web
echo [Mode] Web Report Viewer
echo.
python "%SCRIPT_DIR%\Scripts\godot_source_analyzer.py" --web
goto end

:: ============================================================
:: 帮助信息
:: ============================================================
:show_help
echo.
echo Usage: start_godotbuddy [mode] [options]
echo.
echo Modes:
echo   (default)         GDScript project analysis (original behavior)
echo   --source, -src     Godot engine C++ source code analysis
echo   --web, -w          Start web report viewer (http://localhost:5000)
echo.
echo Options for Project Analysis:
echo   --project NAME    Analyze specific project from config.ini
echo   --dir PATH        Analyze a specific Godot project directory
echo   --scan-only       Scan only, no AI analysis
echo   --force           Force re-analysis
echo.
echo Options for Source Analysis:
echo   --source PATH     Override Godot source directory
echo   --modules ID,ID   Analyze specific modules only
echo   --scan-only       Scan only, no AI analysis
echo   --web             Start web viewer
echo.
echo Examples:
echo   start_godotbuddy                              ^| Analyze all configured projects
echo   start_godotbuddy --source                      ^| Analyze Godot engine source
echo   start_godotbuddy --source --scan-only           ^| Scan engine source only
echo   start_godotbuddy --source --modules 02,06,13    ^| Analyze specific modules
echo   start_godotbuddy --web                         ^| Start web viewer
echo.
pause
exit /b 0

:end
echo.
pause
