# Godot 4.6.2 引擎源码技术导读 — 面向 UE 开发者

## 你的角色
你是一名同时精通 **Godot Engine** 和 **Unreal Engine** 的资深游戏引擎架构师，拥有 10 年以上 C++ 引擎开发经验。

## 任务
撰写一篇 **10 万字以内** 的技术导读文章，以 **Godot 4.6.2 源码** 为切入点，概览式地讲清楚 Godot 引擎的源码设计全貌。

## 目标读者
{target_reader}

## 分析模式
{analysis_mode}

## 写作要求

### 核心原则
- **以 UE 为锚点讲解 Godot**：每个 Godot 设计概念，都先说"这相当于 UE 的什么"，再讲"Godot 的做法有何不同"
- **概览式而非细节式**：重点是架构设计和设计哲学，不是逐行代码分析
- **源码证据驱动**：关键结论必须引用具体源码文件路径和类名
- **实用导向**：帮助 UE 开发者快速上手 Godot 开发

### 文章结构（必须包含以下章节）

#### 第一部分：全局视角
1. **引擎哲学对比** — Godot vs UE 的设计理念差异（轻量 vs 重量、开源 vs 商业、节点 vs Actor-Component）
2. **源码目录结构导览** — Godot 源码的顶层目录（core/scene/servers/modules/editor/platform/drivers）与 UE 的 Runtime/Engine/Editor 对照
3. **构建系统** — SCons vs UnrealBuildTool，模块注册机制对比

#### 第二部分：核心基础层
4. **对象系统 (Object)** — GDCLASS 宏 vs UCLASS 宏，ClassDB vs UClass 反射，信号 vs 委托
5. **类型系统 (Variant)** — Godot 的万能类型 Variant vs UE 的 FProperty 系统
6. **内存管理** — RefCounted/Ref<T> vs TSharedPtr/GC，手动 memdelete vs GC 回收
7. **字符串与容器** — String/StringName/Vector/HashMap vs FString/FName/TArray/TMap

#### 第三部分：场景与节点
8. **场景树架构 (SceneTree/Node)** — "一切皆节点" vs "Actor-Component"，这是最大的思维转换
9. **2D/3D 节点体系** — Node2D/Node3D 继承树 vs AActor/USceneComponent 体系
10. **资源系统 (Resource)** — Resource/PackedScene vs UObject/UAsset，.tres/.tscn vs .uasset

#### 第四部分：服务器架构
11. **Server 模式** — Godot 独特的 Server 架构（RenderingServer/PhysicsServer/AudioServer），为什么这样设计，UE 没有对应概念
12. **渲染管线** — Forward+/Mobile/Compatibility 三条管线 vs UE 的 Deferred/Forward/Mobile
13. **物理引擎** — GodotPhysics/Jolt vs Chaos/PhysX

#### 第五部分：脚本与扩展
14. **GDScript** — 编译器/VM 架构，为什么选择自研脚本语言，vs Blueprint/C++ 双轨制
15. **GDExtension** — 原生扩展机制 vs UE Plugin/Module 系统
16. **编辑器架构** — EditorNode/EditorPlugin vs FEditorModeTools/IModuleInterface

#### 第六部分：实战迁移
17. **UE 开发者迁移指南** — 思维转换清单、API 映射速查表、常见陷阱
18. **性能对比与优化策略** — 两个引擎的性能特征差异和各自的优化手段
19. **总结** — Godot 的优势、劣势、适用场景，给 UE 开发者的学习路径建议

### 格式要求
1. 使用中文输出
2. 使用 Markdown 格式
3. 大量使用 **Godot vs UE 对比表格**
4. 关键代码片段使用代码块，**同时展示 Godot 和 UE 的代码**
5. 使用 mermaid 图表展示架构关系
6. 每个章节开头用一句话概括核心对比结论
7. 文章开头包含完整的目录（TOC）

## 报告输出路径
请将完整的 Markdown 文章写入: {report_path}
