#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Godot 项目扫描器 (godot_project_scanner.py)

功能：
  1. 扫描 Godot 项目目录，提取项目结构信息
  2. 解析 project.godot 配置文件
  3. 收集所有 GDScript 文件及其类结构
  4. 解析 .tscn 场景文件的节点树
  5. 提取输入映射、自动加载、物理层等配置
  6. 生成结构化的项目分析上下文

依赖：仅使用 Python 标准库
"""

import os
import re
import json
import configparser
from collections import defaultdict
from datetime import datetime


# ============================================================
# project.godot 解析
# ============================================================

def parse_project_godot(project_dir):
    """
    解析 project.godot 文件，提取项目配置信息。
    
    :param project_dir: Godot 项目根目录
    :return: dict 项目配置信息
    """
    godot_file = os.path.join(project_dir, "project.godot")
    if not os.path.exists(godot_file):
        return {"error": f"未找到 project.godot: {godot_file}"}
    
    config = {
        "project_name": "",
        "description": "",
        "main_scene": "",
        "engine_version": "",
        "features": [],
        "autoloads": {},
        "input_actions": {},
        "physics_layers": {},
        "display": {},
        "rendering": {},
    }
    
    current_section = ""
    
    with open(godot_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith(";"):
                continue
            
            # 解析 section
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue
            
            # 解析键值对
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                
                # 去除字符串引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                
                if current_section == "application":
                    if key == "config/name":
                        config["project_name"] = value
                    elif key == "config/description":
                        config["description"] = value
                    elif key == "run/main_scene":
                        config["main_scene"] = value
                    elif key == "config/features":
                        # 解析 PackedStringArray
                        features_match = re.findall(r'"([^"]*)"', value)
                        config["features"] = features_match
                        # 从 features 推断引擎版本
                        for f_item in features_match:
                            if re.match(r'^\d+\.\d+', f_item):
                                config["engine_version"] = f_item
                
                elif current_section == "autoload":
                    # 自动加载格式: Name="*res://path/script.gd"
                    autoload_path = value.lstrip("*")
                    config["autoloads"][key] = autoload_path
                
                elif current_section == "input":
                    # 输入映射（简化提取动作名）
                    config["input_actions"][key] = "configured"
                
                elif current_section == "layer_names":
                    config["physics_layers"][key] = value
                
                elif current_section == "display":
                    config["display"][key] = value
                
                elif current_section == "rendering":
                    config["rendering"][key] = value
                
                elif current_section == "physics":
                    if "physics" not in config:
                        config["physics"] = {}
                    config["physics"][key] = value
    
    return config


# ============================================================
# GDScript 文件分析
# ============================================================

def analyze_gdscript_file(filepath):
    """
    分析单个 GDScript 文件，提取类结构信息。
    
    :param filepath: .gd 文件路径
    :return: dict 脚本分析结果
    """
    result = {
        "path": filepath,
        "class_name": "",
        "extends": "",
        "line_count": 0,
        "signals": [],
        "enums": [],
        "constants": [],
        "exports": [],
        "onready_vars": [],
        "variables": [],
        "functions": [],
        "rpc_functions": [],
        "dependencies": [],  # preload/load 引用
        "has_ready": False,
        "has_process": False,
        "has_physics_process": False,
        "has_input": False,
    }
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        result["error"] = str(e)
        return result
    
    result["line_count"] = len(lines)
    
    current_enum = None
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 跳过注释和空行
        if not stripped or stripped.startswith("#"):
            continue
        
        # class_name
        match = re.match(r'^class_name\s+(\w+)', stripped)
        if match:
            result["class_name"] = match.group(1)
            continue
        
        # extends
        match = re.match(r'^extends\s+(\w+)', stripped)
        if match:
            result["extends"] = match.group(1)
            continue
        
        # signal
        match = re.match(r'^signal\s+(\w+)', stripped)
        if match:
            result["signals"].append(match.group(1))
            continue
        
        # enum
        match = re.match(r'^enum\s+(\w+)\s*\{', stripped)
        if match:
            result["enums"].append(match.group(1))
            continue
        
        # const
        match = re.match(r'^const\s+(\w+)', stripped)
        if match:
            result["constants"].append(match.group(1))
            continue
        
        # @export
        match = re.match(r'^@export\s+var\s+(\w+)', stripped)
        if match:
            result["exports"].append(match.group(1))
            continue
        
        # @onready
        match = re.match(r'^@onready\s+var\s+(\w+)', stripped)
        if match:
            result["onready_vars"].append(match.group(1))
            continue
        
        # var（普通变量）
        match = re.match(r'^var\s+(\w+)', stripped)
        if match:
            result["variables"].append(match.group(1))
            continue
        
        # func（函数定义）
        match = re.match(r'^func\s+(\w+)\s*\(', stripped)
        if match:
            func_name = match.group(1)
            result["functions"].append(func_name)
            
            # 检查特殊函数
            if func_name == "_ready":
                result["has_ready"] = True
            elif func_name == "_process":
                result["has_process"] = True
            elif func_name == "_physics_process":
                result["has_physics_process"] = True
            elif func_name == "_input" or func_name == "_unhandled_input":
                result["has_input"] = True
            continue
        
        # @rpc 函数
        if stripped.startswith("@rpc"):
            # 下一行应该是 func
            pass  # 标记在 func 解析时处理
        
        # RPC 函数检测（旧式）
        match = re.match(r'^@rpc\b', stripped)
        if match:
            # 查找下一个 func
            for j in range(i, min(i + 3, len(lines))):
                next_line = lines[j].strip()
                func_match = re.match(r'^func\s+(\w+)', next_line)
                if func_match:
                    result["rpc_functions"].append(func_match.group(1))
                    break
        
        # preload/load 依赖
        for dep_match in re.finditer(r'(?:preload|load)\s*\(\s*"([^"]+)"\s*\)', stripped):
            result["dependencies"].append(dep_match.group(1))
    
    return result


# ============================================================
# 场景文件分析
# ============================================================

def analyze_scene_file(filepath):
    """
    分析 .tscn 场景文件，提取节点树结构。
    
    :param filepath: .tscn 文件路径
    :return: dict 场景分析结果
    """
    result = {
        "path": filepath,
        "format_version": "",
        "external_resources": [],
        "nodes": [],
        "root_node": None,
        "scripts": [],
        "signals_connected": [],
    }
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        result["error"] = str(e)
        return result
    
    # 解析头部
    header_match = re.match(r'\[gd_scene\s+([^\]]+)\]', content)
    if header_match:
        result["format_version"] = header_match.group(1)
    
    # 解析外部资源引用
    for match in re.finditer(r'\[ext_resource\s+type="([^"]+)"[^]]*path="([^"]+)"[^]]*\]', content):
        res_type = match.group(1)
        res_path = match.group(2)
        result["external_resources"].append({
            "type": res_type,
            "path": res_path,
        })
        if res_type == "Script":
            result["scripts"].append(res_path)
    
    # 解析节点
    for match in re.finditer(
        r'\[node\s+name="([^"]+)"\s+(?:type="([^"]+)")?[^]]*(?:parent="([^"]*)")?[^]]*\]',
        content
    ):
        node_name = match.group(1)
        node_type = match.group(2) or ""
        parent = match.group(3)
        
        node_info = {
            "name": node_name,
            "type": node_type,
            "parent": parent if parent else "(root)",
        }
        result["nodes"].append(node_info)
        
        if parent is None or parent == "":
            # 可能是根节点（parent 属性缺失表示根节点）
            if result["root_node"] is None:
                result["root_node"] = node_info
    
    # 解析信号连接
    for match in re.finditer(
        r'\[connection\s+signal="([^"]+)"\s+from="([^"]+)"\s+to="([^"]+)"\s+method="([^"]+)"',
        content
    ):
        result["signals_connected"].append({
            "signal": match.group(1),
            "from": match.group(2),
            "to": match.group(3),
            "method": match.group(4),
        })
    
    return result


# ============================================================
# 项目全局扫描
# ============================================================

def scan_project(project_dir, ignore_dirs=None, scan_extensions=None):
    """
    扫描整个 Godot 项目，收集所有文件信息。
    
    :param project_dir: 项目根目录
    :param ignore_dirs: 忽略的目录列表
    :param scan_extensions: 扫描的文件扩展名列表
    :return: dict 项目扫描结果
    """
    if ignore_dirs is None:
        ignore_dirs = [".godot", ".import", "addons", "build", "export", "android", "ios"]
    if scan_extensions is None:
        scan_extensions = [".gd", ".tscn", ".tres", ".gdshader", ".cfg"]
    
    result = {
        "project_dir": project_dir,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_config": parse_project_godot(project_dir),
        "gdscript_files": [],
        "scene_files": [],
        "resource_files": [],
        "shader_files": [],
        "other_files": [],
        "statistics": {
            "total_files": 0,
            "gdscript_count": 0,
            "scene_count": 0,
            "resource_count": 0,
            "shader_count": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_signals": 0,
            "total_exports": 0,
        },
        "class_registry": {},  # class_name -> file_path 映射
        "dependency_graph": {},  # file -> [dependencies] 映射
        "autoload_scripts": {},  # autoload_name -> script_analysis
    }
    
    # 遍历项目目录
    for root, dirs, files in os.walk(project_dir):
        # 过滤忽略目录
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, project_dir).replace("\\", "/")
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in scan_extensions:
                continue
            
            result["statistics"]["total_files"] += 1
            
            if ext == ".gd":
                # 分析 GDScript 文件
                script_info = analyze_gdscript_file(filepath)
                script_info["rel_path"] = rel_path
                result["gdscript_files"].append(script_info)
                result["statistics"]["gdscript_count"] += 1
                result["statistics"]["total_lines"] += script_info.get("line_count", 0)
                result["statistics"]["total_functions"] += len(script_info.get("functions", []))
                result["statistics"]["total_signals"] += len(script_info.get("signals", []))
                result["statistics"]["total_exports"] += len(script_info.get("exports", []))
                
                # 注册 class_name
                if script_info.get("class_name"):
                    result["class_registry"][script_info["class_name"]] = rel_path
                
                # 记录依赖关系
                if script_info.get("dependencies"):
                    result["dependency_graph"][rel_path] = script_info["dependencies"]
            
            elif ext == ".tscn":
                # 分析场景文件
                scene_info = analyze_scene_file(filepath)
                scene_info["rel_path"] = rel_path
                result["scene_files"].append(scene_info)
                result["statistics"]["scene_count"] += 1
            
            elif ext == ".tres":
                result["resource_files"].append({"rel_path": rel_path})
                result["statistics"]["resource_count"] += 1
            
            elif ext == ".gdshader":
                result["shader_files"].append({"rel_path": rel_path})
                result["statistics"]["shader_count"] += 1
            
            else:
                result["other_files"].append({"rel_path": rel_path})
    
    # 分析 autoload 脚本
    autoloads = result["project_config"].get("autoloads", {})
    for name, path in autoloads.items():
        # 将 res:// 路径转换为实际路径
        if path.startswith("res://"):
            actual_path = os.path.join(project_dir, path[6:])
            if os.path.exists(actual_path) and actual_path.endswith(".gd"):
                script_info = analyze_gdscript_file(actual_path)
                result["autoload_scripts"][name] = script_info
    
    return result


# ============================================================
# 分析上下文生成
# ============================================================

def generate_analysis_context(scan_result, analysis_focus="all"):
    """
    根据扫描结果生成结构化的分析上下文文本。
    
    :param scan_result: scan_project() 的返回结果
    :param analysis_focus: 分析重点
    :return: str 分析上下文文本
    """
    ctx = []
    config = scan_result["project_config"]
    stats = scan_result["statistics"]
    
    # 项目基本信息
    ctx.append("# Godot 项目分析上下文")
    ctx.append("")
    ctx.append("## 项目基本信息")
    ctx.append(f"- **项目名称**: {config.get('project_name', '未知')}")
    ctx.append(f"- **项目描述**: {config.get('description', '无')}")
    ctx.append(f"- **引擎版本**: Godot {config.get('engine_version', '未知')}")
    ctx.append(f"- **主场景**: {config.get('main_scene', '未设置')}")
    ctx.append(f"- **项目目录**: {scan_result['project_dir']}")
    ctx.append(f"- **扫描时间**: {scan_result['scan_time']}")
    ctx.append("")
    
    # 统计信息
    ctx.append("## 项目统计")
    ctx.append(f"- 总文件数: {stats['total_files']}")
    ctx.append(f"- GDScript 文件: {stats['gdscript_count']}")
    ctx.append(f"- 场景文件: {stats['scene_count']}")
    ctx.append(f"- 资源文件: {stats['resource_count']}")
    ctx.append(f"- 着色器文件: {stats['shader_count']}")
    ctx.append(f"- 总代码行数: {stats['total_lines']}")
    ctx.append(f"- 总函数数: {stats['total_functions']}")
    ctx.append(f"- 总信号数: {stats['total_signals']}")
    ctx.append(f"- 总导出变量数: {stats['total_exports']}")
    ctx.append("")
    
    # 自动加载
    if config.get("autoloads"):
        ctx.append("## 自动加载 (Autoload)")
        for name, path in config["autoloads"].items():
            ctx.append(f"- **{name}**: `{path}`")
        ctx.append("")
    
    # 输入映射
    if config.get("input_actions"):
        ctx.append("## 输入映射 (Input Actions)")
        actions = list(config["input_actions"].keys())
        # 过滤掉 ui_ 开头的默认动作
        custom_actions = [a for a in actions if not a.startswith("ui_")]
        if custom_actions:
            ctx.append("### 自定义动作")
            for action in custom_actions:
                ctx.append(f"- `{action}`")
        ctx.append("")
    
    # 物理层
    if config.get("physics_layers"):
        ctx.append("## 物理层 (Physics Layers)")
        for layer, name in config["physics_layers"].items():
            ctx.append(f"- {layer}: {name}")
        ctx.append("")
    
    # 类注册表
    if scan_result.get("class_registry"):
        ctx.append("## 自定义类 (class_name)")
        for cls_name, file_path in scan_result["class_registry"].items():
            ctx.append(f"- **{cls_name}**: `{file_path}`")
        ctx.append("")
    
    # GDScript 文件详情
    ctx.append("## GDScript 文件详情")
    ctx.append("")
    
    for script in sorted(scan_result["gdscript_files"], key=lambda x: x.get("rel_path", "")):
        rel_path = script.get("rel_path", script.get("path", ""))
        ctx.append(f"### `{rel_path}`")
        
        info_parts = []
        if script.get("class_name"):
            info_parts.append(f"class_name: {script['class_name']}")
        if script.get("extends"):
            info_parts.append(f"extends: {script['extends']}")
        info_parts.append(f"{script.get('line_count', 0)} 行")
        ctx.append(f"- {' | '.join(info_parts)}")
        
        if script.get("signals"):
            ctx.append(f"- **信号**: {', '.join(script['signals'])}")
        if script.get("enums"):
            ctx.append(f"- **枚举**: {', '.join(script['enums'])}")
        if script.get("exports"):
            ctx.append(f"- **导出变量**: {', '.join(script['exports'])}")
        if script.get("onready_vars"):
            ctx.append(f"- **@onready 变量**: {', '.join(script['onready_vars'])}")
        if script.get("functions"):
            ctx.append(f"- **函数**: {', '.join(script['functions'])}")
        if script.get("rpc_functions"):
            ctx.append(f"- **RPC 函数**: {', '.join(script['rpc_functions'])}")
        if script.get("dependencies"):
            ctx.append(f"- **依赖**: {', '.join(script['dependencies'])}")
        
        # 特殊函数标记
        special = []
        if script.get("has_ready"):
            special.append("_ready")
        if script.get("has_process"):
            special.append("_process")
        if script.get("has_physics_process"):
            special.append("_physics_process")
        if script.get("has_input"):
            special.append("_input")
        if special:
            ctx.append(f"- **生命周期**: {', '.join(special)}")
        
        ctx.append("")
    
    # 场景文件详情
    if scan_result.get("scene_files"):
        ctx.append("## 场景文件详情")
        ctx.append("")
        
        for scene in sorted(scan_result["scene_files"], key=lambda x: x.get("rel_path", "")):
            rel_path = scene.get("rel_path", scene.get("path", ""))
            ctx.append(f"### `{rel_path}`")
            
            if scene.get("root_node"):
                root = scene["root_node"]
                ctx.append(f"- **根节点**: {root.get('name', '?')} ({root.get('type', '?')})")
            
            if scene.get("scripts"):
                ctx.append(f"- **脚本**: {', '.join(scene['scripts'])}")
            
            if scene.get("nodes"):
                ctx.append(f"- **节点数**: {len(scene['nodes'])}")
                # 列出主要节点（前10个）
                for node in scene["nodes"][:10]:
                    parent_info = f" (parent: {node['parent']})" if node.get("parent") != "(root)" else ""
                    ctx.append(f"  - {node['name']}: {node.get('type', '?')}{parent_info}")
                if len(scene["nodes"]) > 10:
                    ctx.append(f"  - ... 还有 {len(scene['nodes']) - 10} 个节点")
            
            if scene.get("signals_connected"):
                ctx.append(f"- **信号连接**: {len(scene['signals_connected'])} 个")
                for conn in scene["signals_connected"][:5]:
                    ctx.append(f"  - {conn['from']}.{conn['signal']} -> {conn['to']}.{conn['method']}")
            
            ctx.append("")
    
    # 依赖关系图
    if scan_result.get("dependency_graph"):
        ctx.append("## 资源依赖关系")
        for file_path, deps in scan_result["dependency_graph"].items():
            ctx.append(f"- `{file_path}` 依赖:")
            for dep in deps:
                ctx.append(f"  - `{dep}`")
        ctx.append("")
    
    # 渲染配置
    if config.get("rendering"):
        ctx.append("## 渲染配置")
        for key, value in config["rendering"].items():
            ctx.append(f"- {key}: {value}")
        ctx.append("")
    
    # 显示配置
    if config.get("display"):
        ctx.append("## 显示配置")
        for key, value in config["display"].items():
            ctx.append(f"- {key}: {value}")
        ctx.append("")
    
    return "\n".join(ctx)


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python godot_project_scanner.py <项目目录>")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    
    if not os.path.exists(os.path.join(project_dir, "project.godot")):
        print(f"错误: {project_dir} 不是有效的 Godot 项目目录（未找到 project.godot）")
        sys.exit(1)
    
    print(f"正在扫描 Godot 项目: {project_dir}")
    result = scan_project(project_dir)
    
    # 输出 JSON 格式的扫描结果
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
