"""
Godot Source Analyzer - 模块分类配置
定义源码目录到分析类别的映射关系
"""

# ============================================================================
# 模块分类映射表
# 每个 category 包含: 名称、描述（用于报告）、源码目录匹配规则、优先级
# ============================================================================

MODULE_CATEGORIES = {
    
    "01_core_foundation": {
        "name": "核心基础层",
        "name_en": "Core Foundation",
        "description": "核心数据结构、内存管理、对象系统、数学库 — Godot 的地基",
        "ue_equivalent": "UE 的 Core 模块 (Runtime/Core)",
        "directories": ["core/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [
            "core/ext/",
            "core/crypto/",  # 单独分类
            "core/io/",      # 单独分类
            "core/math/",    # 可单独也可归入核心
            "core/object/",  # 重点模块，单独高亮
        ],
        "priority": 1,
        "estimated_files": 200,
    },

    "02_object_system": {
        "name": "对象系统",
        "name_en": "Object System",
        "description": "Object 基类、引用计数、信号槽机制、脚本绑定 — Godot 最核心的设计",
        "ue_equivalent": "UObject 系统 + 反射系统 + Delegate",
        "directories": ["core/object/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 1,
        "estimated_files": 30,
        "highlight": True,  # 高亮重点模块
    },

    "03_memory_management": {
        "name": "内存管理",
        "name_en": "Memory Management",
        "description": "内存分配器、SafeRef、RID、Variant 类型系统",
        "ue_equivalent": "UE 的 FMemory + TSharedPtr/TWeakPtr + Property System",
        "directories": ["core/memory/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 2,
        "estimated_files": 20,
    },

    "04_math_library": {
        "name": "数学库",
        "name_en": "Math Library",
        "description": "向量、矩阵、变换、AABB、平面等几何数学类型",
        "ue_equivalent": "UE 的 Math 模块 (FVector, FMatrix, FTransform 等)",
        "directories": ["core/math/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 2,
        "estimated_files": 40,
    },

    "05_io_system": {
        "name": "IO与文件系统",
        "name_en": "I/O & File System",
        "description": "文件访问、资源加载、序列化、压缩、网络IO",
        "ue_equivalent": "UE 的 PlatformFilesystem + Archive 系统 + AssetData",
        "directories": ["core/io/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 80,
    },

    "06_rendering_server": {
        "name": "渲染服务器",
        "name_en": "Rendering Server",
        "description": "RenderingServer 后端实现：Forward+ / Mobile / GL Compatibility 三条渲染管线",
        "ue_equivalent": "UE 的 RHI (Render Hardware Interface) + Renderer 模块",
        "directories": ["servers/rendering/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 1,
        "estimated_files": 300,
        "highlight": True,
    },

    "07_graphics_drivers": {
        "name": "图形驱动层",
        "name_en": "Graphics Drivers (RHI)",
        "description": "图形API抽象：Vulkan / D3D11 / OpenGL / Metal 驱动实现",
        "ue_equivalent": "UE 的 RHI 层 (VulkanRHI, D3D11Rhi, OpenGLRHI 等)",
        "directories": ["drivers/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 2,
        "estimated_files": 150,
    },

    "08_scene_tree_2d": {
        "name": "场景树 - 2D",
        "name_en": "Scene Tree - 2D",
        "description": "2D 节点系统：CanvasLayer、Control、各类 2D Node",
        "ue_equivalent": "UE UMG (Widget) + Slate + 2D 空间中的 Actor 体系",
        "directories": ["scene/2d/", "scene/gui/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 2,
        "estimated_files": 250,
    },

    "09_scene_tree_3d": {
        "name": "场景树 - 3D",
        "name_en": "Scene Tree - 3D",
        "description": "3D 节点系统：Node3D、MeshInstance3D、Camera3D 等",
        "ue_equivalent": "UE 的 AActor / USceneComponent / UPrimitiveComponent 体系",
        "directories": ["scene/3d/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 2,
        "estimated_files": 180,
    },

    "10_scene_main": {
        "name": "场景树核心",
        "name_en": "Scene Tree Core",
        "description": "SceneTree、Node 基类、NodePath、MainLoop — 场景管理中枢",
        "ue_equivalent": "UWorld + ULevel + ULayaout (GameFramework)",
        "directories": ["scene/main/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 1,
        "estimated_files": 60,
        "highlight": True,
    },

    "11_physics_2d": {
        "name": "物理引擎 - 2D",
        "name_en": "Physics Engine - 2D",
        "description": "PhysicsServer2D 实现（基于 Box2D），刚体碰撞检测",
        "ue_equivalent": "UE 的 Chaos Physics 2D / 旧 PhysX 2D 子系统",
        "directories": ["servers/physics_2d/", "scene/physics_body_2d/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 60,
    },

    "12_physics_3d": {
        "name": "物理引擎 - 3D",
        "name_en": "Physics Engine - 3D",
        "description": "PhysicsServer3D 实现（基于 Godot Physics / Jolt / Bullet）",
        "ue_equivalent": "UE 的 Chaos Physics / PhysX 集成",
        "directories": ["servers/physics_3d/", "scene/physics_body_3d/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 120,
    },

    "13_script_system": {
        "name": "脚本系统",
        "name_en": "Script System",
        "description": "GDScript 编译器与VM、C# 绑定、脚本实例管理、扩展 API",
        "ue_equivalent": "UE 的 UFunction/UScript + Blueprint VM + C#（via Mono/ILCPP）",
        "directories": ["modules/gdscript/", "core/variant/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 1,
        "estimated_files": 150,
        "highlight": True,
    },

    "14_animation_system": {
        "name": "动画系统",
        "name_en": "Animation System",
        "description": "AnimationPlayer、AnimationTree、AnimationNode 状态机、骨骼动画、BlendSpace",
        "ue_equivalent": "UE 的 AnimInstance / AnimBlueprint / Skeleton / BlendSpace",
        "directories": ["scene/animation/", "servers/animation/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 100,
    },

    "15_resource_system": {
        "name": "资源系统",
        "name_en": "Resource System",
        "description": "Resource 加载缓存、RefCount、PackedScene、.tres 格式",
        "ue_equivalent": "UE 的 UObject + Soft/Hard Reference + AssetRegistry",
        "directories": ["core/io/resource.h"],  # 核心头文件
        "file_patterns": ["resource.cpp", "resource.h", "resource_loader.cpp", "resource_saver.cpp"],
        # 资源系统比较分散，需要特殊处理
        "scan_mode": "focused",
        "focus_files": [
            "core/io/resource.h",
            "core/io/resource.cpp",
        ],
        "priority": 2,
        "estimated_files": 30,
    },

    "16_import_pipeline": {
        "name": "导入管线",
        "name_en": "Import Pipeline",
        "description": "资源导入器链：纹理/模型/音频/字体/.tscn/.tres 导入流程",
        "ue_equivalent": "UE 的 Factory 系统 (UFactory) + Editor 数据资产管线",
        "directories": ["editor/import/", "scene/resources/importer/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 100,
    },

    "17_audio_system": {
        "name": "音频系统",
        "name_en": "Audio System",
        "description": "AudioServer、音频总线(Bus)、音频流、空间音效、各平台后端",
        "ue_equivalent": "UE 的 AudioRuntime + AudioSynthesis + SoundWave / SoundCue",
        "directories": ["servers/audio/", "scene/audio/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 4,
        "estimated_files": 60,
    },

    "18_input_system": {
        "name": "输入系统",
        "name_en": "Input System",
        "description": "InputEvent、InputMap、动作映射、键盘/鼠标/手柄/触摸输入",
        "ue_equivalent": "UE 的 EnhancedInputSystem + Keybinding / ActionMapping",
        "directories": ["core/input/", "main/input_default.cpp"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 40,
    },

    "19_ui_system": {
        "name": "UI系统",
        "name_en": "UI System",
        "description": "Control 节点体系、主题(Theme)、布局容器、RichText、GUI皮肤",
        "ue_equivalent": "UE UMG (Unreal Motion Graphics) + Slate",
        "directories": ["scene/gui/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 3,
        "estimated_files": 200,
    },

    "20_navigation": {
        "name": "导航系统",
        "name_en": "Navigation System",
        "description": "NavigationServer、导航网格生成、寻路算法、避障",
        "ue_equivalent": "UE 的 NavigationSystem (RecastDetour) + AI Controller MoveTo",
        "directories": ["modules/navigation/", "servers/navigation/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 4,
        "estimated_files": 50,
    },

    "21_editor_framework": {
        "name": "编辑器框架",
        "name_en": "Editor Framework",
        "description": "EditorNode、EditorPlugin、Inspector Dock、编辑器插件架构",
        "ue_equivalent": "UE Editor Module (EditorMode / FEditorToolkit / DetailsPanel)",
        "directories": ["editor/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": ["editor/import/", "editor/plugins/"],  # 单独处理
        "priority": 4,
        "estimated_files": 300,
    },

    "22_networking": {
        "name": "网络与多人",
        "name_en": "Networking & Multiplayer",
        "description": "High-level Multiplayer API、RPC、状态同步、WebRTC",
        "ue_equivalent": "UE Replication System + RPC + OnlineSubsystem + NetDriver",
        "directories":["scene/multiplayer/", "servers/networking/", "modules/webrtc/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 4,
        "estimated_files": 80,
    },

    "23_platform_abstraction": {
        "name": "平台抽象层",
        "name_en": "Platform Abstraction Layer",
        "description": "各平台入口：Windows/macOS/Linux/Android/iOS/Web",
        "ue_equivalent": "UE 的 Platform abstraction (GenericPlatform → WindowsPlatform etc.)",
        "directories": ["platform/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [],
        "priority": 5,
        "estimated_files": 400,
    },

    "24_optional_modules": {
        "name": "可选功能模块",
        "name_en": "Optional Modules",
        "description": "glTF 导出/导入、FBX、Vulkan、Certs、等等",
        "ue_equivalent": "UE 的 Plugin / Feature Pack 体系",
        "directories": ["modules/"],
        "file_patterns": ["*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": [
            "modules/gdscript/",
            "modules/navigation/",
            "modules/webrtc/",
        ],
        "priority": 5,
        "estimated_files": 500,
    },
}

# 分析时每个文件的最大token数（超出则截断）
MAX_FILE_TOKENS = 8000

# LLM分析的批次大小（每次送入LLM的文件数）
ANALYSIS_BATCH_SIZE = 5

# 输出目录
OUTPUT_DIR = "output"

# 源码根目录（运行时通过 --source 参数指定）
SOURCE_ROOT = ""

# 目标读者背景
TARGET_READER_BACKGROUND = """
目标读者是有 Unreal Engine 开发经验的游戏开发者。
他们熟悉以下 UE 概念：
- UObject 反射系统和 GC
- AActor / UComponent 世界构建模式
- TSharedPtr / TWeakObjectPtr 智能指针
- UProperty / UProperty 序列化
- Blueprint / C++ 混合开发
- Chaos Physics / PhysX
- 渲染线程和 RHI 抽象
- GameplayAbilitySystem / EnhancedInput

对比时请多用 UE 概念类比帮助理解。
"""
