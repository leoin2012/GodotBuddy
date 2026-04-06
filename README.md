# GodotBuddy

> **Godot 引擎 AI 分析工具集** — 面向有 Unreal Engine 经验的游戏开发者

GodotBuddy 是一套完整的 Godot 引擎分析工具，统一使用 **knot-cli** 作为 AI 分析引擎，包含以下核心能力：

| 模式 | 说明 | 目标用户 |
|------|------|---------|
| **🎮 项目分析** | 扫描 GDScript 游戏项目 → AI 生成深度分析报告 | Godot 游戏开发者 |
| **🔍 源码分析** | 扫描 Godot C++ 引擎源码 → 按 24 个模块生成面向 UE 开发者的架构分析报告 | 想深入了解引擎实现的开发者 |
| **📖 技术导读** | 生成 Godot vs UE 概览式技术导读文章（支持交叉对比模式） | UE 开发者快速了解 Godot |
| **🌐 Web 展示** | 交互式网站浏览所有分析报告（暗色引擎风格 UI） | 所有读者 |

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- knot-cli（AI 分析引擎，项目分析和源码分析共用）

### 启动方式

GodotBuddy 采用 **bat 启动器 + Python 主逻辑** 架构：
- `start_godotbuddy.bat` — 轻量启动器，仅负责检查 Python 环境并转发参数
- `start_godotbuddy.py` — 主逻辑入口，支持交互式菜单和命令行两种模式

```bash
# 双击 bat 或命令行启动 → 进入交互式菜单
start_godotbuddy.bat

# 命令行直接执行（跳过菜单）：
start_godotbuddy.bat --project TPS-Demo           # 分析指定项目
start_godotbuddy.bat --source                      # 全量源码分析（24 模块）
start_godotbuddy.bat --source --modules 02,06,13   # 分析指定模块
start_godotbuddy.bat --source --scan-only           # 仅扫描不分析
start_godotbuddy.bat --guide                        # 生成技术导读文章
start_godotbuddy.bat --web                          # 启动 Web 报告查看器
```

### 交互式菜单

无参数启动时进入交互式菜单，提供 5 个功能入口：

```
  +----------------------------------------------------------+
  |              GodotBuddy v2.0 - Analysis Hub              |
  +----------------------------------------------------------+
  |   [1] GDScript Project Analysis                          |
  |   [2] Godot Engine Source Analysis (per module)          |
  |   [3] Source Guide (Godot vs UE overview article)        |
  |   [4] Web Report Viewer                                  |
  |   [5] View Progress (OVERVIEW)                           |
  |   [0] Exit                                               |
  +----------------------------------------------------------+
```

---

## 📁 项目结构

```
GodotBuddy/
├── start_godotbuddy.bat           # ★ 启动器（检查 Python 环境，转发参数）
├── start_godotbuddy.py            # ★ 主逻辑入口（交互式菜单 + 命令行分派）
├── config.ini                     # 全局配置（所有模式的配置集中管理）
│
├── Scripts/                       # 核心脚本目录
│   ├── godotbuddy.py              # [项目分析] 主入口
│   ├── godot_project_scanner.py   # [项目分析] GDScript/场景文件扫描器
│   ├── ai_analyzer.py             # [项目分析] AI 分析模块 (knot-cli)
│   ├── knot_cli_setup.py          # [通用] Knot CLI 检测与自动安装
│   │
│   ├── godot_source_analyzer.py   # [源码分析] 主入口（扫描 + 分析 + Web）
│   └── SourceAnalyzer/            # [源码分析] 引擎源码分析子模块
│       ├── categories.py          #   24 个引擎模块分类定义（含 UE 对标映射）
│       ├── slicer.py              #   C++ 源码切片器（按模块分类归档）
│       ├── analyzer.py            #   knot-cli 分析引擎
│       └── reporter.py            #   MD 报告生成器（面向 UE 开发者格式化输出）
│
├── Prompt/                        # AI 系统提示词（外部 Prompt 模板，不在脚本中硬编码）
│   ├── system_prompt.md           #   GodotBuddy 角色定义 + 分析方法论
│   ├── project_analysis_prompt.md #   项目分析 Prompt 模板
│   ├── source_analysis_prompt.md  #   源码分析 Prompt 模板
│   └── source_guide_prompt.md     #   技术导读 Prompt 模板
│
├── Reports/                       # 报告输出目录
│   ├── GodotProjects/             #   项目分析报告
│   ├── GodotEngine/               #   源码分析报告
│   │   ├── OVERVIEW.md            #     分析计划与进度总览
│   │   ├── 4.6.2/                 #     技术导读文章输出目录
│   │   └── [module_id].md         #     各模块分析报告 × 24
│   └── GodotBuddyReport_*.md     #   旧版项目分析报告（兼容）
│
├── Cache/                         # 临时缓存目录（自动创建）
│   ├── context_*.md               #   扫描上下文缓存
│   ├── prompt_*.md                #   构建的 Prompt 缓存
│   ├── scan_*.json                #   扫描结果缓存
│   └── guide_prompt_*.md          #   技术导读 Prompt 缓存
│
├── SourceAnalyzerWeb/             # Web 展示平台
│   ├── app.py                     #   Flask 主应用（路由 + 数据加载）
│   ├── requirements.txt           #   flask + markdown
│   ├── templates/
│   │   ├── index.html             #     首页（Hero + 24 模块卡片网格）
│   │   ├── module_detail.html     #     模块详情（MD 报告渲染 + TOC 导航）
│   │   ├── module_placeholder.html#     占位页（未生成报告时）
│   │   └── comparison.html        #     UE vs Godot 对比总表页
│   └── static/
│       ├── css/style.css          #     完整样式（暗色引擎风格主题）
│       └── js/app.js              #     搜索、过滤、交互逻辑
│
├── Skills/                        # IDE Skill 定义
│   └── GodotBuddy/SKILL.md
│
└── README.md                      # 本文件
```

---

## ⚙️ 配置说明

所有配置集中在 `config.ini` 一个文件中，按功能分为以下配置节：

### `[General]` — 全局设置

```ini
[General]
version = 2.0
reports_base_dir =          ; 报告输出目录（留空使用默认 Reports/）
cache_base_dir =            ; 缓存目录（留空使用默认 Cache/）
```

### `[KnotCLI]` — 统一 AI 引擎配置

所有分析模式共用同一个 knot-cli 配置：

```ini
[KnotCLI]
command = knot-cli          ; CLI 工具命令名称
model = claude-4.6-opus     ; AI 模型
user_rules =                ; 用户规则文件路径（可选）
timeout = 1800              ; 执行超时时间（秒）
team_token =                ; 团队密钥（可选，用于自动安装）
cli_version =               ; 指定 knot-cli 版本（可选）
```

### `[ProjectAnalysis]` — 项目分析配置

```ini
[ProjectAnalysis]
prompt_file = Prompt/project_analysis_prompt.md
cli_args_template = chat -w "{project_dir}" -w "{godotbuddy_dir}" --codebase --model "{model}" ...
max_concurrent = 3          ; 批量分析最大并发数
```

### `[SourceAnalysis]` — 源码分析配置

```ini
[SourceAnalysis]
prompt_file = Prompt/source_analysis_prompt.md
godot_source_dir = D:\Project\Godot\GodotEngine       ; Godot 引擎源码目录
ue_source_dir = D:\Project\CrashBuddy_UAMO_0608\UnrealEngine  ; UE 源码（可选，启用交叉对比）
output_dir = Reports/GodotEngine
cli_args_template = chat -w "{source_dir}" -w "{ue_source_dir}" -w "{godotbuddy_dir}" --codebase ...
modules =                   ; 指定模块（逗号分隔，留空=全量 24 模块）
max_files_per_module = 25
max_file_tokens = 8000
```

### `[SourceGuide]` — 技术导读配置

```ini
[SourceGuide]
prompt_file = Prompt/source_guide_prompt.md
output_dir = Reports/GodotEngine/4.6.2
output_filename = Godot_4.6.2_Source_Guide_for_UE_Developers.md
cli_args_template = chat -w "{source_dir}" -w "{ue_source_dir}" -w "{godotbuddy_dir}" --codebase ...
```

### `[Scanner]` — 扫描器配置

```ini
[Scanner]
ignore_dirs = .godot, .import, addons, build, export, android, ios
scan_extensions = .gd, .tscn, .tres, .gdshader, .cfg, .import
max_script_lines = 500
parse_scene_tree = true
```

### `[Project:项目名]` — 项目配置

每个 Godot 游戏项目一个独立的 section：

```ini
[Project:ThirdPersonShooter-TPS-Demo]
project_dir = D:\Project\Godot\ThirdPersonShooter(tps)Demo
engine_version =            ; 留空自动检测
description =               ; 留空自动读取
analysis_focus = all        ; architecture / performance / code_quality / security / all
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

## 📖 技术导读（Source Guide）

技术导读是一篇面向 UE 开发者的 Godot 源码概览式技术文章，特点：

- **交叉对比模式**：配置了 UE 源码目录后，knot-cli 可同时搜索两个引擎源码进行源码级对比
- **Prompt 模板驱动**：通过 `Prompt/source_guide_prompt.md` 定义文章结构和分析要求
- **自动填充上下文**：根据 config.ini 配置动态生成目标读者描述和分析模式说明

生成命令：
```bash
start_godotbuddy.bat --guide
# 或在交互式菜单中选择 [3]
```

输出位置：`Reports/GodotEngine/4.6.2/`

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

### 自定义 Prompt 模板

所有 Prompt 均以外部 Markdown 文件形式存放在 `Prompt/` 目录，不在脚本中硬编码。
编辑对应的 `.md` 文件即可自定义分析行为，支持 `{target_reader}`、`{analysis_mode}`、`{report_path}` 等占位符。

### 添加新的源码分析模块

编辑 `Scripts/SourceAnalyzer/categories.py`，在 `MODULE_CATEGORIES` 字典中添加新条目。

### 自定义 knot-cli 命令模板

在 `config.ini` 各配置节的 `cli_args_template` 字段中自定义 knot-cli 调用参数，
支持的占位符包括：`{prompt_file}` `{report_path}` `{source_dir}` `{ue_source_dir}` `{godotbuddy_dir}` `{model}` `{user_rules}`

### 自定义 Web 主题

修改 `SourceAnalyzerWeb/static/css/style.css` 中的 CSS 变量（`:root` 部分）。

---

## ⚠️ 注意事项

1. **API Key 安全**: 不要将 API Key 提交到 Git。knot-cli 自身管理认证，无需在 config.ini 中配置 API Key。
2. **Token 用量**: 源码全量分析 24 个模块预计消耗大量 tokens，建议按需选择模块分析。
3. **Godot 源码大小**: 完整仓库约 5-8GB（含 .git），建议使用 `--depth 1` 浅克隆。
4. **Python 版本**: 需要 Python 3.8+。
5. **依赖安装**:
   ```bash
   # 项目分析 / 源码分析 / 技术导读：需要 knot-cli
   # Web 展示模式：
   pip install flask markdown
   ```

---

## 📋 版本历史

| 版本 | 变更 |
|------|------|
| v1.0 | GDScript 项目分析（knot-cli + Claude） |
| v2.0 | 架构重构：bat 启动器 + Python 主逻辑；交互式菜单；统一 knot-cli 引擎；新增 Godot 引擎 C++ 源码逐模块分析；新增技术导读生成（Godot vs UE 交叉对比）；Prompt 外部化（4 个 .md 模板）；Web 展示平台 |

---

## 📄 License

MIT License
