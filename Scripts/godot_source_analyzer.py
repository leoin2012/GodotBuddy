#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GodotBuddy - Godot 引擎源码分析入口 (godot_source_analyzer.py)

功能：
  1. 从 config.ini 读取 [SourceAnalyzer] 配置
  2. 调用 SourceAnalyzer 模块扫描 Godot 引擎 C++ 源码
  3. 调用 LLM 对每个模块进行深度语义分析
  4. 生成面向 UE 开发者的 Markdown 分析报告
  5. 支持通过 Web 平台展示报告

使用方式：
  python godot_source_analyzer.py                     # 全量分析
  python godot_source_analyzer.py --scan-only         # 仅扫描
  python godot_source_analyzer.py --modules 02,06,13 # 只分析指定模块
  python godot_source_analyzer.py --web               # 启动 Web 展示平台

依赖：openai (或 anthropic) + 同目录下的 SourceAnalyzer/ 模块
"""

import sys
import os
import io
import json
import argparse
import configparser
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

try:
    from categories import MODULE_CATEGORIES, OUTPUT_DIR, TARGET_READER_BACKGROUND
    from slicer import CodeSlicer
    from analyzer import (
        AnalysisEngine, OpenAIBackend, AnthropicBackend, LLMBackend
    )
    from reporter import ReportGenerator
except ImportError as e:
    print(f"[ERROR] 无法导入 SourceAnalyzer 模块: {e}")
    print(f"  请确保 Scripts/SourceAnalyzer/ 目录存在且包含完整模块文件")
    sys.exit(1)


# ============================================================
# 配置加载
# ============================================================

def load_source_analyzer_config(config_path=None):
    """从 config.ini 加载 [SourceAnalyzer] 配置节"""
    if config_path is None:
        config_path = os.path.join(ROOT_DIR, 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
    
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding='utf-8')
    
    if not cfg.has_section('SourceAnalyzer'):
        print("[ERROR] config.ini 中缺少 [SourceAnalyzer] 配置节")
        print("  请参考 config.ini 中的注释添加配置")
        sys.exit(1)
    
    section = cfg['SourceAnalyzer']
    
    config = {
        'godot_source_dir': section.get('godot_source_dir', '').strip(),
        'llm_backend': section.get('llm_backend', 'openai').strip(),
        'api_key': section.get('api_key', '').strip(),
        'base_url': section.get('base_url', '').strip() or None,
        'model': section.get('model', 'gpt-4o').strip(),
        'temperature': section.getfloat('temperature', 0.3),
        'output_dir': section.get('output_dir', 'SourceAnalyzerOutput').strip(),
        'modules': section.get('modules', '').strip(),
        'max_files_per_module': section.getint('max_files_per_module', 25),
        'max_file_tokens': section.getint('max_file_tokens', 8000),
        'scan_only': section.getboolean('scan_only', False),
    }
    
    return config, cfg


# ============================================================
# LLM 后端工厂
# ============================================================

def create_llm_backend(config):
    """根据配置创建 LLM 后端实例"""
    backend_type = config['llm_backend'].lower()
    
    if backend_type in ('openai', 'custom'):
        return OpenAIBackend(
            api_key=config['api_key'] or None,
            base_url=config['base_url'],
            model=config['model'],
            temperature=config['temperature'],
        )
    elif backend_type == 'anthropic':
        return AnthropicBackend(
            api_key=config['api_key'] or None,
            model=config['model'],
            temperature=config['temperature'],
        )
    else:
        raise ValueError(f"不支持的 LLM 后端类型: {backend_type}")


# ============================================================
# 工具函数
# ============================================================

def print_banner():
    """打印启动横幅"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 70)
    print("  +--------------------------------------------------+")
    print("  |     GodotBuddy - Godot Engine Source Analyzer       |")
    print("  |     AI-Powered Analysis for Unreal Developers         |")
    print("  +--------------------------------------------------+")
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

def run_scan(config):
    """仅执行源码扫描（不调用 LLM）"""
    source_dir = config['godot_source_dir']
    
    if not source_dir:
        print("[ERROR] 未配置 godot_source_dir")
        print("  请在 config.ini 的 [SourceAnalyzer] 中设置 godot_source_dir")
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
    output_dir = os.path.join(ROOT_DIR, config['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    scan_result_path = os.path.join(output_dir, 'scan_result.json')
    slicer.export_scan_result(scan_result_path)
    
    print_stats(slices)
    print(f"\n  [OK] Saved to: {scan_result_path}")
    return True


def run_analysis(config):
    """执行完整的扫描 + LLM 分析流程"""
    source_dir = config['godot_source_dir']
    
    if not source_dir:
        print("[ERROR] 未配置 godot_source_dir")
        return False
    
    if not os.path.exists(source_dir):
        print(f"[ERROR] 源码目录不存在: {source_dir}")
        return False
    
    output_dir = os.path.join(ROOT_DIR, config['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: 扫描
    print(f"[Step 1/4] Scanning: {source_dir}")
    
    slicer = CodeSlicer(source_dir, MODULE_CATEGORIES)
    
    def on_progress(current, total):
        pct = current * 100 / total
        print(f"\r  Scanning... {pct:.1f}% ({current}/{total})", end="")
    
    slices = slicer.scan(progress_callback=on_progress)
    print()
    
    scan_result_path = os.path.join(output_dir, 'scan_result.json')
    slicer.export_scan_result(scan_result_path)
    print_stats(slices)
    
    # Step 2: 创建 LLM 后端
    print("\n[Step 2/4] Initializing LLM...")
    try:
        llm_backend = create_llm_backend(config)
        print(f"  [OK] {llm_backend.get_model_name()}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    
    # Step 3: 分析
    engine = AnalysisEngine(
        llm_backend=llm_backend,
        categories_config=MODULE_CATEGORIES,
        max_file_tokens=config['max_file_tokens'],
    )
    
    modules_to_run = None
    if config['modules']:
        modules_to_run = [m.strip() for m in config['modules'].split(',') if m.strip()]
    
    print(f"\n[Step 3/4] Analyzing with LLM...")
    print(f"  Modules: {'All' if modules_to_run is None else ', '.join(modules_to_run)}")
    print()
    
    def on_analysis_progress(current, total, module_name):
        print(f"  [{current}/{total}] {module_name}...")
    
    results = engine.batch_analyze(
        slices=slices,
        slicer_instance=slicer,
        categories_to_run=modules_to_run,
        progress_callback=on_analysis_progress,
    )
    
    engine.export_results(output_dir)
    
    # Step 4: 报告生成
    print(f"\n[Step 4/4] Generating reports...")
    
    reporter = ReportGenerator(
        output_dir=output_dir,
        categories_config=MODULE_CATEGORIES,
    )
    
    generated = reporter.generate_all(results, slices)
    
    success_count = sum(1 for r in results.values() if r and not r.overview.startswith("# "))
    print(f"\n  [OK] {len(generated)} reports -> {output_dir}")
    print(f"       Success: {success_count}, Failed: {len(results) - success_count}")
    
    return True


def run_web(config):
    """启动 Web 展示平台"""
    web_dir = os.path.join(ROOT_DIR, 'SourceAnalyzerWeb')
    app_py = os.path.join(web_dir, 'app.py')
    
    if not os.path.exists(app_py):
        print(f"[ERROR] Web app not found: {app_py}")
        return False
    
    output_dir = os.path.join(ROOT_DIR, config['output_dir'])
    
    # 动态修改 Web app 的输出目录指向
    import importlib.util
    spec = importlib.util.spec_from_file_location("web_app", app_py)
    web_app = importlib.util.module_from_spec(spec)
    sys.path.insert(0, web_dir)
    
    # 先加载，再 patch 路径
    spec.loader.exec_module(web_app)
    
    # Patch LOCAL_OUTPUT_DIR
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
        description="GodotBuddy - Godot Engine Source Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python godot_source_analyzer.py                       # Analyze all 24 modules
  python godot_source_analyzer.py --scan-only           # Scan only (no LLM)
  python godot_source_analyzer.py --modules 02,06,13   # Specific modules only
  python godot_source_analyzer.py --web                 # Start web platform
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
    config, _cfg = load_source_analyzer_config()
    
    # CLI 参数覆盖配置文件
    if args.source:
        config['godot_source_dir'] = args.source
    if args.modules:
        config['modules'] = args.modules
    if args.scan_only:
        config['scan_only'] = True
    
    # 显示配置摘要
    print("  [Config]")
    print(f"    Source   : {config['godot_source_dir'] or '(not set)'}")
    print(f"    LLM      : {config['llm_backend']} / {config['model']}")
    print(f"    Output   : {config['output_dir']}")
    print(f"    Mode     : {'scan-only' if config['scan_only'] else 'full analysis'}")
    print()
    
    # 分派模式
    if args.web:
        success = run_web(config)
    elif config['scan_only']:
        success = run_scan(config)
    else:
        success = run_analysis(config)
    
    if not success:
        print("\n  Failed!")
        sys.exit(1)
    
    print("\n  Done!")


if __name__ == '__main__':
    main()
