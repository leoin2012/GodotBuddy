"""
Godot Source Analyzer - 代码切片器
负责遍历 Godot 源码目录，按模块分类，输出结构化的代码片段
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """表示一个源码文件"""
    relative_path: str       # 相对于源码根目录的路径
    absolute_path: str       # 绝对路径
    category_id: str         # 所属分类ID
    file_size: int = 0        # 文件大小(bytes)
    line_count: int = 0       # 行数
    language: str = ""        # cpp / h / glsl / etc.
    content: str = ""          # 文件内容（延迟加载）
    is_loaded: bool = False


@dataclass 
class ModuleSlice:
    """表示一个模块的代码切片（一组相关文件）"""
    category_id: str
    category_name: str
    files: List[CodeFile] = field(default_factory=list)
    total_lines: int = 0
    total_size: int = 0
    
    def add_file(self, f: CodeFile):
        self.files.append(f)
        self.total_lines += f.line_count
        self.total_size += f.file_size


class CodeSlicer:
    """
    代码切片器
    遍历 Godot 源码树，按预定义的分类规则将文件归入不同模块
    """
    
    def __init__(self, source_root: str, categories_config: Dict):
        self.source_root = Path(source_root).resolve()
        self.categories = categories_config
        self.slices: Dict[str, ModuleSlice] = {}
        self.unclassified_files: List[CodeFile] = []
        
        if not self.source_root.exists():
            raise FileNotFoundError(f"Source root not found: {source_root}")
        
        logger.info(f"CodeSlicer initialized with source root: {self.source_root}")
    
    def _detect_language(self, filepath: str) -> str:
        """根据文件扩展名检测语言类型"""
        ext = Path(filepath).suffix.lower()
        lang_map = {
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'h',
            '.hh': 'h',
            '.hpp': 'h',
            '.c': 'c',
            '.glsl': 'glsl',
            '.vert': 'glsl',
            '.frag': 'glsl',
            '.comp': 'glsl',
            '.hlsl': 'hlsl',
            '.slang': 'slang',
            '.py': 'python',
            '.cfg': 'cfg',
            '.tcsn': 'tscn',
            '.tres': 'tres',
            '.xml': 'xml',
            '.json': 'json',
            '.gdnlib': 'gdns',
            '.cs': 'csharp',
        }
        return lang_map.get(ext, 'unknown')
    
    def _should_exclude(self, rel_path: str, exclude_patterns: List[str]) -> bool:
        """检查文件是否应该被排除"""
        for pattern in exclude_patterns:
            # 目录级排除
            if rel_path.startswith(pattern) or f"/{pattern}" in rel_path:
                return True
            # 通配符匹配
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if fnmatch.fnmatch(Path(rel_path).name, pattern):
                return True
        return False
    
    def _match_category(self, rel_path: str) -> Optional[str]:
        """
        将文件路径匹配到分类
        返回 category_id 或 None
        """
        # 标准化路径分隔符
        normalized = rel_path.replace("\\", "/")
        
        for cat_id, cat_cfg in self.categories.items():
            directories = cat_cfg.get("directories", [])
            
            for dir_pattern in directories:
                # 精确前缀匹配
                if normalized.startswith(dir_pattern):
                    # 检查排除规则
                    exclude_patterns = cat_cfg.get("exclude_patterns", [])
                    if not self._should_exclude(normalized, exclude_patterns):
                        return cat_id
                    break
                
                # 特殊模式：focus_files
                if cat_cfg.get("scan_mode") == "focused":
                    focus_files = cat_cfg.get("focus_files", [])
                    if normalized in focus_files:
                        return cat_id
        
        return None
    
    def scan(self, progress_callback=None) -> Dict[str, ModuleSlice]:
        """
        扫描源码目录，生成模块切片
        
        Args:
            progress_callback: 可选的进度回调 function(current, total)
        
        Returns:
            {category_id: ModuleSlice} 字典
        """
        logger.info("Starting source code scan...")
        
        # 初始化所有 slice
        for cat_id, cat_cfg in self.categories.items():
            self.slices[cat_id] = ModuleSlice(
                category_id=cat_id,
                category_name=cat_cfg.get("name", cat_id)
            )
        
        # 统计总文件数（用于进度）
        all_source_files = list(self._iter_source_files())
        total_files = len(all_source_files)
        processed = 0
        
        for file_path in all_source_files:
            try:
                rel_path = str(file_path.relative_to(self.source_root)).replace("\\", "/")
                
                # 获取文件信息
                stat = file_path.stat()
                
                code_file = CodeFile(
                    relative_path=rel_path,
                    absolute_path=str(file_path),
                    category_id="",  # 待分配
                    file_size=stat.st_size,
                    language=self._detect_language(str(file_path))
                )
                
                # 快速估算行数 (平均每行约 40 bytes)
                code_file.line_count = max(1, stat.st_size // 40)
                
                # 匹配分类
                matched_cat = self._match_category(rel_path)
                if matched_cat and matched_cat in self.slices:
                    code_file.category_id = matched_cat
                    self.slices[matched_cat].add_file(code_file)
                else:
                    self.unclassified_files.append(code_file)
                
                processed += 1
                if progress_callback and processed % 100 == 0:
                    progress_callback(processed, total_files)
                    
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
        
        # 打印统计
        self._print_stats(total_files)
        
        return self.slices
    
    def _iter_source_files(self):
        """迭代所有源码文件"""
        # 排除的顶层目录
        skip_dirs = {
            '.git', '.github', 'thirdparty', 'build', 'bin', '.vscode',
            'android', 'ios', 'platform/android', 'platform/ios/metal'
        }
        
        for root, dirs, files in os.walk(self.source_root):
            # 动态修改 dirs 来跳过不需要遍历的目录
            rel_root = Path(root).relative_to(self.source_root) if root != str(self.source_root) else Path(".")
            
            dirs_to_skip = set()
            for d in dirs:
                # 跳过第三方和构建产物
                if d in skip_dirs or d.startswith('.') or d == '__pycache__':
                    dirs_to_skip.add(d)
                # 跳过大型二进制/资源目录
                if d in {'assets', 'testdata', 'tests', 'test'}:
                    dirs_to_skip.add(d)
            
            for d in dirs_to_skip:
                if d in dirs:
                    dirs.remove(d)
            
            for fname in files:
                # 只要源码文件
                ext = Path(fname).suffix.lower()
                valid_exts = {'.cpp', '.h', '.hpp', '.c', '.cc', '.glsl', '.vert', 
                              '.frag', '.comp', '.hlsl', '.slang'}
                if ext not in valid_exts:
                    continue
                
                yield Path(root) / fname
    
    def load_file_content(self, code_file: CodeFile, max_tokens: int = 8000) -> str:
        """
        加载文件内容，如果超出 token 限制则智能截断
        
        截断策略：保留头部(类声明) + 尾部(可能有关键实现) + 中间采样
        """
        if code_file.is_loaded:
            return code_file.content
        
        try:
            with open(code_file.absolute_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            code_file.content = content
            code_file.is_loaded = True
            
            # 更新精确行数
            code_file.line_count = content.count('\n') + 1
            
            # 如果内容太长，进行智能截断
            lines = content.split('\n')
            if len(lines) > max_tokens // 2:  # 粗略估算: 1行 ≈ 2 tokens
                content = self._smart_truncate(lines, max_tokens)
                code_file.content = content
            
            return code_file.content
            
        except Exception as e:
            logger.error(f"Failed to load file {code_file.relative_path}: {e}")
            return ""
    
    def _smart_truncate(self, lines: List[str], max_tokens: int) -> str:
        """智能截断：保留头部 + 采样中间 + 保留尾部"""
        target_lines = min(len(lines), max_tokens // 2)
        
        if len(lines) <= target_lines:
            return '\n'.join(lines)
        
        head_count = target_lines // 3      # 前部 1/3
        tail_count = target_lines // 3      # 尾部 1/3  
        mid_count = target_lines - head_count - tail_count  # 中间部分
        
        # 头部完整保留
        head = lines[:head_count]
        
        # 中间均匀采样
        mid_region = lines[head_count:-tail_count]
        step = max(1, len(mid_region) // mid_count)
        mid_sampled = [mid_region[i] for i in range(0, len(mid_region), step)][:mid_count]
        
        # 尾部完整保留
        tail = lines[-tail_count:]
        
        result = head + [f"\n// ... 省略 {len(mid_region) - len(mid_sampled)} 行 ..."] + mid_sampled + tail
        return '\n'.join(result)
    
    def get_slice_for_analysis(self, category_id: str, max_files: int = 20) -> List[CodeFile]:
        """
        获取某个模块用于分析的代表性文件
        策略：优先取核心头文件 + 大型实现文件，控制总量
        """
        if category_id not in self.slices:
            return []
        
        slice_data = self.slices[category_id]
        files = sorted(slice_data.files, key=lambda f: f.file_size, reverse=True)
        
        # 优先取 .h 文件（接口定义）+ 大型 .cpp 文件（核心实现）
        header_files = [f for f in files if f.language == 'h']
        impl_files = [f for f in files if f.language == 'cpp']
        
        selected = []
        
        # 先取头文件（最多一半）
        for f in header_files[:max_files//2]:
            selected.append(f)
        
        # 再取实现文件
        remaining = max_files - len(selected)
        for f in impl_files[:remaining]:
            selected.append(f)
        
        return selected
    
    def _print_stats(self, total_scanned: int):
        """打印扫描统计信息"""
        print("\n" + "=" * 70)
        print("📊 Godot Source Scan Statistics")
        print("=" * 70)
        print(f"  Total source files scanned : {total_scanned}")
        print(f"  Categories classified      : {len([s for s in self.slices.values() if s.total_lines > 0])}")
        print(f"  Unclassified files          : {len(self.unclassified_files)}")
        print("-" * 70)
        
        # 按代码量排序
        sorted_slices = sorted(
            [(cid, s) for cid, s in self.slices.items() if s.total_lines > 0],
            key=lambda x: x[1].total_lines,
            reverse=True
        )
        
        print(f"  {'Category':<30} {'Files':>8} {'Lines':>12} {'Size':>12}")
        print(f"  {'-'*30} {'-'*8} {'-'*12} {'-'*12}")
        
        for cat_id, sl in sorted_slices:
            cfg = self.categories.get(cat_id, {})
            highlight = " ⭐" if cfg.get('highlight') else ""
            size_mb = sl.total_size / (1024 * 1024)
            print(f"  {sl.category_name:<28} {len(sl.files):>8} {sl.total_lines:>12,} {size_mb:>10.2f}MB{highlight}")
        
        print("=" * 70 + "\n")
    
    def export_scan_result(self, output_path: str):
        """导出扫描结果为 JSON（供后续分析使用）"""
        result = {
            "source_root": str(self.source_root),
            "total_slices": len(self.slices),
            "unclassified_count": len(self.unclassified_files),
            "slices": {}
        }
        
        for cat_id, sl in self.slices.items():
            cfg = self.categories.get(cat_id, {})
            result["slices"][cat_id] = {
                "category_name": sl.category_name,
                "file_count": len(sl.files),
                "total_lines": sl.total_lines,
                "total_size": sl.total_size,
                "ue_equivalent": cfg.get("ue_equivalent", ""),
                "files": [
                    {
                        "path": f.relative_path,
                        "size": f.file_size,
                        "lines": f.line_count,
                        "lang": f.language,
                    }
                    for f in sl.files
                ]
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Scan result exported to: {output_path}")


def main_test():
    """简单测试入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python slicer.py <godot_source_root>")
        sys.exit(1)
    
    from config.categories import MODULE_CATEGORIES
    
    slicer = CodeSlicer(sys.argv[1], MODULE_CATEGORIES)
    
    def on_progress(current, total):
        pct = current * 100 / total
        print(f"\r  Scanning... {pct:.1f}% ({current}/{total})", end="")
    
    slices = slicer.scan(progress_callback=on_progress)
    slicer.export_scan_result("output/scan_result.json")


if __name__ == "__main__":
    main_test()
