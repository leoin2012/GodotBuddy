"""
Godot Source Analyzer - 报告生成器
将 LLM 分析结果整理成面向开发者的精美 MD 报告
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    MD 报告生成器
    
    功能：
    - 生成总索引报告（目录页）
    - 为每个模块生成独立 MD 分析报告
    - 自动生成模块间交叉引用
    - 支持输出到本地文件或 GitHub Wiki 格式
    """
    
    def __init__(self, output_dir: str, categories_config: Dict,
                 target_reader: str = "unreal"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.categories = categories_config
        self.target_reader = target_reader
        
        # 按优先级排序的类别列表（用于生成目录）
        self._sorted_categories = sorted(
            categories_config.items(),
            key=lambda x: x[1].get("priority", 99)
        )
    
    def generate_all(self, analysis_results: Dict,
                     slices_data: Dict) -> Dict[str, Path]:
        """
        生成所有报告
        
        Returns:
            {category_id: report_file_path} 字典
        """
        generated_files = {}
        
        # 1. 生成总索引
        index_path = self.generate_index(analysis_results, slices_data)
        generated_files["__index__"] = index_path
        
        # 2. 生成各模块报告
        for cat_id, result in analysis_results.items():
            if cat_id == "__index__":
                continue
                
            cfg = self.categories.get(cat_id, {})
            
            # 获取对应的切片数据（用于补充元信息）
            slice_info = slices_data.get(cat_id)
            
            try:
                report_path = self.generate_module_report(cat_id, result, slice_info)
                generated_files[cat_id] = report_path
            except Exception as e:
                logger.error(f"Failed to generate report for {cat_id}: {e}")
        
        # 3. 生成汇总对比表
        summary_path = self.generate_ue_comparison_summary(analysis_results)
        generated_files["__summary__"] = summary_path
        
        logger.info(f"✅ All reports generated in: {self.output_dir}")
        
        return generated_files
    
    def generate_index(self, analysis_results: Dict,
                       slices_data: Dict) -> Path:
        """生成总索引 / README 页"""
        
        total_modules = len([r for r in analysis_results.values() 
                            if not r.module_name.startswith("__")])
        total_files = sum(
            sl.total_lines > 0 and len(sl.files) or 0
            for sl in (slices_data or {}).values()
        )
        total_lines = sum(
            sl.total_lines for sl in (slices_data or {}).values()
        )
        
        lines = []
        lines.append("# 🎮 Godot 4.6 源码全景分析报告")
        lines.append("")
        lines.append("> **目标读者**: 有 Unreal Engine 经验的游戏开发者")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 项目信息卡片
        lines.append("## 📋 项目概览")
        lines.append("")
        lines.append("| 属性 | 值 |")
        lines.append("|------|-----|")
        lines.append("| **引擎版本** | Godot 4.6 |")
        lines.append(f"| **分析模块数** | {total_modules} |")
        lines.append(f"| **涉及源码文件** | ~{total_files} |")
        lines.append(f"| **总代码行数** | ~{total_lines:,} |")
        lines.append(f"| **分析时间** | {time.strftime('%Y-%m-%d')} |")
        lines.append(f"| **分析方法** | AI 大模型深度语义分析 |")
        lines.append("")
        
        # 使用指南
        lines.append("## 📖 使用指南")
        lines.append("")
        lines.append("本报告按以下方式组织：")
        lines.append("")
        lines.append("- 📘 **Volume 1-5**: 核心基础层 — 建议最先阅读")
        lines.append("- 📗 **Volume 6-9**: 渲染与场景系统 — 引擎核心能力")
        lines.append("- 📙 **Volume 10-14**: 运行时子系统 — 物理/动画/音频等")
        lines.append("- 📕 **Volume 15+**: 工具链与平台 — 编辑器/平台抽象/可选模块")
        lines.append("")
        lines.append("每个模块报告包含：")
        lines.append("- 一句话总结 + UE 类比")
        lines.append("- 架构概览与核心类详解")
        lines.append("- 设计决策分析与性能注意事项")
        lines.append("- 完整调用链路追踪")
        lines.append("- 与 UE 的深度多维度对比表")
        lines.append("")
        
        # 目录
        lines.append("---")
        lines.append("")
        lines.append("## 📚 模块目录")
        lines.append("")
        
        current_volume = None
        for cat_id, cfg in self._sorted_categories:
            # 提取 volume 编号
            vol_num = cat_id.split("_")[0] if "_" in cat_id else "??"
            module_name = cfg.get("name", cat_id)
            description = cfg.get("description", "")
            ue_equiv = cfg.get("ue_equivalent", "")
            highlight = " ⭐" if cfg.get("highlight") else ""
            
            # Volume 分隔
            if vol_num != current_volume:
                current_volume = vol_num
                lines.append(f"### 📖 Volume {vol_num}")
                lines.append("")
            
            # 检查是否有对应的分析结果和代码
            has_result = cat_id in analysis_results
            sl = slices_data.get(cat_id)
            has_code = sl is not None and len(sl.files) > 0
            
            status_icon = "✅" if (has_result or has_code) else "⏳"
            file_link = f"[{module_name}](./{cat_id}.md)" if (has_result or has_code) else f"{module_name}"
            
            lines.append(f"- {status_icon} {file_link}{highlight}")
            lines.append(f"  - *{description}*")
            lines.append(f"  - `UE: {ue_equiv}`")
            lines.append("")
        
        # 快速导航：按功能分类
        lines.append("---")
        lines.append("")
        lines.append("## 🧭 快速导航（按功能域）")
        lines.append("")
        
        nav_groups = {
            "🏗️ 核心架构": ["01_core_foundation", "02_object_system", "03_memory_management",
                          "04_math_library", "05_io_system"],
            "🎨 渲染管线": ["06_rendering_server", "07_graphics_drivers"],
            "🌍 场景世界": ["08_scene_tree_2d", "09_scene_tree_3d", "10_scene_main"],
            "⚛️ 物理系统": ["11_physics_2d", "12_physics_3d"],
            "💻 脚本系统": ["13_script_system"],
            "🎬 动画系统": ["14_animation_system"],
            "🖥️ UI 系统": ["19_ui_system"],
            "🔊 音频系统": ["17_audio_system"],
            "🎮 输入系统": ["18_input_system"],
            "🗺️ 导航/AI": ["20_navigation"],
            "🔗 网络多人": ["22_networking"],
            "✏️ 编辑器": ["21_editor_framework"],
            "📦 平台/扩展": ["23_platform_abstraction", "24_optional_modules"],
        }
        
        for group_name, cat_ids in nav_groups.items():
            lines.append(f"### {group_name}")
            links = []
            for cid in cat_ids:
                if cid in self.categories:
                    name = self.categories[cid]["name"]
                    if cid in analysis_results or cid in slices_data:
                        links.append(f"[{name}](./{cid}.md)")
            if links:
                lines.append(" · ".join(links))
                lines.append("")
        
        # 附录说明
        lines.append("---")
        lines.append("")
        lines.append("## 📝 附录")
        lines.append("")
        lines.append("- [UE-Godot 概念对照总表](__summary__.md)")
        lines.append("- [分析原始数据](./analysis_results.json)")
        lines.append("- [源码扫描统计](./scan_result.json)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*本报告由 AI 源码分析工具自动生成于 {time.strftime('%Y-%m-%d %H:%M')}*")
        
        # 写入文件
        output_path = self.output_dir / "README.md"
        content = "\n".join(lines)
        self._write_file(output_path, content)
        
        return output_path
    
    def generate_module_report(self, category_id: str, 
                               analysis_result, 
                               slice_info) -> Path:
        """为单个模块生成完整 MD 报告"""
        
        cfg = self.categories.get(category_id, {})
        module_name = cfg.get("name", category_id)
        ue_equiv = cfg.get("ue_equivalent", "N/A")
        description = cfg.get("description", "")
        highlight = " ⭐ 重点模块" if cfg.get("highlight") else ""
        
        lines = []
        
        # === 头部 ===
        lines.append(f"# {module_name} 源码深度解析{highlight}")
        lines.append("")
        lines.append(f"> `{category_id}` | **UE 对标**: {ue_equiv}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # === 元信息栏 ===
        lines.append("## ℹ️ 模块元信息")
        lines.append("")
        lines.append("| 属性 | 详情 |")
        lines.append("|------|------|")
        lines.append(f"| **功能描述** | {description} |")
        lines.append(f"| **UE 等价物** | {ue_equiv} |")
        
        if slice_info:
            lines.append(f"| **源码文件数** | {len(slice_info.files)} |")
            lines.append(f"| **代码总行数** | {slice_info.total_lines:,} |")
            size_mb = slice_info.total_size / (1024*1024)
            lines.append(f"| **代码总量** | {size_mb:.2f} MB |")
        
        lines.append(f"| **分析模型** | {analysis_result.model_used} |")
        lines.append(f"| **分析耗时** | {analysis_result.analysis_time_sec:.1f}s |")
        lines.append("")
        
        # === LLM 分析内容 ===
        if analysis_result.overview:
            lines.append(analysis_result.overview)
        else:
            lines.append("*（暂无分析内容）*")
        
        # === 底部导航 ===
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🔗 相关模块")
        lines.append("")
        lines.append("← [返回总目录](./README.md)")
        lines.append("")
        
        output_path = self.output_dir / f"{category_id}.md"
        content = "\n".join(lines)
        self._write_file(output_path, content)
        
        return output_path
    
    def generate_ue_comparison_summary(self, analysis_results: Dict) -> Path:
        """生成 UE-Godot 概念对照总表"""
        
        lines = []
        lines.append("# 🆚 Godot vs Unreal Engine 概念对照总表")
        lines.append("")
        lines.append("> 从 Godot 各模块分析中提取的核心概念映射")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        lines.append("## 核心概念速查表")
        lines.append("")
        lines.append("| Godot 概念 | Unreal Engine 对应 | 关键差异 |")
        lines.append("|-----------|-------------------|---------|")
        
        # 预定义的核心概念映射
        concept_mappings = [
            ("Object (基类)", "UObject", "Godot 无 GC，用引用计数；UE 用标记清除 GC"),
            ("Node", "AActor / USceneComponent", "Godot Node 更轻量，无 Actor/Component 区分"),
            ("RefCounted", "TSharedPtr / TWeakPtr", "Godot 显式引用计数，UE 多种智能指针"),
            ("SceneTree", "UWorld + ULevel", "Godot 单一世界树；UE 可有多个 UWorld"),
            ("Resource", "UObject (Data Asset)", "类似但 Godot Resource 更轻量"),
            ("Signal", "Delegate / Event (Multicast)", "语法不同但语义相似"),
            ("GDScript VM", "Blueprint VM / Bytecode", "GDScript 更像 Python；BP 是可视化"),
            ("RenderingServer", "RHI + Renderer Module", "都是命令缓冲模式但 API 不同"),
            ("PhysicsServer", "PhysX / Chaos Physics Interface", "Godot 内置物理后端可替换"),
            ("Node3D", "USceneComponent + AActor", "Godot 统一 Node；UE 分层更细"),
            ("Control (UI)", "UWidget (UMG/Slate)", "都支持声明式布局"),
            ("AnimationPlayer", "UAnimInstance (AnimBP)", "Godot 声明式；UE 图形化状态机"),
            ("AudioBus", "SoundSubmix / Audio Bus", "概念几乎一致"),
            ("InputMap / Action", "EnhancedInput Action", "非常相似的 Action Mapping 思路"),
            ("NavigationServer", "UNavigationSystemV1 (Recast)", "都基于 Recast/Detour"),
            ("MultiplayerAPI", "Replication System + RPC", "Godot 高层API更简洁"),
            ("EditorPlugin", "Editor Mode / Editor Toolkit", "插件化思路一致"),
            ("RID (Resource ID)", "FResourceArray / FRHIResource", "都是 GPU 资源的句柄封装"),
            ("Variant 类型", "FProperty Variant", "动态类型系统，实现方式不同"),
        ]
        
        for godot_concept, ue_concept, diff in concept_mappings:
            lines.append(f"| {godot_concept} | {ue_concept} | {diff} |")
        
        lines.append("")
        
        # 架构模式对比
        lines.append("---")
        lines.append("")
        lines.append("## 架构模式对比")
        lines.append("")
        lines.append("| 维度 | Godot | Unreal Engine |")
        lines.append("|------|-------|--------------|")
        lines.append("| **编程范式** | 面向对象 + 数据驱动 (GDScript/C#) | 面向组件 (C++/Blueprint) |")
        lines.append("| **内存管理** | 引用计数为主 | 标记清除 GC + 智能指针 |")
        lines.append("| **场景组织** | 扁平 Node Tree | World → Level → Actor → Component |")
        lines.append("| **渲染架构** | Server 模式 (RenderingServer) | RHI → Renderer → SceneRenderer |")
        lines.append("| **脚本绑定** | GDExtension / C# (Mono) | UObject 反射 + Blueprint |")
        lines.append("| **编辑器扩展** | EditorPlugin (GDScript/C#) | Editor Module (C++/Plugin) |")
        lines.append("| **跨平台** | 自建 Platform 抽象 | GenericPlatform → XXXPlatform |")
        lines.append("| **开源协议** | MIT (完全自由商用) | 自定义（基于许可使用） |")
        lines.append("| **学习曲线** | 中低（GDScript 友好） | 中高（C++ 复杂度高） |")
        lines.append("")
        
        # 各模块详细链接
        lines.append("---")
        lines.append("")
        lines.append("## 📖 各模块详细分析")
        lines.append("")
        lines.append("| 模块 | UE 对照 | 详细报告 |")
        lines.append("|------|---------|---------|")
        
        for cat_id, cfg in self._sorted_categories:
            name = cfg.get("name", cat_id)
            ue_eq = cfg.get("ue_equivalent", "-")
            if cat_id in analysis_results:
                lines.append(f"| [{name}]({cat_id}.md) | {ue_eq} | [查看报告]({cat_id}.md) |")
            else:
                lines.append(f"| {name} | {ue_eq} | 待分析 |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*由 AI 源码分析工具自动生成*")
        
        output_path = self.output_dir / "ue_godot_comparison.md"
        content = "\n".join(lines)
        self._write_file(output_path, content)
        
        return output_path
    
    def _write_file(self, path: Path, content: str):
        """写入文件"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Written: {path}")


def main_test():
    """简单测试"""
    from config.categories import MODULE_CATEGORIES
    
    gen = ReportGenerator(
        output_dir="output",
        categories_config=MODULE_CATEGORIES,
    )
    
    # 创建假数据测试
    class FakeResult:
        module_name = "Test Module"
        model_used = "gpt-4o"
        overview = "# Test\n\nTest content"
        analysis_time_sec = 5.0
    
    class FakeSlice:
        files = ["a.cpp", "b.h"]
        total_lines = 1000
        total_size = 50000
    
    gen.generate_all({"test_cat": FakeResult()}, {"test_cat": FakeSlice()})
    print("Report generation test complete!")


if __name__ == "__main__":
    main_test()
