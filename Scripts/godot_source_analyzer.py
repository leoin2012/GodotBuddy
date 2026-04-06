#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GodotBuddy - Godot 引擎源码分析入口 (godot_source_analyzer.py)

功能：
  1. 从 config.ini 读取 [SourceAnalysis] + [KnotCLI] 配置
  2. 调用 SourceAnalyzer 模块扫描 Godot 引擎 C++ 源码
  3. 为每个模块构建分析 Prompt
  4. 调用 knot-cli 执行 AI 分析，生成 Markdown 报告
  5. 支持通过 Web 平台展示报告

使用方式：
  python godot_source_analyzer.py                     # 全量分析
  python godot_source_analyzer.py --scan-only         # 仅扫描
  python godot_source_analyzer.py --modules 02,06,13 # 只分析指定模块
  python godot_source_analyzer.py --web               # 启动 Web 展示平台

依赖：knot-cli + 同目录下的 SourceAnalyzer/ 模块
"""

import sys
import os
import io
import json
import argparse
import configparser
import subprocess
import shutil
import platform
from datetime import datetime

# 修复 Windows GBK 控制台编码问题
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower().replace('-', '') != 'utf8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 将脚本所在目录和 SourceAnalyzer 目录加入 Python 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'SourceAnalyzer'))

import knot_cli_setup

try:
    from categories import MODULE_CATEGORIES, TARGET_READER_BACKGROUND
    from slicer import CodeSlicer
    from reporter import ReportGenerator
except ImportError as e:
    print(f"[ERROR] 无法导入 SourceAnalyzer 模块: {e}")
    print(f"  请确保 Scripts/SourceAnalyzer/ 目录存在且包含完整模块文件")
    sys.exit(1)


# ============================================================
# 配置加载
# ============================================================

def load_config(config_path=None):
    """从 config.ini 加载 [KnotCLI] + [SourceAnalysis] 配置"""
    if config_path is None:
        config_path = os.path.join(ROOT_DIR, 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding='utf-8')
    
    # KnotCLI 公共配置
    knot_config = {
        'command': cfg.get('KnotCLI', 'command', fallback='knot-cli').strip(),
        'model': cfg.get('KnotCLI', 'model', fallback='claude-4.6-opus').strip(),
        'user_rules': cfg.get('KnotCLI', 'user_rules', fallback='').strip(),
        'timeout': cfg.getint('KnotCLI', 'timeout', fallback=1800),
    }
    
    # SourceAnalysis 配置
    source_config = {
        'godot_source_dir': cfg.get('SourceAnalysis', 'godot_source_dir', fallback='').strip(),
        'ue_source_dir': cfg.get('SourceAnalysis', 'ue_source_dir', fallback='').strip(),
        'output_dir': cfg.get('SourceAnalysis', 'output_dir', fallback='Reports/GodotEngine').strip(),
        'cli_args_template': cfg.get('SourceAnalysis', 'cli_args_template', fallback='').strip(),
        'prompt_file': cfg.get('SourceAnalysis', 'prompt_file', fallback='').strip(),
        'modules': cfg.get('SourceAnalysis', 'modules', fallback='').strip(),
        'max_files_per_module': cfg.getint('SourceAnalysis', 'max_files_per_module', fallback=25),
        'max_file_tokens': cfg.getint('SourceAnalysis', 'max_file_tokens', fallback=8000),
    }
    
    return cfg, knot_config, source_config


# ============================================================
# Prompt 构建
# ============================================================

# Prompt 模板目录
PROMPT_DIR = os.path.join(ROOT_DIR, "Prompt")


def load_prompt_template(prompt_file_path):
    """
    从外部 md 文件加载 Prompt 模板。
    
    :param prompt_file_path: Prompt 模板文件路径（绝对路径或相对于 ROOT_DIR）
    :return: str 模板文本
    """
    if not os.path.isabs(prompt_file_path):
        prompt_file_path = os.path.join(ROOT_DIR, prompt_file_path)
    
    if not os.path.exists(prompt_file_path):
        print(f"  [ERROR] Prompt 模板文件不存在: {prompt_file_path}")
        print(f"  [INFO] 请检查 config.ini 中的 prompt_file 配置")
        return None
    
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        return f.read()


def build_module_prompt(module_id, module_config, file_list_text, report_path, prompt_template_path=None, ue_source_dir=''):
    """为单个模块构建分析 Prompt（从外部 md 文件加载模板）"""
    # 加载外部 Prompt 模板
    if not prompt_template_path:
        prompt_template_path = os.path.join(PROMPT_DIR, "source_analysis_prompt.md")
    
    template = load_prompt_template(prompt_template_path)
    if template is None:
        print(f"  [WARN] 无法加载 Prompt 模板，使用最小化 Prompt")
        template = "# 源码分析任务\n\n模块: {module_id} - {module_name}\n文件列表:\n{file_list}\n\n报告输出: {report_path}"
    
    # 根据是否有 UE 源码，动态生成分析模式说明
    if ue_source_dir and os.path.isdir(ue_source_dir):
        analysis_mode = (
            f"**🔀 交叉对比模式已启用**\n\n"
            f"已配置 UE 引擎源码目录: `{ue_source_dir}`\n"
            f"你可以直接搜索和阅读 UE 源码进行对比分析。\n\n"
            f"请在分析 Godot 每个功能点时，**同时查阅 UE 对应模块的源码**，\n"
            f"给出源码级别的交叉对比，包括：\n"
            f"- 引用 UE 源码中的具体文件路径和类名\n"
            f"- 对比两个引擎的实现方式差异\n"
            f"- 分析各自的设计 trade-off"
        )
    else:
        analysis_mode = (
            "**📖 单引擎分析模式**\n\n"
            "未配置 UE 引擎源码目录，将基于 UE 公开文档和常识进行概念对比。\n"
            "对比内容以架构层面为主，不涉及 UE 源码细节。"
        )
    
    return template.format(
        target_reader=TARGET_READER_BACKGROUND,
        analysis_mode=analysis_mode,
        module_id=module_id,
        module_name=module_config.get('name', module_id),
        module_name_en=module_config.get('name_en', module_id),
        module_description=module_config.get('description', ''),
        ue_equivalent=module_config.get('ue_equivalent', ''),
        file_list=file_list_text,
        report_path=report_path,
    )


def build_file_list_text(slicer, slice_data, max_files=25):
    """构建模块文件列表文本"""
    lines = []
    files = slice_data.files[:max_files]
    for f in files:
        rel_path = os.path.relpath(f['path'], slicer.source_root) if 'path' in f else f.get('relative_path', '')
        lines.append(f"- `{rel_path}` ({f.get('lines', 0)} 行)")
    if len(slice_data.files) > max_files:
        lines.append(f"- ... 还有 {len(slice_data.files) - max_files} 个文件（已截断）")
    return "\n".join(lines)


# ============================================================
# knot-cli 调用
# ============================================================

def run_knot_cli_source_analysis(prompt_file, report_path, source_dir, knot_config, source_config):
    """
    调用 knot-cli 执行源码模块分析。
    
    :return: (bool, str) - (是否成功, 结果消息)
    """
    cli_command = knot_config['command']
    args_template = source_config.get('cli_args_template', '')
    model = knot_config['model']
    user_rules = knot_config['user_rules']
    timeout = knot_config['timeout']
    
    if not args_template:
        return False, "cli_args_template 未配置"
    
    # 替换占位符
    ue_source_dir = source_config.get('ue_source_dir', '')
    args_str = args_template.format(
        prompt_file=prompt_file.replace("\\", "/"),
        report_path=report_path.replace("\\", "/"),
        source_dir=source_dir.replace("\\", "/"),
        ue_source_dir=ue_source_dir.replace("\\", "/") if ue_source_dir else "",
        godotbuddy_dir=ROOT_DIR.replace("\\", "/"),
        model=model,
        user_rules=user_rules.replace("\\", "/") if user_rules else "",
    )
    
    full_command = f"{cli_command} {args_str}"
    
    print(f"    [AI] 模型: {model}")
    print(f"    [AI] 超时: {timeout}s")
    
    try:
        process = subprocess.Popen(
            full_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=source_dir,
        )
        
        output_lines = []
        try:
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    print(f"      {line}")
                    output_lines.append(line)
        except Exception:
            pass
        
        process.wait(timeout=timeout)
        
        if process.returncode == 0:
            if os.path.exists(report_path):
                file_size = os.path.getsize(report_path)
                return True, f"报告已生成 ({file_size:,} bytes)"
            else:
                return False, "CLI 执行成功但报告文件未生成"
        else:
            return False, f"CLI 执行失败 (返回码: {process.returncode})"
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False, f"CLI 执行超时 ({timeout}s)"
    except Exception as e:
        return False, f"CLI 执行异常: {e}"


# ============================================================
# 工具函数
# ============================================================

def print_banner():
    """打印启动横幅"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 70)
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  GodotBuddy - Godot Engine Source Analyzer       ║")
    print("  ║  Powered by knot-cli                             ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(f"  Time: {now}")
    print("=" * 70)
    print()


def print_stats(slices):
    """打印扫描统计"""
    print()
    print("=" * 70)
    print("  [Scan Complete] Statistics")
    print("=" * 70)

    sorted_slices = sorted(
        [(cid, s) for cid, s in slices.items() if s.total_lines > 0],
        key=lambda x: x[1].total_lines,
        reverse=True
    )
    
    total_files = sum(len(s.files) for s in slices.values())
    total_lines = sum(s.total_lines for s in slices.values())
    
    print(f"  Total files : {total_files}")
    print(f"  Total lines : {total_lines:,}")
    print(f"  Categories : {len(sorted_slices)}")
    print()
    print(f"  {'Module':<28} {'Files':>8} {'Lines':>12} {'Size':>10}")
    print(f"  {'-'*28} {'-'*8} {'-'*12} {'-'*10}")
    
    for cat_id, sl in sorted_slices:
        cfg = MODULE_CATEGORIES.get(cat_id, {})
        mark = " *" if cfg.get('highlight') else ""
        size_mb = sl.total_size / (1024 * 1024)
        print(f"  {sl.category_name:<28} {len(sl.files):>8} {sl.total_lines:>12,} {size_mb:>9.2f}MB{mark}")
    
    print("=" * 70)


# ============================================================
# 核心流程
# ============================================================

def run_scan(source_config):
    """仅执行源码扫描（不调用 knot-cli）"""
    source_dir = source_config['godot_source_dir']
    
    if not source_dir:
        print("[ERROR] 未配置 godot_source_dir")
        return False
    
    if not os.path.exists(source_dir):
        print(f"[ERROR] 源码目录不存在: {source_dir}")
        return False
    
    print(f"[Step 1/2] Scanning: {source_dir}")
    
    slicer = CodeSlicer(source_dir, MODULE_CATEGORIES)
    
    def on_progress(current, total):
        pct = current * 100 / total
        print(f"\r  Scanning... {pct:.1f}% ({current}/{total})", end="")
    
    slices = slicer.scan(progress_callback=on_progress)
    print()
    
    # 导出结果
    output_dir = os.path.join(ROOT_DIR, source_config['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    scan_result_path = os.path.join(output_dir, 'scan_result.json')
    slicer.export_scan_result(scan_result_path)
    
    print_stats(slices)
    print(f"\n  [OK] Saved to: {scan_result_path}")
    return True


def run_analysis(knot_config, source_config):
    """执行完整的扫描 + knot-cli 分析流程"""
    source_dir = source_config['godot_source_dir']
    
    if not source_dir:
        print("[ERROR] 未配置 godot_source_dir")
        return False
    
    if not os.path.exists(source_dir):
        print(f"[ERROR] 源码目录不存在: {source_dir}")
        return False
    
    output_dir = os.path.join(ROOT_DIR, source_config['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    cache_dir = os.path.join(ROOT_DIR, "Cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Step 1: 扫描
    print(f"[Step 1/3] Scanning: {source_dir}")
    
    slicer = CodeSlicer(source_dir, MODULE_CATEGORIES)
    
    def on_progress(current, total):
        pct = current * 100 / total
        print(f"\r  Scanning... {pct:.1f}% ({current}/{total})", end="")
    
    slices = slicer.scan(progress_callback=on_progress)
    print()
    
    scan_result_path = os.path.join(output_dir, 'scan_result.json')
    slicer.export_scan_result(scan_result_path)
    print_stats(slices)
    
    # Step 2: 检查 knot-cli
    print(f"\n[Step 2/3] Checking knot-cli...")
    cli_command = knot_config['command']
    available, version_info = knot_cli_setup.is_knot_cli_installed(cli_command)
    if not available:
        print(f"  [ERROR] {cli_command} 不可用: {version_info}")
        print(f"  [INFO] 请先安装 knot-cli")
        return False
    print(f"  [OK] {cli_command} ({version_info})")
    
    # Step 3: 逐模块分析
    modules_to_run = None
    if source_config['modules']:
        modules_to_run = [m.strip() for m in source_config['modules'].split(',') if m.strip()]
    
    # 筛选要分析的模块
    target_modules = []
    for cat_id, sl in slices.items():
        if sl.total_lines == 0:
            continue
        if modules_to_run is not None:
            if not any(m in cat_id for m in modules_to_run):
                continue
        target_modules.append((cat_id, sl))
    
    print(f"\n[Step 3/3] Analyzing {len(target_modules)} modules with knot-cli...")
    print(f"  Model: {knot_config['model']}")
    print()
    
    results = {}
    for idx, (cat_id, sl) in enumerate(target_modules, 1):
        module_cfg = MODULE_CATEGORIES.get(cat_id, {})
        module_name = module_cfg.get('name', cat_id)
        
        print(f"  [{idx}/{len(target_modules)}] {module_name} ({cat_id})...")
        
        # 构建文件列表
        file_list_text = build_file_list_text(slicer, sl, source_config['max_files_per_module'])
        
        # 报告路径
        report_path = os.path.join(output_dir, f"{cat_id}.md")
        
        # 构建 Prompt（从外部 md 文件加载模板）
        prompt_template_path = source_config.get('prompt_file', '') or None
        ue_source_dir = source_config.get('ue_source_dir', '')
        prompt_text = build_module_prompt(cat_id, module_cfg, file_list_text, report_path, prompt_template_path, ue_source_dir)
        
        # 保存 Prompt
        prompt_file = os.path.join(cache_dir, f"source_prompt_{cat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        
        # 调用 knot-cli
        success, msg = run_knot_cli_source_analysis(
            prompt_file=prompt_file,
            report_path=report_path,
            source_dir=source_dir,
            knot_config=knot_config,
            source_config=source_config,
        )
        
        results[cat_id] = {
            'success': success,
            'message': msg,
            'report_path': report_path if success else None,
        }
        
        status = "✅" if success else "❌"
        print(f"    {status} {msg}")
        print()
    
    # 汇总
    success_count = sum(1 for r in results.values() if r['success'])
    fail_count = len(results) - success_count
    print(f"\n  [Done] {success_count} succeeded, {fail_count} failed -> {output_dir}")
    
    return success_count > 0


def run_web(source_config):
    """启动 Web 展示平台"""
    web_dir = os.path.join(ROOT_DIR, 'SourceAnalyzerWeb')
    app_py = os.path.join(web_dir, 'app.py')
    
    if not os.path.exists(app_py):
        print(f"[ERROR] Web app not found: {app_py}")
        return False
    
    output_dir = os.path.join(ROOT_DIR, source_config['output_dir'])
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("web_app", app_py)
    web_app = importlib.util.module_from_spec(spec)
    sys.path.insert(0, web_dir)
    spec.loader.exec_module(web_app)
    web_app.LOCAL_OUTPUT_DIR = output_dir
    
    print()
    print("=" * 70)
    print("  Starting GodotBuddy Source Analyzer Web Platform...")
    print(f"  Reports: {output_dir}")
    print("  http://localhost:5000")
    print("=" * 70)
    print()
    
    web_app.app.run(host='0.0.0.0', port=5000, debug=True)
    return True


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="GodotBuddy - Godot Engine Source Analyzer (powered by knot-cli)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python godot_source_analyzer.py                       # Analyze all modules
  python godot_source_analyzer.py --scan-only           # Scan only (no AI)
  python godot_source_analyzer.py --modules 02,06,13   # Specific modules
  python godot_source_analyzer.py --web                 # Start web viewer
  python godot_source_analyzer.py --source ./godot-4.6  # Override source dir
        """,
    )
    parser.add_argument('--scan-only', '-s', action='store_true',
                        help='Scan source code only, no AI analysis')
    parser.add_argument('--web', '-w', action='store_true',
                        help='Start Flask web viewer')
    parser.add_argument('--source', '-src', type=str, default=None,
                        help='Godot engine source root directory')
    parser.add_argument('--modules', '-m', type=str, default=None,
                        help='Comma-separated module IDs to analyze')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force re-analysis')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 加载配置
    cfg, knot_config, source_config = load_config()
    
    # CLI 参数覆盖配置文件
    if args.source:
        source_config['godot_source_dir'] = args.source
    if args.modules:
        source_config['modules'] = args.modules
    
    # 显示配置摘要
    ue_source_dir = source_config.get('ue_source_dir', '')
    ue_status = f"{ue_source_dir}" if ue_source_dir and os.path.isdir(ue_source_dir) else '(未配置，单引擎模式)'
    print("  [Config]")
    print(f"    Godot    : {source_config['godot_source_dir'] or '(not set)'}")
    print(f"    UE       : {ue_status}")
    print(f"    Mode     : {'交叉对比模式 (Godot vs UE)' if ue_source_dir and os.path.isdir(ue_source_dir) else '单引擎分析模式'}")
    print(f"    Engine   : knot-cli / {knot_config['model']}")
    print(f"    Output   : {source_config['output_dir']}")
    print(f"    Analysis : {'scan-only' if args.scan_only else 'full analysis'}")
    print()
    
    # 确保 knot-cli 就绪（非扫描模式）
    if not args.scan_only and not args.web:
        print("  [环境] 检查 knot-cli...")
        knot_ok, knot_msg = knot_cli_setup.ensure_knot_cli(cfg, section="KnotCLI", verbose=True)
        if not knot_ok:
            print(f"  [WARN] knot-cli 环境问题: {knot_msg}")
        print()
    
    # 分派模式
    if args.web:
        success = run_web(source_config)
    elif args.scan_only:
        success = run_scan(source_config)
    else:
        success = run_analysis(knot_config, source_config)
    
    if not success:
        print("\n  Failed!")
        sys.exit(1)
    
    print("\n  Done!")


if __name__ == '__main__':
    main()
