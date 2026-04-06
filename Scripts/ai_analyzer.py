#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GodotBuddy AI 分析模块 (ai_analyzer.py)

功能：
  1. 构建分析 Prompt（包含项目扫描上下文）
  2. 调用 knot-cli 执行 AI 分析
  3. 管理报告输出和归档
  4. 支持 agent 和 direct 两种分析模式

依赖：同目录下的 godot_project_scanner.py
"""

import os
import sys
import io
import re
import json
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import godot_project_scanner


# ============================================================
# Prompt 构建
# ============================================================

SYSTEM_PROMPT_TEMPLATE = """# GodotBuddy 项目分析任务

## 你的角色
你是 **GodotBuddy**，一名资深的 Godot 引擎和 GDScript 游戏开发分析专家。

## 分析目标
请对以下 Godot 项目进行全面深入的分析，生成一份结构化的 Markdown 分析报告。

## 项目上下文
{analysis_context}

## 分析要求
请按照以下结构生成分析报告：

### 1. 项目概览
- 项目名称、引擎版本、项目类型（2D/3D/混合）
- 项目规模统计（文件数、代码行数、场景数等）
- 项目描述和核心玩法

### 2. 架构分析
- 项目目录结构和组织方式
- 场景树层级关系
- 自动加载（Autoload）全局管理器分析
- 自定义类（class_name）体系

### 3. 核心系统分析
对每个核心系统进行深入分析：
- 系统职责和设计模式
- 关键函数和逻辑流程
- 数据流和状态管理
- 与其他系统的交互关系

### 4. 网络/多人游戏架构（如适用）
- 网络同步策略（MultiplayerSynchronizer / RPC）
- 服务器-客户端职责划分
- 网络权限管理

### 5. 输入系统分析
- 输入映射配置
- 输入处理流程
- 支持的输入设备（键鼠/手柄）

### 6. 渲染和视觉效果
- 渲染管线配置
- 光照方案（GI 类型、阴影等）
- 粒子效果和着色器
- 性能优化设置

### 7. 音频系统
- 音频总线配置
- 音效管理方式

### 8. 代码质量评估
- GDScript 编码规范遵循情况
- 代码组织和模块化程度
- 潜在的性能问题
- 潜在的 Bug 和安全隐患
- 内存管理和资源加载策略

### 9. 改进建议
- 架构优化建议
- 性能优化建议
- 代码质量改进建议
- 最佳实践推荐

### 10. 总结
- 项目整体评价
- 技术亮点
- 主要风险点
- 推荐优先改进项

## 输出要求
1. 使用中文输出
2. 使用 Markdown 格式
3. 对关键代码片段使用代码块引用
4. 使用 mermaid 流程图展示架构关系（如适用）
5. 每个分析结论都要有具体的代码证据支撑
6. 报告开头包含一句话总结（不超过60个汉字）

## 报告输出路径
请将完整的 Markdown 分析报告写入: {report_path}
"""


def build_analysis_prompt(scan_result, report_path, analysis_focus="all"):
    """
    构建分析 Prompt。
    
    :param scan_result: 项目扫描结果
    :param report_path: 报告输出路径
    :param analysis_focus: 分析重点
    :return: str Prompt 文本
    """
    # 生成分析上下文
    context = godot_project_scanner.generate_analysis_context(scan_result, analysis_focus)
    
    # 填充模板
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        analysis_context=context,
        report_path=report_path,
    )
    
    return prompt


# ============================================================
# Knot CLI 调用
# ============================================================

def is_knot_cli_available(cli_command="knot-cli"):
    """
    检测 knot-cli 是否可用。
    
    :return: (bool, str) - (是否可用, 版本或错误信息)
    """
    if not shutil.which(cli_command):
        return False, "命令不在 PATH 中"
    
    try:
        result = subprocess.run(
            [cli_command, "--version"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
        else:
            return False, f"返回码: {result.returncode}"
    except Exception as e:
        return False, str(e)


def run_knot_cli_analysis(prompt_file, report_path, project_dir, config, timeout=1800):
    """
    调用 knot-cli 执行 AI 分析。
    
    :param prompt_file: Prompt 文件路径
    :param report_path: 报告输出路径
    :param project_dir: 被分析的 Godot 项目目录
    :param config: 全局配置 dict
    :param timeout: 超时时间（秒）
    :return: (bool, str) - (是否成功, 结果消息)
    """
    cli_command = config.get("cli_tool_command", "knot-cli")
    args_template = config.get("cli_tool_args_template", "")
    cli_model = config.get("cli_tool_model", "claude-4.6-opus")
    cli_user_rules = config.get("cli_tool_user_rules", "")
    cli_workspace = config.get("cli_tool_workspace", project_dir)
    
    if not args_template:
        return False, "cli_tool_args_template 未配置"
    
    # 替换占位符
    args_str = args_template.format(
        prompt_file=prompt_file.replace("\\", "/"),
        report_path=report_path.replace("\\", "/"),
        project_dir=project_dir.replace("\\", "/"),
        cli_tool_workspace=cli_workspace.replace("\\", "/"),
        cli_tool_model=cli_model,
        cli_tool_user_rules=cli_user_rules.replace("\\", "/") if cli_user_rules else "",
        godotbuddy_dir=ROOT_DIR.replace("\\", "/"),
    )
    
    # 构建完整命令
    full_command = f"{cli_command} {args_str}"
    
    print(f"  [AI] 执行命令: {cli_command} chat ...")
    print(f"  [AI] 模型: {cli_model}")
    print(f"  [AI] 超时: {timeout}s")
    print()
    
    try:
        # 使用 shell 执行（因为参数模板可能包含引号等特殊字符）
        is_windows = platform.system() == "Windows"
        
        process = subprocess.Popen(
            full_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=project_dir,
        )
        
        # 实时输出
        output_lines = []
        try:
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    print(f"    {line}")
                    output_lines.append(line)
        except Exception:
            pass
        
        process.wait(timeout=timeout)
        
        if process.returncode == 0:
            # 检查报告文件是否生成
            if os.path.exists(report_path):
                file_size = os.path.getsize(report_path)
                return True, f"分析完成，报告已生成: {report_path} ({file_size:,} bytes)"
            else:
                return False, f"CLI 执行成功但报告文件未生成: {report_path}"
        else:
            return False, f"CLI 执行失败 (返回码: {process.returncode})"
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False, f"CLI 执行超时 ({timeout}s)"
    except Exception as e:
        return False, f"CLI 执行异常: {e}"


# ============================================================
# 报告管理
# ============================================================

def generate_report_filename(project_name, analysis_focus="all"):
    """
    生成标准化的报告文件名。
    
    格式: GodotBuddyReport_{YYYYMMDD}_{项目名}_{分析重点}.md
    
    :param project_name: 项目名称
    :param analysis_focus: 分析重点
    :return: str 文件名
    """
    date_str = datetime.now().strftime("%Y%m%d")
    # 清理项目名中的特殊字符
    safe_name = re.sub(r'[^\w\-]', '_', project_name)
    return f"GodotBuddyReport_{date_str}_{safe_name}_{analysis_focus}.md"


def inject_report_header(report_path, project_name, project_dir, scan_result, analysis_mode="agent"):
    """
    为报告注入头部元信息。
    
    :param report_path: 报告文件路径
    :param project_name: 项目名称
    :param project_dir: 项目目录
    :param scan_result: 扫描结果
    :param analysis_mode: 分析模式
    """
    if not os.path.exists(report_path):
        return
    
    with open(report_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    config = scan_result.get("project_config", {})
    stats = scan_result.get("statistics", {})
    
    header_lines = [
        f"> **GodotBuddy 分析报告**",
        f"> ",
        f"> 👤 分析者: {platform.node()} | 🤖 模式: {analysis_mode}",
        f"> 📂 项目: {project_name} | 🎮 引擎: Godot {config.get('engine_version', '?')}",
        f"> 📊 规模: {stats.get('gdscript_count', 0)} 脚本 / {stats.get('total_lines', 0)} 行代码 / {stats.get('scene_count', 0)} 场景",
        f"> 📁 路径: `{project_dir}`",
        f"> 🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"---",
        f"",
    ]
    
    header = "\n".join(header_lines)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(header + content)


# ============================================================
# 分析流程
# ============================================================

def analyze_project(project_dir, project_name, config, reports_dir, 
                    analysis_focus="all", force=False):
    """
    分析单个 Godot 项目的完整流程。
    
    :param project_dir: 项目目录
    :param project_name: 项目名称
    :param config: 全局配置
    :param reports_dir: 报告输出目录
    :param analysis_focus: 分析重点
    :param force: 是否强制重新分析
    :return: (bool, str) - (是否成功, 结果消息)
    """
    print(f"  [Step 1/4] 扫描项目结构...")
    
    # 扫描项目
    ignore_dirs = [d.strip() for d in config.get("ignore_dirs", ".godot,.import,addons").split(",")]
    scan_result = godot_project_scanner.scan_project(project_dir, ignore_dirs=ignore_dirs)
    
    stats = scan_result["statistics"]
    print(f"  [OK] 扫描完成:")
    print(f"       GDScript: {stats['gdscript_count']} 文件, {stats['total_lines']} 行")
    print(f"       场景: {stats['scene_count']} 个")
    print(f"       函数: {stats['total_functions']} 个")
    print(f"       信号: {stats['total_signals']} 个")
    print()
    
    # 生成报告文件名和路径
    report_filename = generate_report_filename(project_name, analysis_focus)
    report_path = os.path.join(reports_dir, report_filename)
    
    # 检查是否已存在
    if not force and os.path.exists(report_path):
        print(f"  [SKIP] 报告已存在: {report_path}")
        return True, report_path
    
    # 确保报告目录存在
    os.makedirs(reports_dir, exist_ok=True)
    
    print(f"  [Step 2/4] 构建分析 Prompt...")
    
    # 构建 Prompt
    prompt_text = build_analysis_prompt(scan_result, report_path, analysis_focus)
    
    # 保存 Prompt 到临时文件
    cache_dir = config.get("cache_base_dir", os.path.join(ROOT_DIR, "Cache"))
    os.makedirs(cache_dir, exist_ok=True)
    prompt_file = os.path.join(cache_dir, f"prompt_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    
    print(f"  [OK] Prompt 已保存: {prompt_file}")
    print(f"       Prompt 大小: {os.path.getsize(prompt_file):,} bytes")
    print()
    
    # 检查 knot-cli 是否可用
    print(f"  [Step 3/4] 检查 AI 分析引擎...")
    cli_command = config.get("cli_tool_command", "knot-cli")
    available, version_info = is_knot_cli_available(cli_command)
    
    if not available:
        print(f"  [ERROR] {cli_command} 不可用: {version_info}")
        print(f"  [INFO] Prompt 文件已保存，可手动执行分析")
        return False, f"{cli_command} 不可用: {version_info}"
    
    print(f"  [OK] {cli_command} 已就绪 ({version_info})")
    print()
    
    # 执行 AI 分析
    print(f"  [Step 4/4] 执行 AI 分析...")
    print()
    
    timeout = config.get("cli_tool_timeout", 1800)
    if isinstance(timeout, str):
        timeout = int(timeout)
    
    success, result = run_knot_cli_analysis(
        prompt_file=prompt_file,
        report_path=report_path,
        project_dir=project_dir,
        config=config,
        timeout=timeout,
    )
    
    if success:
        # 注入报告头部
        inject_report_header(
            report_path=report_path,
            project_name=project_name,
            project_dir=project_dir,
            scan_result=scan_result,
            analysis_mode=config.get("analysis_mode", "agent"),
        )
        print()
        print(f"  ✅ 分析完成: {report_path}")
    else:
        print()
        print(f"  ❌ 分析失败: {result}")
    
    return success, report_path if success else result


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GodotBuddy AI 分析模块")
    parser.add_argument("project_dir", help="Godot 项目目录")
    parser.add_argument("--report-dir", default=None, help="报告输出目录")
    parser.add_argument("--focus", default="all", help="分析重点")
    parser.add_argument("--force", action="store_true", help="强制重新分析")
    
    args = parser.parse_args()
    
    if not os.path.exists(os.path.join(args.project_dir, "project.godot")):
        print(f"错误: {args.project_dir} 不是有效的 Godot 项目目录")
        sys.exit(1)
    
    reports_dir = args.report_dir or os.path.join(ROOT_DIR, "Reports")
    project_name = os.path.basename(args.project_dir)
    
    # 简单配置
    config = {
        "cli_tool_command": "knot-cli",
        "cli_tool_model": "claude-4.6-opus",
        "cli_tool_timeout": 1800,
        "analysis_mode": "agent",
        "ignore_dirs": ".godot,.import,addons",
    }
    
    success, result = analyze_project(
        project_dir=args.project_dir,
        project_name=project_name,
        config=config,
        reports_dir=reports_dir,
        analysis_focus=args.focus,
        force=args.force,
    )
    
    sys.exit(0 if success else 1)
