#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GodotBuddy v2.0 - 统一启动入口（交互式菜单 + 命令行）

功能：
  - 交互式菜单：GDScript 项目分析 / 引擎源码分析 / 技术导读 / Web 查看器
  - 命令行模式：支持 --source / --guide / --web 等参数直接执行

由 start_godotbuddy.bat 启动。
"""

import sys
import os
import io
import subprocess
import configparser
import shutil
import argparse
from datetime import datetime

# 修复 Windows GBK 控制台编码问题
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "Scripts")
sys.path.insert(0, SCRIPTS_DIR)


# ============================================================
# 配置加载
# ============================================================

def load_ini():
    """加载 config.ini 返回 ConfigParser 对象"""
    path = os.path.join(ROOT_DIR, "config.ini")
    if not os.path.exists(path):
        print(f"[ERROR] config.ini not found: {path}")
        sys.exit(1)
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    return cfg


# ============================================================
# 工具函数
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg="Press Enter to continue..."):
    input(f"\n  {msg}")


def run_python_script(script_name, args_list=None):
    """运行 Scripts/ 目录下的 Python 脚本"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"  [ERROR] Script not found: {script_path}")
        return False
    cmd = [sys.executable, script_path] + (args_list or [])
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    return result.returncode == 0


# ============================================================
# 技术导读生成
# ============================================================

def run_source_guide(cfg):
    """
    生成 Godot vs UE 技术导读文章。
    读取 [SourceGuide] + [KnotCLI] + [SourceAnalysis] 配置，
    构建 Prompt 并调用 knot-cli 生成完整文章。
    """
    import knot_cli_setup

    # 读取配置
    knot_cmd = cfg.get("KnotCLI", "command", fallback="knot-cli").strip()
    model = cfg.get("KnotCLI", "model", fallback="claude-4.6-opus").strip()
    user_rules = cfg.get("KnotCLI", "user_rules", fallback="").strip()
    timeout = cfg.getint("KnotCLI", "timeout", fallback=3600)

    source_dir = cfg.get("SourceAnalysis", "godot_source_dir", fallback="").strip()
    ue_source_dir = cfg.get("SourceAnalysis", "ue_source_dir", fallback="").strip()

    guide_prompt_file = cfg.get("SourceGuide", "prompt_file", fallback="Prompt/source_guide_prompt.md").strip()
    guide_output_dir = cfg.get("SourceGuide", "output_dir", fallback="Reports/GodotEngine/4.6.2").strip()
    guide_filename = cfg.get("SourceGuide", "output_filename",
                             fallback="Godot_4.6.2_Source_Guide_for_UE_Developers.md").strip()
    guide_cli_template = cfg.get("SourceGuide", "cli_args_template", fallback="").strip()

    # 验证
    if not source_dir or not os.path.isdir(source_dir):
        print(f"  [ERROR] Godot source dir not found: {source_dir}")
        return False

    # 准备输出目录
    abs_output_dir = os.path.join(ROOT_DIR, guide_output_dir) if not os.path.isabs(guide_output_dir) else guide_output_dir
    os.makedirs(abs_output_dir, exist_ok=True)
    report_path = os.path.join(abs_output_dir, guide_filename)

    # 加载 Prompt 模板并填充
    abs_prompt_template = os.path.join(ROOT_DIR, guide_prompt_file) if not os.path.isabs(guide_prompt_file) else guide_prompt_file
    if not os.path.exists(abs_prompt_template):
        print(f"  [ERROR] Prompt template not found: {abs_prompt_template}")
        return False

    with open(abs_prompt_template, "r", encoding="utf-8") as f:
        template = f.read()

    # 动态生成 target_reader 和 analysis_mode
    target_reader = (
        "目标读者是有 Unreal Engine 4 开发经验的游戏开发者。\n"
        "他们熟悉 UObject 反射系统、AActor/UComponent 世界构建模式、\n"
        "TSharedPtr 智能指针、Blueprint/C++ 混合开发、Chaos Physics、\n"
        "渲染线程和 RHI 抽象、GameplayAbilitySystem 等 UE 核心概念。\n"
        "对比时请多用 UE 概念类比帮助理解。"
    )

    if ue_source_dir and os.path.isdir(ue_source_dir):
        analysis_mode = (
            f"**交叉对比模式已启用**\n\n"
            f"Godot 源码: `{source_dir}`\n"
            f"UE 源码: `{ue_source_dir}`\n\n"
            f"你可以直接搜索和阅读两个引擎的源码进行对比分析。\n"
            f"请在讲解每个 Godot 设计概念时，同时查阅 UE 对应模块的源码，\n"
            f"给出源码级别的交叉对比。"
        )
    else:
        analysis_mode = (
            "**单引擎分析模式**\n\n"
            "未配置 UE 引擎源码目录，将基于 UE 公开文档和常识进行概念对比。"
        )

    # 填充模板并保存到 Cache
    cache_dir = os.path.join(ROOT_DIR, "Cache")
    os.makedirs(cache_dir, exist_ok=True)
    filled_prompt = template.format(
        target_reader=target_reader,
        analysis_mode=analysis_mode,
        report_path=report_path.replace("\\", "/"),
    )
    prompt_file = os.path.join(cache_dir, f"guide_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(filled_prompt)

    # 检查 knot-cli
    available, version_info = knot_cli_setup.is_knot_cli_installed(knot_cmd)
    if not available:
        print(f"  [ERROR] {knot_cmd} not available: {version_info}")
        print(f"  [INFO] Prompt saved to: {prompt_file}")
        return False

    # 构建 knot-cli 命令
    if guide_cli_template:
        args_str = guide_cli_template.format(
            prompt_file=prompt_file.replace("\\", "/"),
            report_path=report_path.replace("\\", "/"),
            source_dir=source_dir.replace("\\", "/"),
            ue_source_dir=ue_source_dir.replace("\\", "/") if ue_source_dir else "",
            godotbuddy_dir=ROOT_DIR.replace("\\", "/"),
            model=model,
            user_rules=user_rules.replace("\\", "/") if user_rules else "",
        )
        full_command = f"{knot_cmd} {args_str}"
    else:
        # 默认命令
        ws_args = f'-w "{source_dir.replace(chr(92), "/")}"'
        if ue_source_dir and os.path.isdir(ue_source_dir):
            ws_args += f' -w "{ue_source_dir.replace(chr(92), "/")}"'
        ws_args += f' -w "{ROOT_DIR.replace(chr(92), "/")}"'
        full_command = (
            f'{knot_cmd} chat {ws_args} --codebase --model "{model}"'
            f' -p "Read file {prompt_file.replace(chr(92), "/")} for the complete task instructions.'
            f' Write the full technical guide article to: {report_path.replace(chr(92), "/")}"'
        )

    # 打印信息
    print()
    print("=" * 66)
    print("  GodotBuddy - Source Guide Generator")
    print("=" * 66)
    print(f"  Godot  : {source_dir}")
    if ue_source_dir and os.path.isdir(ue_source_dir):
        print(f"  UE     : {ue_source_dir}")
        print(f"  Mode   : Cross-comparison (Godot vs UE)")
    else:
        print(f"  Mode   : Single-engine analysis")
    print(f"  Model  : {model}")
    print(f"  Output : {report_path}")
    print(f"  Timeout: {timeout}s")
    print("=" * 66)
    print()

    # 执行
    try:
        process = subprocess.Popen(
            full_command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=source_dir,
        )
        try:
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    print(f"    {line}")
        except Exception:
            pass
        process.wait(timeout=timeout)

        if process.returncode == 0 and os.path.exists(report_path):
            size = os.path.getsize(report_path)
            print(f"\n  [OK] Guide generated: {report_path} ({size:,} bytes)")
            return True
        else:
            print(f"\n  [FAIL] Return code: {process.returncode}")
            return False
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"\n  [FAIL] Timeout ({timeout}s)")
        return False
    except Exception as e:
        print(f"\n  [FAIL] {e}")
        return False


# ============================================================
# 交互式菜单
# ============================================================

def show_main_menu():
    clear_screen()
    print()
    print("  +----------------------------------------------------------+")
    print("  |              GodotBuddy v2.0 - Analysis Hub              |")
    print("  |        Powered by knot-cli AI Analysis Engine            |")
    print("  +----------------------------------------------------------+")
    print("  |                                                          |")
    print("  |   [1] GDScript Project Analysis                          |")
    print("  |       Analyze Godot game project GDScript code           |")
    print("  |                                                          |")
    print("  |   [2] Godot Engine Source Analysis (per module)          |")
    print("  |       Analyze Godot 4.6.2 C++ source by module          |")
    print("  |                                                          |")
    print("  |   [3] Source Guide (Godot vs UE overview article)        |")
    print("  |       Generate a full technical guide for UE devs        |")
    print("  |                                                          |")
    print("  |   [4] Web Report Viewer                                  |")
    print("  |       Launch browser to view analysis reports            |")
    print("  |                                                          |")
    print("  |   [5] View Progress (OVERVIEW)                           |")
    print("  |       View engine source analysis plan and progress      |")
    print("  |                                                          |")
    print("  |   [0] Exit                                               |")
    print("  |                                                          |")
    print("  +----------------------------------------------------------+")
    print()
    return input("  Select [0-5]: ").strip()


def show_project_menu():
    clear_screen()
    print()
    print("  +----------------------------------------------------------+")
    print("  |            GDScript Project Analysis                     |")
    print("  +----------------------------------------------------------+")
    print("  |                                                          |")
    print("  |   [1] Analyze all configured projects                    |")
    print("  |   [2] Analyze specific project (from config.ini)         |")
    print("  |   [3] Analyze specific directory (input path)            |")
    print("  |   [4] Scan only (no AI analysis)                         |")
    print("  |   [5] Force re-analyze all projects                      |")
    print("  |                                                          |")
    print("  |   [0] Back to main menu                                  |")
    print("  +----------------------------------------------------------+")
    print()
    return input("  Select [0-5]: ").strip()


def show_source_menu(cfg):
    godot_dir = cfg.get("SourceAnalysis", "godot_source_dir", fallback="(not set)")
    ue_dir = cfg.get("SourceAnalysis", "ue_source_dir", fallback="(not set)")
    clear_screen()
    print()
    print("  +----------------------------------------------------------+")
    print("  |            Godot Engine Source Analysis (per module)      |")
    print(f"  |  Godot: {godot_dir[:49]:<49s} |")
    print(f"  |  UE:    {ue_dir[:49]:<49s} |")
    print("  +----------------------------------------------------------+")
    print("  |                                                          |")
    print("  |   [1] Full analysis (all 24 modules)                     |")
    print("  |   [2] Select modules to analyze                          |")
    print("  |   [3] Scan only (no knot-cli)                            |")
    print("  |   [4] Core modules (Object/Rendering/SceneTree/Script)   |")
    print("  |   [5] View module list                                   |")
    print("  |                                                          |")
    print("  |   [0] Back to main menu                                  |")
    print("  +----------------------------------------------------------+")
    print()
    return input("  Select [0-5]: ").strip()


MODULE_LIST = """
  +--------------------------------------------------------------+
  |  ID                        Name              Priority        |
  +--------------------------------------------------------------+
  |  01_core_foundation        Core Foundation   [*****]         |
  |  02_object_system       *  Object System     [*****]         |
  |  03_memory_management      Memory Mgmt       [****]          |
  |  04_math_library           Math Library       [****]          |
  |  05_io_system              I/O System         [***]           |
  |  06_rendering_server    *  Rendering Server   [*****]         |
  |  07_graphics_drivers       Graphics Drivers   [****]          |
  |  08_scene_tree_2d          Scene Tree 2D      [****]          |
  |  09_scene_tree_3d          Scene Tree 3D      [****]          |
  |  10_scene_main          *  Scene Tree Core    [*****]         |
  |  11_physics_2d             Physics 2D         [***]           |
  |  12_physics_3d             Physics 3D         [***]           |
  |  13_script_system       *  Script System      [*****]         |
  |  14_animation_system       Animation          [***]           |
  |  15_resource_system        Resource System    [****]          |
  |  16_import_pipeline        Import Pipeline    [***]           |
  |  17_audio_system           Audio System       [****]          |
  |  18_input_system           Input System       [***]           |
  |  19_ui_system              UI System          [***]           |
  |  20_navigation             Navigation         [****]          |
  |  21_editor_framework       Editor Framework   [****]          |
  |  22_networking             Networking         [****]          |
  |  23_platform_abstraction   Platform Layer     [*****]         |
  |  24_optional_modules       Optional Modules   [*****]         |
  +--------------------------------------------------------------+
    * = Key highlighted module
"""


def menu_loop():
    """交互式菜单主循环"""
    cfg = load_ini()

    while True:
        choice = show_main_menu()

        # [1] GDScript 项目分析
        if choice == "1":
            while True:
                pc = show_project_menu()
                if pc == "1":
                    run_python_script("godotbuddy.py")
                    pause()
                elif pc == "2":
                    name = input("  Enter project name ([Project:xxx] in config.ini): ").strip()
                    if name:
                        run_python_script("godotbuddy.py", ["--project", name])
                    pause()
                elif pc == "3":
                    path = input("  Enter Godot project directory path: ").strip()
                    if path:
                        run_python_script("godotbuddy.py", ["--dir", path])
                    pause()
                elif pc == "4":
                    run_python_script("godotbuddy.py", ["--scan-only"])
                    pause()
                elif pc == "5":
                    run_python_script("godotbuddy.py", ["--force"])
                    pause()
                elif pc == "0":
                    break
                else:
                    print("  [!] Invalid choice")
                    pause()

        # [2] 源码逐模块分析
        elif choice == "2":
            while True:
                sc = show_source_menu(cfg)
                if sc == "1":
                    print("\n  [INFO] Starting full analysis, this may take a long time...")
                    run_python_script("godot_source_analyzer.py")
                    pause()
                elif sc == "2":
                    print()
                    print("  Available module IDs:")
                    print("    01_core_foundation     02_object_system       03_memory_management")
                    print("    04_math_library        05_io_system           06_rendering_server")
                    print("    07_graphics_drivers    08_scene_tree_2d       09_scene_tree_3d")
                    print("    10_scene_main          11_physics_2d          12_physics_3d")
                    print("    13_script_system       14_animation_system    15_resource_system")
                    print("    16_import_pipeline     17_audio_system        18_input_system")
                    print("    19_ui_system           20_navigation          21_editor_framework")
                    print("    22_networking          23_platform_abstraction 24_optional_modules")
                    print()
                    mods = input("  Enter module IDs (comma-separated, e.g. 02,06,13): ").strip()
                    if mods:
                        run_python_script("godot_source_analyzer.py", ["--modules", mods])
                    pause()
                elif sc == "3":
                    run_python_script("godot_source_analyzer.py", ["--scan-only"])
                    pause()
                elif sc == "4":
                    print("\n  [INFO] Analyzing core modules: Object, Rendering, SceneTree, Script...")
                    run_python_script("godot_source_analyzer.py",
                                     ["--modules", "02_object_system,06_rendering_server,10_scene_main,13_script_system"])
                    pause()
                elif sc == "5":
                    print(MODULE_LIST)
                    pause()
                elif sc == "0":
                    break
                else:
                    print("  [!] Invalid choice")
                    pause()

        # [3] 技术导读文章
        elif choice == "3":
            clear_screen()
            print()
            print("  +----------------------------------------------------------+")
            print("  |     Source Guide: Godot 4.6.2 for UE Developers          |")
            print("  +----------------------------------------------------------+")
            print("  |                                                          |")
            print("  |  Generate a comprehensive technical guide article         |")
            print("  |  covering Godot 4.6.2 source architecture,               |")
            print("  |  cross-compared with Unreal Engine.                      |")
            print("  |                                                          |")
            print("  |  Output: Reports/GodotEngine/4.6.2/                      |")
            print("  |                                                          |")
            print("  |  [1] Generate guide (may take 20-40 min)                 |")
            print("  |  [0] Back to main menu                                   |")
            print("  |                                                          |")
            print("  +----------------------------------------------------------+")
            print()
            gc = input("  Select [0-1]: ").strip()
            if gc == "1":
                cfg = load_ini()  # 重新加载以获取最新配置
                run_source_guide(cfg)
                pause()

        # [4] Web 报告查看器
        elif choice == "4":
            print("\n  [INFO] Starting Web Report Viewer...")
            print("  [INFO] Open browser: http://localhost:5000")
            run_python_script("godot_source_analyzer.py", ["--web"])
            pause()

        # [5] 查看分析进度
        elif choice == "5":
            clear_screen()
            overview_path = os.path.join(ROOT_DIR, "Reports", "GodotEngine", "OVERVIEW.md")
            if os.path.exists(overview_path):
                print()
                print("  +----------------------------------------------------------+")
                print("  |     Godot Engine Source Analysis - Plan and Progress     |")
                print("  +----------------------------------------------------------+")
                print()
                with open(overview_path, "r", encoding="utf-8", errors="replace") as f:
                    print(f.read())
            else:
                print(f"\n  [WARN] OVERVIEW.md not found: {overview_path}")
                print("  [INFO] Please run source scan first to initialize")
            pause()

        # [0] 退出
        elif choice == "0":
            print("\n  Bye!")
            break

        else:
            print("  [!] Invalid choice, please try again")
            pause()


# ============================================================
# 命令行模式
# ============================================================

def cli_mode():
    """命令行参数解析与分派"""
    parser = argparse.ArgumentParser(
        description="GodotBuddy v2.0 - Godot Analysis Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  start_godotbuddy.py                                  Interactive menu
  start_godotbuddy.py --project TPS-Demo               Analyze project
  start_godotbuddy.py --source                         Full source analysis
  start_godotbuddy.py --source --modules 02,06,13      Specific modules
  start_godotbuddy.py --source --scan-only             Scan source only
  start_godotbuddy.py --guide                          Generate tech guide
  start_godotbuddy.py --web                            Start Web viewer
        """,
    )
    parser.add_argument("--source", "-src", action="store_true",
                        help="Godot engine C++ source analysis mode")
    parser.add_argument("--guide", "-g", action="store_true",
                        help="Generate Godot vs UE technical guide article")
    parser.add_argument("--web", "-w", action="store_true",
                        help="Start Web report viewer")
    parser.add_argument("--modules", "-m", type=str, default=None,
                        help="Comma-separated module IDs (for --source)")
    parser.add_argument("--scan-only", "-s", action="store_true",
                        help="Scan only, no AI analysis")
    parser.add_argument("--project", "-p", type=str, default=None,
                        help="Analyze specific project")
    parser.add_argument("--dir", "-d", type=str, default=None,
                        help="Analyze specific directory")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force re-analysis")

    args = parser.parse_args()

    # 无参数 → 交互式菜单
    if len(sys.argv) <= 1:
        menu_loop()
        return

    # --guide 模式
    if args.guide:
        cfg = load_ini()
        success = run_source_guide(cfg)
        sys.exit(0 if success else 1)

    # --web 模式
    if args.web:
        run_python_script("godot_source_analyzer.py", ["--web"])
        return

    # --source 模式
    if args.source:
        extra_args = []
        if args.modules:
            extra_args += ["--modules", args.modules]
        if args.scan_only:
            extra_args.append("--scan-only")
        if args.force:
            extra_args.append("--force")
        run_python_script("godot_source_analyzer.py", extra_args)
        return

    # 默认：项目分析模式
    extra_args = []
    if args.project:
        extra_args += ["--project", args.project]
    if args.dir:
        extra_args += ["--dir", args.dir]
    if args.scan_only:
        extra_args.append("--scan-only")
    if args.force:
        extra_args.append("--force")
    run_python_script("godotbuddy.py", extra_args)


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    cli_mode()
