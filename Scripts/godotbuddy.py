#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GodotBuddy 主入口脚本 (godotbuddy.py)

功能：
  1. 读取 config.ini 中的全局配置和项目配置
  2. 扫描 Godot 项目结构（GDScript、场景、资源等）
  3. 构建分析上下文 Prompt
  4. 调用 knot-cli（AI 分析引擎）生成分析报告
  5. 报告输出到 Reports/ 目录

使用方式：
  python godotbuddy.py                         # 分析所有配置项目
  python godotbuddy.py --project XXX           # 只分析指定项目
  python godotbuddy.py --dir <项目目录>         # 分析指定目录的 Godot 项目
  python godotbuddy.py --scan-only             # 仅扫描项目结构，不进行 AI 分析
  python godotbuddy.py --force                 # 强制重新分析

依赖：仅使用 Python 标准库 + 同目录下的模块
"""

import sys
import os
import io
import json
import configparser
import argparse
from datetime import datetime

# 修复 Windows GBK 控制台编码问题
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 将脚本所在目录加入 Python 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import godot_project_scanner
import ai_analyzer
import knot_cli_setup


# ============================================================
# 配置加载
# ============================================================

def load_config():
    """
    读取 config.ini，返回 (global_config, projects_list)。
    """
    config_path = os.path.join(ROOT_DIR, "config.ini")
    if not os.path.exists(config_path):
        print(f"  [ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")

    # 全局配置
    global_config = {
        "version": cfg.get("General", "version", fallback="1.0"),
        "reports_base_dir": cfg.get("General", "reports_base_dir", fallback="").strip(),
        "cache_base_dir": cfg.get("General", "cache_base_dir", fallback="").strip(),
        # Analysis
        "cli_tool_command": cfg.get("Analysis", "cli_tool_command", fallback="knot-cli").strip(),
        "cli_tool_args_template": cfg.get("Analysis", "cli_tool_args_template", fallback="").strip(),
        "cli_tool_workspace": cfg.get("Analysis", "cli_tool_workspace", fallback="").strip(),
        "cli_tool_model": cfg.get("Analysis", "cli_tool_model", fallback="claude-4.6-opus").strip(),
        "cli_tool_user_rules": cfg.get("Analysis", "cli_tool_user_rules", fallback="").strip(),
        "cli_tool_timeout": cfg.getint("Analysis", "cli_tool_timeout", fallback=1800),
        "analysis_mode": cfg.get("Analysis", "analysis_mode", fallback="agent").strip(),
        "max_input_tokens": cfg.getint("Analysis", "max_input_tokens", fallback=70000),
        "max_concurrent": cfg.getint("Analysis", "max_concurrent", fallback=3),
        # Scanner
        "ignore_dirs": cfg.get("Scanner", "ignore_dirs", fallback=".godot,.import,addons,build,export").strip(),
        "scan_extensions": cfg.get("Scanner", "scan_extensions", fallback=".gd,.tscn,.tres,.gdshader,.cfg").strip(),
        "max_script_lines": cfg.getint("Scanner", "max_script_lines", fallback=500),
        "parse_scene_tree": cfg.getboolean("Scanner", "parse_scene_tree", fallback=True),
    }

    # 默认路径
    if not global_config["reports_base_dir"]:
        global_config["reports_base_dir"] = os.path.join(ROOT_DIR, "Reports")
    if not global_config["cache_base_dir"]:
        global_config["cache_base_dir"] = os.path.join(ROOT_DIR, "Cache")

    # 解析项目配置
    projects = []
    for section in cfg.sections():
        if section.startswith("Project:"):
            project_name = section[len("Project:"):]
            project = {
                "project_name": project_name,
                "project_dir": cfg.get(section, "project_dir", fallback="").strip(),
                "engine_version": cfg.get(section, "engine_version", fallback="").strip(),
                "description": cfg.get(section, "description", fallback="").strip(),
                "analysis_focus": cfg.get(section, "analysis_focus", fallback="all").strip(),
            }
            projects.append(project)

    return cfg, global_config, projects


# ============================================================
# 工具函数
# ============================================================

def print_banner():
    """打印启动横幅"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 62)
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║           GodotBuddy v1.0                        ║")
    print("  ║     Godot GDScript 项目分析助手                   ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print(f"  启动时间: {now}")
    print("=" * 62)
    print()


def print_project_header(project_name, project_dir, engine_version, analysis_focus):
    """打印项目分析头"""
    print()
    print("┌" + "─" * 60 + "┐")
    print(f"│  项目: {project_name:<52s}│")
    print(f"│  目录: {project_dir[:52]:<52s}│")
    print(f"│  引擎: Godot {engine_version:<46s}│")
    print(f"│  分析: {analysis_focus:<52s}│")
    print("└" + "─" * 60 + "┘")
    print()


# ============================================================
# 核心流程
# ============================================================

def process_single_project(global_config, project_config, force=False, scan_only=False):
    """
    处理单个项目：扫描 → 构建 Prompt → AI 分析。

    :param global_config: 全局配置
    :param project_config: 项目配置
    :param force: 是否强制重新分析
    :param scan_only: 是否仅扫描不分析
    :return: (success, result)
    """
    project_name = project_config["project_name"]
    project_dir = project_config["project_dir"]
    analysis_focus = project_config.get("analysis_focus", "all")

    # 验证项目目录
    if not project_dir or not os.path.exists(project_dir):
        print(f"  [ERROR] 项目目录不存在: {project_dir}")
        return False, f"项目目录不存在: {project_dir}"

    godot_file = os.path.join(project_dir, "project.godot")
    if not os.path.exists(godot_file):
        print(f"  [ERROR] 不是有效的 Godot 项目（未找到 project.godot）: {project_dir}")
        return False, "不是有效的 Godot 项目"

    # 自动检测引擎版本
    engine_version = project_config.get("engine_version", "")
    if not engine_version:
        config_info = godot_project_scanner.parse_project_godot(project_dir)
        engine_version = config_info.get("engine_version", "未知")

    print_project_header(project_name, project_dir, engine_version, analysis_focus)

    if scan_only:
        # 仅扫描模式
        print(f"  [扫描模式] 仅扫描项目结构...")
        ignore_dirs = [d.strip() for d in global_config.get("ignore_dirs", "").split(",")]
        scan_result = godot_project_scanner.scan_project(project_dir, ignore_dirs=ignore_dirs)
        
        # 生成上下文文本
        context = godot_project_scanner.generate_analysis_context(scan_result, analysis_focus)
        
        # 保存扫描结果
        cache_dir = global_config.get("cache_base_dir", os.path.join(ROOT_DIR, "Cache"))
        os.makedirs(cache_dir, exist_ok=True)
        
        # 保存 JSON
        json_path = os.path.join(cache_dir, f"scan_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scan_result, f, indent=2, ensure_ascii=False, default=str)
        
        # 保存上下文文本
        ctx_path = os.path.join(cache_dir, f"context_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        with open(ctx_path, "w", encoding="utf-8") as f:
            f.write(context)
        
        stats = scan_result["statistics"]
        print(f"  [OK] 扫描完成:")
        print(f"       GDScript: {stats['gdscript_count']} 文件, {stats['total_lines']} 行")
        print(f"       场景: {stats['scene_count']} 个")
        print(f"       函数: {stats['total_functions']} 个")
        print(f"       信号: {stats['total_signals']} 个")
        print(f"  [OK] JSON 结果: {json_path}")
        print(f"  [OK] 上下文文本: {ctx_path}")
        
        return True, ctx_path

    # 完整分析模式
    reports_dir = global_config["reports_base_dir"]
    
    return ai_analyzer.analyze_project(
        project_dir=project_dir,
        project_name=project_name,
        config=global_config,
        reports_dir=reports_dir,
        analysis_focus=analysis_focus,
        force=force,
    )


def process_directory(global_config, project_dir, force=False, scan_only=False, analysis_focus="all"):
    """
    分析指定目录的 Godot 项目。

    :param global_config: 全局配置
    :param project_dir: 项目目录
    :param force: 是否强制重新分析
    :param scan_only: 是否仅扫描
    :param analysis_focus: 分析重点
    :return: (success, result)
    """
    # 自动推断项目名
    project_name = os.path.basename(project_dir.rstrip("/\\"))
    
    # 从 project.godot 获取项目名
    config_info = godot_project_scanner.parse_project_godot(project_dir)
    if config_info.get("project_name"):
        project_name = config_info["project_name"]
    
    project_config = {
        "project_name": project_name,
        "project_dir": project_dir,
        "engine_version": config_info.get("engine_version", ""),
        "description": config_info.get("description", ""),
        "analysis_focus": analysis_focus,
    }
    
    return process_single_project(global_config, project_config, force=force, scan_only=scan_only)


# ============================================================
# 主流程
# ============================================================

def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="GodotBuddy - Godot GDScript 项目分析助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python godotbuddy.py                                    # 分析所有配置项目
  python godotbuddy.py --project ThirdPersonShooter       # 只分析指定项目
  python godotbuddy.py --dir "D:\\Project\\MyGame"         # 分析指定目录
  python godotbuddy.py --scan-only                        # 仅扫描不分析
  python godotbuddy.py --force                            # 强制重新分析
        """
    )
    parser.add_argument("--project", "-p", type=str, default=None,
                        help="只分析指定项目名（对应 config.ini 中 [Project:xxx] 的 xxx）")
    parser.add_argument("--dir", "-d", type=str, default=None,
                        help="分析指定目录的 Godot 项目")
    parser.add_argument("--focus", type=str, default="all",
                        help="分析重点: architecture, performance, code_quality, security, all")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重新分析（不跳过已有报告）")
    parser.add_argument("--scan-only", "-s", action="store_true",
                        help="仅扫描项目结构，不进行 AI 分析")

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    # 加载配置
    print("  [配置] 加载 config.ini...")
    cfg, global_config, projects = load_config()

    print(f"  [OK] 项目数: {len(projects)}")
    print(f"  [OK] Reports 目录: {global_config['reports_base_dir']}")
    print(f"  [OK] 分析模式: {global_config['analysis_mode']}")
    print(f"  [OK] AI 模型: {global_config['cli_tool_model']}")
    print()

    # 确保 knot-cli 就绪（如果不是仅扫描模式）
    if not args.scan_only:
        print("  [环境] 检查 knot-cli...")
        knot_ok, knot_msg = knot_cli_setup.ensure_knot_cli(cfg, verbose=True)
        if not knot_ok:
            print(f"  [WARN] knot-cli 环境问题: {knot_msg}")
            print(f"  [WARN] 如果需要 AI 分析，请先安装 knot-cli")
        print()

    # ============================================================
    # 目录模式：分析指定目录
    # ============================================================
    if args.dir:
        project_dir = os.path.abspath(args.dir)
        
        if not os.path.exists(os.path.join(project_dir, "project.godot")):
            print(f"  [ERROR] 不是有效的 Godot 项目目录: {project_dir}")
            sys.exit(1)
        
        success, result = process_directory(
            global_config=global_config,
            project_dir=project_dir,
            force=args.force,
            scan_only=args.scan_only,
            analysis_focus=args.focus,
        )
        
        if success:
            print(f"\n  ✅ 完成: {result}")
        else:
            print(f"\n  ❌ 失败: {result}")
        sys.exit(0 if success else 1)

    # ============================================================
    # 项目模式：遍历配置的项目
    # ============================================================
    if not projects:
        print("  [WARN] 未配置任何项目！")
        print(f"  请在 config.ini 中添加 [Project:xxx] 配置节")
        print(f"  或使用 --dir 参数指定 Godot 项目目录")
        sys.exit(1)

    # 筛选项目
    target_projects = projects
    if args.project:
        target_projects = [p for p in projects if p["project_name"] == args.project]
        if not target_projects:
            print(f"  [ERROR] 未找到项目: {args.project}")
            print(f"  可用项目: {', '.join(p['project_name'] for p in projects)}")
            sys.exit(1)

    print(f"  [开始] 准备分析 {len(target_projects)} 个项目...")

    # 遍历所有目标项目
    all_results = []
    for proj_idx, project_config in enumerate(target_projects, 1):
        project_name = project_config["project_name"]
        print()
        print("╔" + "═" * 62 + "╗")
        print(f"║  项目 [{proj_idx}/{len(target_projects)}]: {project_name:<43s}║")
        print("╚" + "═" * 62 + "╝")

        success, result = process_single_project(
            global_config=global_config,
            project_config=project_config,
            force=args.force,
            scan_only=args.scan_only,
        )
        all_results.append((project_name, success, result))

    # ============================================================
    # 打印最终汇总
    # ============================================================
    print()
    print("╔" + "═" * 62 + "╗")
    print("║                GodotBuddy 执行汇总                        ║")
    print("╚" + "═" * 62 + "╝")
    print()

    total = len(all_results)
    success_count = sum(1 for _, s, _ in all_results if s)
    fail_count = total - success_count

    print(f"  总计: {total}  ✅成功: {success_count}  ❌失败: {fail_count}")
    print()
    for name, success, result in all_results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
        if success and isinstance(result, str) and os.path.exists(result):
            print(f"       → {result}")
        elif not success:
            print(f"       → 错误: {result}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print(f"  完成时间: {now}")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
