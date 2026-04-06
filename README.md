# GodotBuddy

> **Godot 引擎 AI 分析工具集** — 面向有 Unreal Engine 经验的游戏开发者

GodotBuddy 是一套完整的 Godot 引擎分析工具，包含两大核心能力：

| 模式 | 说明 | 目标用户 |
|------|------|---------|
| **🎮 项目分析** | 扫描 GDScript 游戏项目 → AI 生成深度分析报告 | Godot 游戏开发者 |
| **🔍 源码分析** | 扫描 Godot C++ 引擎源码 → 按 24 个模块生成面向 UE 开发者的架构分析报告 | 想深入了解引擎实现的开发者 |
| **🌐 Web 展示** | 交互式网站浏览所有分析报告（暗色引擎风格 UI） | 所有读者 |

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- （源码分析模式需要）OpenAI API Key 或其他 LLM API Key
- （项目分析模式需要）knot-cli（可选，用于 Claude 分析）

### 启动方式

```bash
# 双击运行，或命令行：
start_godotbuddy.bat

# 模式 1: GDScript 项目分析（默认）
start_godotbuddy.bat
start_godotbuddy.bat --project ThirdPersonShooter
start_godotbuddy.bat --dir "D:\Project\MyGame"
start_godotbuddy.bat --scan-only          # 仅扫描不分析

# 模式 2: Godot 引擎源码分析
start_godotbuddy.bat --source              # 使用 config.ini 中配置的源码路径
start_godotbuddy.bat --source --scan-only  # 仅扫描验证
start_godotbuddy.bat --source --modules 02_object_system,06_rendering_server,13_script_system

# 模式 3: 启动 Web 展示平台
start_godotbuddy.bat --web                # http://localhost:5000
```

---

## 📁 项目结构

```
GodotBuddy/
├── start_godotbuddy.bat           # ★ 统一启动入口（双模式）
├── config.ini                    # 全局配置（含两种模式的配置节）
│
├── Scripts/                      # 核心脚本目录
│   ├── godotbuddy.py             # [项目分析] 主入口
│   ├── godot_project_scanner.py # [项目分析] GDScript/场景文件扫描器
│   ├── ai_analyzer.py            # [项目分析] AI 分析模块 (knot-cli)
│   ├── knot_cli_setup.py         # [项目分析] Knot CLI 自动安装工具
│   │
│   └── SourceAnalyzer/           # [源码分析] 引擎源码分析模块 ★NEW★
│       ├── categories.py         #   24 个引擎模块分类定义（含 UE 对标映射）
│       ├── slicer.py             #   C++ 源码切片器（按模块分类归档）
│       ├── analyzer.py           #   LLM 分析引擎（OpenAI/Claude/本地模型）
│       └── reporter.py           #   MD 报告生成器（面向 UE 开发者格式化输出）
│
├── SourceAnalyzerWeb/            # ★ Web 展示平台 ★NEW★
│   ├── app.py                   # Flask 主应用（路由 + 数据加载）
│   ├── requirements.txt         # flask + markdown
│   ├── templates/
│   │   ├── index.html           #   首页（Hero + 24 模块卡片网格）
│   │   ├── module_detail.html   #   模块详情（MD 报告渲染 + TOC 导航）
│   │   ├── module_placeholder.html  # 占位页（未生成报告时）
│   │   └── comparison.html      #   UE vs Godot 对比总表页
│   └── static/
│       ├── css/style.css        #   完整样式（暗色引擎风格主题）
│       └── js/app.js            #   搜索、过滤、交互逻辑
│
├── Prompt/                       # AI 系统提示词
│   └── system_prompt.md          # GodotBuddy 角色定义 + 分析方法论
│
├── Reports/                      # 项目分析报告输出
│   └── GodotBuddyReport_*.md
│
├── SourceAnalyzerOutput/         # 源码分析报告输出（运行后自动创建）★NEW★
│   ├── README.md                 # 总索引
│   ├── ue_godot_comparison.md    # UE-Godot 对照总表
│   ├── scan_result.json          # 扫描统计数据
│   ├── analysis_results.json     # LLM 原始返回
│   └── [module_id].md            # 各模块分析报告 × 24
│
├── Skills/                       # IDE Skill 定义
│   └── GodotBuddy/SKILL.md
│
└── README.md                     # 本文件
```

---

## ⚙️ 配置说明

所有配置集中在 `config.ini` 一个文件中：

```ini
; ====== 项目分析配置（原有功能）=====
[General]
version = 1.0
reports_base_dir = Reports/

[Analysis]
cli_tool_command = knot-cli
cli_tool_model = claude-4.6-opus
analysis_mode = agent

[Scanner]
ignore_dirs = .godot, .import, addons, build, export, android, ios
scan_extensions = .gd, .tscn, .tres, .gdshader, .cfg, .import

[Project:YourProjectName]
project_dir = D:\Path\To\Your\Godot\Project
analysis_focus = all


; ====== 源码分析配置（新增功能）=====
[SourceAnalyzer]
godot_source_dir = D:\Path\To\godot-4.6     ; Godot 引擎源码根目录
llm_backend = openai                        ; openai / anthropic / custom
api_key = sk-xxx                            ; API Key
base_url =                                 ; 自定义接口地址（Ollama/vLLM等留空）
model = gpt-4o                              ; 模型名称
temperature = 0.3                           ; LLM 温度
output_dir = SourceAnalyzerOutput           ; 报告输出目录
modules =                                   ; 指定模块(逗号分隔)，留空=全量
max_files_per_module = 25
max_file_tokens = 8000
scan_only = false
```

---

## 📘 源码分析的 24 个模块

源码分析将 Godot 4.6 的 C++ 源码按以下 24 个模块分类，每个模块都标注了与 Unreal Engine 的对应关系：

| ID | 模块 | UE 对标 | 重点 |
|----|------|--------|------|
| 01 | 核心基础层 | Core Module | |
| 02 | **对象系统** | UObject + 反射 | ⭐ |
| 03 | 内存管理 | FMemory + SmartPtrs | |
| 04 | 数学库 | Math Module | |
| 05 | IO 与文件系统 | PlatformFile + Archive | |
| 06 | **渲染服务器** | RHI + Renderer | ⭐ |
| 07 | 图形驱动层 | VulkanRHI / D3D11RHI | |
| 08 | 场景树 - 2D | UMG / Slate | |
| 09 | 场景树 - 3D | AActor / Component | |
| 10 | **场景树核心** | UWorld / Level | ⭐ |
| 11 | 物理 - 2D | Chaos Physics 2D | |
| 12 | 物理 - 3D | Chaos / PhysX | |
| 13 | **脚本系统** | Blueprint VM + C# | ⭐ |
| 14 | 动画系统 | AnimInstance / ABP | |
| 15 | 资源系统 | UObject Asset System | |
| 16 | 导入管线 | Factory / Import Pipeline | |
| 17 | 音频系统 | Audio Runtime | |
| 18 | 输入系统 | Enhanced Input | |
| 19 | UI 系统 | UMG Widget | |
| 20 | 导航系统 | NavigationSystem | |
| 21 | 编辑器框架 | Editor Mode / Toolkit | |
| 22 | 网络多人 | Replication + RPC | |
| 23 | 平台抽象层 | GenericPlatform | |
| 24 | 可选功能模块 | Plugin / Feature Pack | |

---

## 📄 报告示例结构（源码分析）

每个模块的分析报告包含：

```markdown
# [Module Name] 源码深度解析

> `category_id` | **UE 对标**: XXX

## ℹ️ 模块元信息
| 功能描述 | ... |
| UE 等价物 | ... |
| 源码文件数 | ... |
| 代码总行数 | ... |

## 📌 一句话总结
> 用一句 UE 开发者能懂的话概括这个模块

## 🏗️ 架构概览
## 🔑 核心类/结构详解（每个关键类单独表格）
## 💡 设计决策 & 亮点
## ⚠️ 注意事项 / 开发者陷阱
## 🔄 完整数据流 / 调用链
## 🆚 与 UE 的深度对比（多维度对比表）
## 📚 关键源码索引
## 🔗 相关模块
```

---

## 🌐 Web 平台特性

启动 `--web` 模式或直接运行 Flask：

```bash
cd SourceAnalyzerWeb
pip install -r requirements.txt
python app.py    # 或: start_godotbuddy.bat --web
```

- **首页**: Hero 统计区域 + 24 个模块卡片网格（每张卡片独立配色）
- **详情页**: Markdown 实时渲染 + 自动 TOC 目录导航 + 上下翻页
- **对比页**: UE vs Godot 概念对照总表 + 架构模式对比
- **搜索过滤**: 实时关键词搜索 / 只看重点 / 只看已生成
- **响应式设计**: 手机 / 平板 / 桌面全适配
- **API 接口**: `/api/modules`, `/api/module/<id>` JSON 数据

---

## 🔧 扩展开发

### 添加新的 LLM 后端

在 `Scripts/SourceAnalyzer/analyzer.py` 中继承 `LLMBackend` 类即可。

### 添加新的源码分析模块

编辑 `Scripts/SourceAnalyzer/categories.py`，在 `MODULE_CATEGORIES` 字典中添加新条目。

### 自定义 Web 主题

修改 `SourceAnalyzerWeb/static/css/style.css` 中的 CSS 变量（`:root` 部分）。

---

## ⚠️ 注意事项

1. **API Key 安全**: 不要将 API Key 提交到 Git。建议通过环境变量设置。
2. **Token 用量**: 源码全量分析 24 个模块预计消耗 ~200K-500K input tokens。
3. **Godot 源码大小**: 完整仓库约 5-8GB（含 .git），建议使用 `--depth 1` 浅克隆。
4. **Python 版本**: 需要 Python 3.9+（源码分析器使用了 dataclass 等 3.7+ 特性）。
5. **依赖安装**:
   ```bash
   # 项目分析模式：纯标准库，无需额外安装
   # 源码分析模式：
   pip install openai    # 或 anthropic
   # Web 展示模式：
   pip install flask markdown
   ```

---

## 📋 版本历史

| 版本 | 变更 |
|------|------|
| v1.0 | GDScript 项目分析（knot-cli + Claude） |
| v2.0 | 新增 Godot 引擎 C++ 源码分析 + Web 展示平台 |

---

## 📄 License

MIT License
