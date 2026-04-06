"""
Godot Source Analyzer - LLM 分析引擎
调用大模型对代码切片进行深度语义分析

支持多种 LLM 后端：
  - OpenAI API (GPT-4 / GPT-4o)
  - Anthropic Claude
  - 本地 Ollama (可选)
  - 自定义 OpenAI 兼容接口 (如 vLLM, LM Studio 等)
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """单次分析结果"""
    category_id: str
    module_name: str
    
    # 分析内容（MD 格式）
    overview: str = ""                    # 架构概览
    core_classes: List[Dict] = field(default_factory=list)  # 核心类详解列表
    design_decisions: str = ""            # 设计决策与亮点
    pitfalls: str = ""                    # 注意事项/坑
    data_flow: str = ""                   # 数据流/调用链
    ue_comparison: str = ""               # 与 UE 的对比总结
    source_index: List[str] = field(default_factory=list)   # 源码索引
    raw_response: str = ""                # 原始 LLM 返回
    
    # 元信息
    model_used: str = ""
    tokens_used: int = 0
    analysis_time_sec: float = 0.0


# ============================================================================
# LLM 后端抽象层
# ============================================================================

class LLMBackend(ABC):
    """LLM 后端基类"""
    
    @abstractmethod
    def analyze(self, prompt: str, system_prompt: str = "") -> str:
        """发送分析请求，返回文本结果"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """返回当前使用的模型名称"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """估算 token 数量"""
        pass


class OpenAIBackend(LLMBackend):
    """OpenAI / 兼容 API 后端"""
    
    def __init__(self, api_key: str = None, base_url: str = None,
                 model: str = "gpt-4o", temperature: float = 0.3):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env or pass api_key param.")
        
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", 
                         "https://api.openai.com/v1")).rstrip("/")
        self.model = model
        self.temperature = temperature
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("Please install: pip install openai")
        
        logger.info(f"OpenAI backend initialized: model={model}, base={self.base_url}")
    
    def get_model_name(self) -> str:
        return f"openai/{self.model}"
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 3  # 粗略估算
    
    def analyze(self, prompt: str, system_prompt: str = "") -> str:
        import openai
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=16000,
        )
        
        result = response.choices[0].message.content
        usage = response.usage
        logger.info(f"  LLM response: {usage.prompt_tokens} in / {usage.completion_tokens} out tokens")
        return result


class AnthropicBackend(LLMBackend):
    """Anthropic Claude 后端"""
    
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514",
                 temperature: float = 0.3):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required.")
        
        self.model = model
        self.temperature = temperature
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install: pip install anthropic")
        
        logger.info(f"Anthropic backend initialized: model={model}")
    
    def get_model_name(self) -> str:
        return f"anthropic/{self.model}"
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 3
    
    def analyze(self, prompt: str, system_prompt: str = "") -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        result = response.content[0].text
        logger.info(f"  Claude response received")
        return result


# ============================================================================
# 分析引擎核心
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """你是一位资深的游戏引擎架构师，精通 Unreal Engine、Unity 和 Godot 引擎源码。

你的任务是对 Godot 引擎的某个模块进行深度源码分析，并输出面向有 UE 经验的开发者的分析报告。

{target_reader_background}

## 输出要求

请严格按照以下 Markdown 结构输出分析报告（不要省略任何章节）：

---

# {module_name}

## 📌 一句话总结
> 用一句UE开发者能立刻理解的话概括这个模块的核心职责和设计定位

## 🏗️ 架构概览
- 模块的职责边界是什么？
- 内部如何划分子模块/子系统？画出关键类的关系（用文字描述继承和组合关系）
- 与其他模块的依赖关系
- 整体数据流向（从用户操作到引擎内部的路径）
- 核心设计模式（观察者、命令、工厂、单例等）

## 🔑 核心类/结构详解
对每个关键类，按以下格式输出：

### ClassName
| 属性 | 说明 |
|------|------|
| **文件位置** | `path/to/file.h` |
| **角色** | 这个类在整体中扮演什么角色 |
| **关键成员变量** | 列出最重要的 3-5 个成员及其作用 |
| **关键方法** | 列出最核心的 3-5 个方法，每个方法一句话描述 |
| **UE 对比** | 类似于 UE 的什么？（如：类似 UWorld，但更轻量） |
| **线程安全** | 是线程安全的吗？用了什么同步机制 |

## 💡 设计决策 & 亮点
- 为什么这样设计？（分析设计者的意图）
- 有哪些巧妙的设计模式或技巧？
- 与其他引擎相比的独特之处
- 性能优化策略

## ⚠️ 注意事项 / 开发者陷阱
- 使用时容易踩的坑（至少 3 条）
- 性能瓶颈在哪里
- 需要特别注意的生命周期管理
- 常见错误用法及正确做法

## 🔄 完整数据流 / 调用链
选取 2-3 个典型场景，从用户API调用到最终执行的完整链路：
- 场景1：（最常见的使用场景）
- 场景2：（另一个重要场景）

每条链路格式：`User API → 中间层 → Server层 → Driver层 → GPU`

## 🆚 与 UE 的深度对比
从以下维度对比：

| 维度 | Godot 实现 | Unreal Engine 实现 | 差异分析 |
|------|-----------|-------------------|---------|
| 架构模式 | | | |
| 内存管理 | | | |
| 多线程策略 | | | |
| 扩展性 | | | |
| 性能特征 | | | |
| 学习曲线 | | | |

## 📚 关键源码索引
列出本模块必读的核心文件（按重要性排序）：
1. **文件路径** — 一句话说明为什么重要
2. ...

## 🔗 相关模块
- 上游依赖哪些模块？
- 被哪些模块依赖？
- 与哪些模块紧密协作？

---"""


class AnalysisEngine:
    """
    LLM 分析引擎
    
    将代码切片送入大模型进行深度分析
    """
    
    def __init__(self, llm_backend: LLMBackend, categories_config: Dict,
                 max_file_tokens: int = 8000):
        self.llm = llm_backend
        self.categories = categories_config
        self.max_file_tokens = max_file_tokens
        self.results: Dict[str, AnalysisResult] = {}
    
    def _build_analysis_prompt(self, category_id: str, 
                                code_files: List, 
                                category_cfg: Dict) -> str:
        """
        为一个模块构建完整的分析 prompt
        
        将该模块的关键代码片段 + 元信息组合成 prompt
        """
        module_name = category_cfg.get("name", category_id)
        description = category_cfg.get("description", "")
        ue_equiv = category_cfg.get("ue_equivalent", "")
        
        # 收集代码片段
        code_sections = []
        total_chars = 0
        char_limit = 120000  # context window 限制（留余量给输出）
        
        for cf in code_files:
            if hasattr(cf, 'content') and cf.content:
                section = f"""\
### 文件: {cf.relative_path}
```cpp
{cf.content}
```
"""
                if total_chars + len(section) > char_limit:
                    remaining = char_limit - total_chars
                    if remaining > 500:
                        code_sections.append(section[:remaining] + "\n```\n\n// [截断 - 内容过长]")
                    break
                
                code_sections.append(section)
                total_chars += len(section)
        
        code_content = "\n".join(code_sections)
        
        prompt = f"""## 任务：深度分析 Godot 引擎模块 — 「{module_name}」

### 模块基本信息
- **模块名**: {module_name}
- **模块ID**: {category_id}
- **功能描述**: {description}
- **UE 等价物**: {ue_equiv}
- **包含文件数**: {len(code_files)}

### 源码内容
以下是本模块的核心源码文件内容（已按重要性排序）：

{code_content}

请基于以上源码，输出完整深度的分析报告。重点关注架构设计、实现原理、以及与 Unreal Engine 的对比。
确保报告对有 UE 经验的开发者具有实际参考价值。"""

        return prompt
    
    def _build_system_prompt(self, category_cfg: Dict) -> str:
        """构建系统提示词"""
        module_name = category_cfg.get("name", "Unknown")
        
        from config.categories import TARGET_READER_BACKGROUND
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            module_name=module_name,
            target_reader_background=TARGET_READER_BACKGROUND
        )
    
    def analyze_module(self, category_id: str, 
                       code_files: List,
                       retry_count: int = 2) -> AnalysisResult:
        """
        对单个模块执行完整分析
        
        Args:
            category_id: 模块分类ID
            code_files: 已加载内容的 CodeFile 列表
            retry_count: 失败重试次数
        
        Returns:
            AnalysisResult
        """
        if category_id not in self.categories:
            raise ValueError(f"Unknown category: {category_id}")
        
        cfg = self.categories[category_id]
        module_name = cfg.get("name", category_id)
        
        logger.info(f"🔍 Analyzing module: {module_name} ({len(code_files)} files)")
        
        # 构建 prompt
        user_prompt = self._build_analysis_prompt(category_id, code_files, cfg)
        system_prompt = self._build_system_prompt(cfg)
        
        # 调用 LLM（带重试）
        raw_result = ""
        start_time = time.time()
        
        for attempt in range(retry_count + 1):
            try:
                raw_result = self.llm.analyze(user_prompt, system_prompt)
                break
            except Exception as e:
                logger.warning(f"  Attempt {attempt+1}/{retry_count+1} failed: {e}")
                if attempt < retry_count:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"  Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"All {retry_count+1} attempts failed") from e
        
        elapsed = time.time() - start_time
        
        result = AnalysisResult(
            category_id=category_id,
            module_name=module_name,
            raw_response=raw_result,
            model_used=self.llm.get_model_name(),
            analysis_time_sec=elapsed,
        )
        
        # 尝试解析结构化字段（原始 MD 直接存入 overview）
        result.overview = raw_result
        
        # 记录结果
        self.results[category_id] = result
        
        logger.info(f"✅ Module '{module_name}' analyzed in {elapsed:.1f}s")
        
        return result
    
    def batch_analyze(self, slices: Dict, slicer_instance,
                      categories_to_run: List[str] = None,
                      progress_callback=None) -> Dict[str, AnalysisResult]:
        """
        批量分析所有模块
        
        Args:
            slices: CodeSlicer.scan() 返回的结果
            slicer_instance: CodeSlicer 实例（用于加载文件内容）
            categories_to_run: 只分析指定的类别，None 表示全部
            progress_callback: 进度回调 function(current, total, module_name)
        
        Returns:
            {category_id: AnalysisResult}
        """
        # 决定要分析的类别
        if categories_to_run is None:
            # 只分析有文件的类别
            cats_to_analyze = [
                cid for cid, sl in slices.items()
                if sl.total_lines > 0
            ]
        else:
            cats_to_analyze = categories_to_run
        
        total = len(cats_to_analyze)
        
        for idx, cat_id in enumerate(cats_to_analyze):
            sl = slices.get(cat_id)
            if not sl or len(sl.files) == 0:
                continue
            
            cfg = self.categories.get(cat_id, {})
            module_name = cfg.get("name", cat_id)
            
            if progress_callback:
                progress_callback(idx + 1, total, module_name)
            
            # 获取代表性文件并加载内容
            representative_files = slicer_instance.get_slice_for_analysis(cat_id, max_files=25)
            
            for cf in representative_files:
                slicer_instance.load_file_content(cf, max_tokens=self.max_file_tokens)
            
            # 执行分析
            try:
                result = self.analyze_module(cat_id, representative_files)
                self.results[cat_id] = result
            except Exception as e:
                logger.error(f"❌ Failed to analyze '{module_name}': {e}")
                # 创建空结果标记失败
                self.results[cat_id] = AnalysisResult(
                    category_id=cat_id,
                    module_name=module_name,
                    overview=f"# {module_name}\n\n⚠️ **分析失败**: {str(e)}"
                )
            
            # 避免触发 API rate limit
            if idx < total - 1:
                time.sleep(2)
        
        return self.results
    
    def export_results(self, output_dir: str):
        """导出所有分析结果为 JSON"""
        os.makedirs(output_dir, exist_ok=True)
        
        export_data = {
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": self.llm.get_model_name(),
            "total_modules": len(self.results),
            "results": {}
        }
        
        for cat_id, result in self.results.items():
            export_data["results"][cat_id] = {
                "module_name": result.module_name,
                "model_used": result.model_used,
                "tokens_used": result.tokens_used,
                "analysis_time_sec": round(result.analysis_time_sec, 1),
                "overview_preview": result.overview[:500] + "..." if len(result.overview) > 500 else result.overview,
            }
        
        output_path = os.path.join(output_dir, "analysis_results.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Analysis results exported to: {output_path}")
