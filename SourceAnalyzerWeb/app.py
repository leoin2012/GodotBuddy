"""
GodotBuddy - Source Analyzer Web 应用
展示 AI 生成的 Godot 引擎源码深度分析报告

数据源: SourceAnalyzerOutput/ 目录下的 MD 报告
"""

import os
import re
import json
import markdown
from flask import (
    Flask, render_template_string, render_template,
    send_from_directory, abort, jsonify
)

# ============================================================================
# 配置
# ============================================================================

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
)

# 本地数据源目录（相对于 GodotBuddy 根目录）
_LOCAL_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SourceAnalyzerOutput')

# 可通过外部环境变量或全局变量覆盖 LOCAL_OUTPUT_DIR
LOCAL_OUTPUT_DIR = os.environ.get('GODOTBUDDY_OUTPUT_DIR', _LOCAL_OUTPUT_DIR)

# 站点元信息
SITE_CONFIG = {
    "title": "Godot 4.6 Engine Deep Dive",
    "subtitle": "AI-Powered Source Code Analysis for Unreal Engine Developers",
    "author": "Source Analyzer",
    "description": "Complete Godot 4.6 source code analysis reports, powered by AI.",
    "github_url": f"https://github.com/{GITHUB_REPO}",
    "version": "4.6",
}

# 模块分类定义（用于导航和卡片展示）
MODULE_CATEGORIES = {
    "01_core_foundation": {"name": "Core Foundation", "name_cn": "核心基础层", "icon": "🏗️", "color": "#478CBF", "ue": "UE Core Module", "vol": 1},
    "02_object_system": {"name": "Object System", "name_cn": "对象系统", "icon": "🔗", "color": "#E55B9C", "ue": "UObject + Reflection", "vol": 1, "highlight": True},
    "03_memory_management": {"name": "Memory Management", "name_cn": "内存管理", "icon": "🧠", "color": "#A86BB6", "ue": "FMemory + SmartPtrs", "vol": 2},
    "04_math_library": {"name": "Math Library", "name_cn": "数学库", "icon": "📐", "color": "#5DCAB5", "ue": "Math Module", "vol": 2},
    "05_io_system": {"name": "I/O & File System", "name_cn": "IO与文件系统", "icon": "💾", "color": "#FF8C42", "ue": "PlatformFile + Archive", "vol": 3},
    "06_rendering_server": {"name": "Rendering Server", "name_cn": "渲染服务器", "icon": "🎨", "color": "#E74C3C", "ue": "RHI + Renderer", "vol": 6, "highlight": True},
    "07_graphics_drivers": {"name": "Graphics Drivers (RHI)", "name_cn": "图形驱动层", "icon": "⚡", "color": "#9B59B6", "ue": "VulkanRHI / D3D11RHI", "vol": 7},
    "08_scene_tree_2d": {"name": "Scene Tree - 2D", "name_cn": "场景树-2D", "icon": "📜", "color": "#3498DB", "ue": "UMG / Slate", "vol": 8},
    "09_scene_tree_3d": {"name": "Scene Tree - 3D", "name_cn": "场景树-3D", "icon": "🌍", "color": "#27AE60", "ue": "AActor / Component", "vol": 9},
    "10_scene_main": {"name": "Scene Tree Core", "name_cn": "场景树核心", "icon": "🌳", "color": "#16A085", "ue": "UWorld / Level", "vol": 10, "highlight": True},
    "11_physics_2d": {"name": "Physics - 2D", "name_cn": "物理引擎-2D", "icon": "⚽", "color": "#F39C12", "ue": "Chaos Physics 2D", "vol": 11},
    "12_physics_3d": {"name": "Physics - 3D", "name_cn": "物理引擎-3D", "icon": "⚛️", "color": "#E67E22", "ue": "Chaos / PhysX", "vol": 12},
    "13_script_system": {"name": "Script System", "name_cn": "脚本系统", "icon": "💻", "color": "#2980B9", "ue": "Blueprint VM + C#", "vol": 13, "highlight": True},
    "14_animation_system": {"name": "Animation System", "name_cn": "动画系统", "icon": "🎬", "color": "#C0392B", "ue": "AnimInstance / ABP", "vol": 14},
    "15_resource_system": {"name": "Resource System", "name_cn": "资源系统", "icon": "📦", "color": "#7F8C8D", "ue": "UObject Asset System", "vol": 15},
    "16_import_pipeline": {"name": "Import Pipeline", "name_cn": "导入管线", "icon": "📥", "color": "#95A5A6", "ue": "Factory / Import Pipeline", "vol": 16},
    "17_audio_system": {"name": "Audio System", "name_cn": "音频系统", "icon": "🔊", "color": "#1ABC9C", "ue": "Audio Runtime", "vol": 17},
    "18_input_system": {"name": "Input System", "name_cn": "输入系统", "icon": "🎮", "color": "#E74C3C", "ue": "Enhanced Input", "vol": 18},
    "19_ui_system": {"name": "UI System", "name_cn": "UI系统", "icon": "🖥️", "color": "#8E44AD", "ue": "UMG Widget", "vol": 19},
    "20_navigation": {"name": "Navigation / AI", "name_cn": "导航/AI", "icon": "🗺️", "color": "#34495E", "ue": "NavigationSystem", "vol": 20},
    "21_editor_framework": {"name": "Editor Framework", "name_cn": "编辑器框架", "icon": "✏️", "color": "#2C3E50", "ue": "Editor Mode / Toolkit", "vol": 21},
    "22_networking": {"name": "Networking & Multiplayer", "name_cn": "网络与多人", "icon": "🔗", "color": "#D35400", "ue": "Replication + RPC", "vol": 22},
    "23_platform_abstraction": {"name": "Platform Abstraction", "name_cn": "平台抽象层", "icon": "💻", "color": "#7F8C8D", "ue": "GenericPlatform", "vol": 23},
    "24_optional_modules": {"name": "Optional Modules", "name_cn": "可选功能模块", "icon": "🧩", "color": "#BDC3C7", "ue": "Plugin / Feature Pack", "vol": 24},
}


# ============================================================================
# 数据加载工具
# ============================================================================

def load_scan_data():
    """加载扫描统计数据 (scan_result.json)"""
    data_path = os.path.join(LOCAL_OUTPUT_DIR, "scan_result.json")
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_available_reports():
    """
    获取可用的报告列表
    返回 [(category_id, module_name, has_report), ...]
    """
    available = []
    
    # 检查本地文件
    for cat_id, cfg in MODULE_CATEGORIES.items():
        report_path = os.path.join(LOCAL_OUTPUT_DIR, f"{cat_id}.md")
        has_report = os.path.exists(report_path)
        
        entry = {
            "id": cat_id,
            "name_en": cfg["name"],
            "name_cn": cfg.get("name_cn", ""),
            "icon": cfg.get("icon", ""),
            "color": cfg.get("color", "#333"),
            "ue_equivalent": cfg.get("ue", ""),
            "has_report": has_report,
            "volume": cfg.get("vol", 0),
            "is_highlight": cfg.get("highlight", False),
        }
        
        # 如果有扫描数据，补充统计信息
        scan_data = load_scan_data()
        if scan_data and "slices" in scan_data and cat_id in scan_data["slices"]:
            sl = scan_data["slices"][cat_id]
            entry["file_count"] = sl.get("file_count", 0)
            entry["total_lines"] = sl.get("total_lines", 0)
            entry["total_size"] = sl.get("total_size", 0)
        
        available.append(entry)
    
    # 按 volume 排序
    available.sort(key=lambda x: x["volume"])
    return available


def load_markdown_content(filename):
    """加载并转换 Markdown 文件为 HTML"""
    file_path = os.path.join(LOCAL_OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 使用 Python-Markdown 转 HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br',
            'sane_lists',
        ],
        extension_configs={
            'codehilite': {'guess_lang': False, 'css_class': 'highlight'},
        }
    )
    
    return html_content


# ============================================================================
# 路由定义
# ============================================================================

@app.route('/')
def index():
    """首页 — 展示所有模块概览卡片"""
    reports = get_available_reports()
    scan_data = load_scan_data()
    
    # 统计信息
    total_modules = len([r for r in reports if r["has_report"]])
    total_files = sum(r.get("file_count", 0) for r in reports)
    total_lines = sum(r.get("total_lines", 0) for r in reports) if reports else 0
    
    stats = {
        "modules_analyzed": total_modules,
        "total_modules": len(reports),
        "total_files": total_files,
        "total_lines": total_lines,
    }
    
    if scan_data:
        stats["source_version"] = "Godot 4.6"
    
    return render_template('index.html',
                           site=SITE_CONFIG,
                           modules=reports,
                           stats=stats,
                           active_page='home')


@app.route('/module/<module_id>')
def module_detail(module_id):
    """模块详情页 — 展示单个分析报告的完整内容"""
    if module_id not in MODULE_CATEGORIES:
        abort(404)
    
    cfg = MODULE_CATEGORIES[module_id]
    filename = f"{module_id}.md"
    
    content_html = load_markdown_content(filename)
    
    if not content_html:
        # 报告尚未生成，显示占位信息
        return render_template('module_placeholder.html',
                               site=SITE_CONFIG,
                               module_id=module_id,
                               config=cfg,
                               active_page=module_id)
    
    # 获取相邻模块（用于上下导航）
    all_ids = list(MODULE_CATEGORIES.keys())
    current_idx = all_ids.index(module_id) if module_id in all_ids else -1
    prev_module = MODULE_CATEGORIES[all_ids[current_idx - 1]] if current_idx > 0 else None
    next_module = MODULE_CATEGORIES[all_ids[current_idx + 1]] if current_idx < len(all_ids) - 1 else None
    
    return render_template('module_detail.html',
                           site=SITE_CONFIG,
                           module_id=module_id,
                           config=cfg,
                           content_html=content_html,
                           prev_module=prev_module,
                           next_module=next_module,
                           active_page=module_id)


@app.route('/comparison')
def comparison():
    """UE-Godot 对比总表页面"""
    content_html = load_markdown_content('ue_godot_comparison.md')
    
    return render_template('comparison.html',
                           site=SITE_CONFIG,
                           content_html=content_html,
                           active_page='comparison')


@app.route('/api/modules')
def api_modules():
    """API: 返回所有模块列表 (JSON)"""
    reports = get_available_reports()
    return jsonify(reports)


@app.route('/api/module/<module_id>')
def api_module(module_id):
    """API: 返回单个模块的原始 Markdown 内容"""
    if module_id not in MODULE_CATEGORIES:
        return jsonify({"error": "Module not found"}), 404
    
    filepath = os.path.join(LOCAL_OUTPUT_DIR, f"{module_id}.md")
    if not os.path.exists(filepath):
        return jsonify({"error": "Report not yet generated"}), 404
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "id": module_id,
        "config": MODULE_CATEGORIES[module_id],
        "content": content,
    })


# ============================================================================
# 开发服务器入口
# ============================================================================

if __name__ == '__main__':
    print("""
╔═════════════════════════════════════════════════════════╗
║                                                           ║
║   Godot Source Analysis - Web Viewer                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
