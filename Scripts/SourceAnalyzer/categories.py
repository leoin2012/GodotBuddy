"""
Godot Source Analyzer - 模块分类配置
定义源码目录到分析类别的映射关系

模块划分原则：
  1. 按 Godot 源码的实际目录结构和功能边界划分
  2. 每个模块聚焦一个明确的子系统，避免过大或过小
  3. 每个模块都标注 UE 对应物，方便交叉对比
  4. key_files 标注该模块的核心文件，引导 AI 优先阅读
  5. analysis_points 列出该模块必须覆盖的分析要点
"""

# ============================================================================
# 模块分类映射表 (28 个模块)
# ============================================================================

MODULE_CATEGORIES = {

    # ========================================================================
    # 第一层：核心基础 (Core Foundation)
    # ========================================================================

    "01_core_foundation": {
        "name": "核心基础层",
        "name_en": "Core Foundation",
        "description": "核心数据结构、模板容器、字符串、OS 抽象、错误处理、配置系统 — Godot 的地基",
        "ue_equivalent": "UE Runtime/Core 模块 (Containers, HAL, Misc)",
        "directories": ["core/"],
        "exclude_patterns": [
            "core/object/",     # → 02
            "core/variant/",    # → 03
            "core/math/",       # → 04
            "core/io/",         # → 05
            "core/input/",      # → 18
            "core/extension/",  # → 15
        ],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "core/typedefs.h",
            "core/templates/vector.h",
            "core/templates/hash_map.h",
            "core/templates/list.h",
            "core/templates/safe_refcount.h",
            "core/string/ustring.h",
            "core/string/string_name.h",
            "core/os/os.h",
            "core/os/memory.h",
            "core/os/thread.h",
            "core/os/mutex.h",
            "core/error/error_macros.h",
            "core/config/engine.h",
            "core/config/project_settings.h",
        ],
        "analysis_points": [
            "String vs FString: Godot 的 String 是 COW 还是 SSO？与 UE FString 的内存策略对比",
            "StringName vs FName: 两者都是字符串池化，实现差异是什么？",
            "Vector<T> vs TArray<T>: 增长策略、内存布局、迭代器设计对比",
            "HashMap vs TMap: 哈希策略、冲突解决、性能特征对比",
            "OS 抽象层 vs FGenericPlatformMisc: 平台抽象的粒度差异",
            "内存分配: memalloc/memrealloc/memfree vs FMemory::Malloc/Realloc/Free",
            "线程模型: Thread/Mutex/Semaphore vs FRunnable/FCriticalSection",
            "错误处理: ERR_FAIL_COND 宏族 vs check/ensure/verify 宏族",
            "ProjectSettings vs GConfig: 配置系统的设计差异",
        ],
    },

    "02_object_system": {
        "name": "对象系统",
        "name_en": "Object System",
        "description": "Object 基类、ClassDB 反射、GDCLASS 宏、信号槽、引用计数、消息队列",
        "ue_equivalent": "UObject 系统 + UClass 反射 + Delegate/MulticastDelegate",
        "directories": ["core/object/"],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "core/object/object.h",
            "core/object/object.cpp",
            "core/object/class_db.h",
            "core/object/class_db.cpp",
            "core/object/ref_counted.h",
            "core/object/method_bind.h",
            "core/object/script_language.h",
            "core/object/message_queue.h",
            "core/object/worker_thread_pool.h",
            "core/object/callable_method_pointer.h",
        ],
        "analysis_points": [
            "GDCLASS 宏 vs UCLASS 宏: 展开后的代码对比，各自注册了什么元数据",
            "ClassDB vs UClass: 反射信息的存储结构、查询方式、性能差异",
            "信号(Signal) vs 委托(Delegate): connect/disconnect/emit vs BindDynamic/Execute",
            "RefCounted vs UObject GC: 引用计数 vs 标记清除，各自的优劣",
            "Ref<T> vs TSharedPtr<T>: 智能指针的实现差异",
            "MethodBind vs UFunction: 方法绑定的实现机制对比",
            "MessageQueue vs GameThread 消息: 跨线程通信机制",
            "WorkerThreadPool vs FQueuedThreadPool: 线程池设计对比",
            "Object 生命周期: _init/_ready/_notification vs Constructor/PostInitProperties/BeginPlay",
        ],
    },

    "03_variant_type_system": {
        "name": "Variant 类型系统",
        "name_en": "Variant Type System",
        "description": "Variant 万能类型、类型转换、Callable、Array/Dictionary 动态容器",
        "ue_equivalent": "UE 的 FProperty 系统 + Blueprint 变量类型 + TVariant (C++17)",
        "directories": ["core/variant/"],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "core/variant/variant.h",
            "core/variant/variant.cpp",
            "core/variant/variant_call.cpp",
            "core/variant/variant_op.cpp",
            "core/variant/variant_utility.cpp",
            "core/variant/callable.h",
            "core/variant/dictionary.h",
            "core/variant/array.h",
            "core/variant/typed_array.h",
        ],
        "analysis_points": [
            "Variant 的内部存储: union 布局、类型标签、内存占用分析",
            "Variant vs FProperty: 动态类型 vs 静态反射属性，设计哲学差异",
            "Variant 类型转换: 隐式/显式转换规则，与 Blueprint 类型转换的对比",
            "Callable vs TFunction/TDelegate: 可调用对象的封装差异",
            "Array/Dictionary vs TArray/TMap: 动态容器 vs 模板容器的性能 trade-off",
            "Variant 在 GDScript VM 中的角色: 为什么 Godot 需要这个万能类型",
        ],
    },

    "04_math_library": {
        "name": "数学库",
        "name_en": "Math Library",
        "description": "向量、矩阵、变换、四元数、AABB、Basis、几何工具",
        "ue_equivalent": "UE Math 模块 (FVector, FMatrix, FTransform, FQuat)",
        "directories": ["core/math/"],
        "priority": 2,
        "key_files": [
            "core/math/vector2.h",
            "core/math/vector3.h",
            "core/math/basis.h",
            "core/math/transform_2d.h",
            "core/math/transform_3d.h",
            "core/math/quaternion.h",
            "core/math/aabb.h",
            "core/math/math_funcs.h",
            "core/math/geometry_2d.h",
            "core/math/geometry_3d.h",
        ],
        "analysis_points": [
            "Vector2/Vector3 vs FVector2D/FVector: 精度(float vs double)、SIMD 优化差异",
            "Basis vs FMatrix: 3x3 旋转矩阵 vs 4x4 矩阵，为什么 Godot 用 Basis",
            "Transform3D vs FTransform: 组合方式(Basis+Origin vs Rotation+Translation+Scale)",
            "坐标系差异: Godot Y-up 右手系 vs UE Z-up 左手系",
            "数学精度: REAL_T_IS_DOUBLE 编译选项 vs UE 的 LWC (Large World Coordinates)",
        ],
    },

    "05_io_resource_system": {
        "name": "IO 与资源系统",
        "name_en": "I/O & Resource System",
        "description": "文件访问、Resource 基类、资源加载/保存、序列化、.tres/.tscn 格式",
        "ue_equivalent": "UE FArchive + FAssetData + UPackage + AssetRegistry",
        "directories": ["core/io/"],
        "priority": 2,
        "key_files": [
            "core/io/resource.h",
            "core/io/resource.cpp",
            "core/io/resource_loader.h",
            "core/io/resource_loader.cpp",
            "core/io/resource_saver.h",
            "core/io/resource_format_binary.h",
            "core/io/resource_importer.h",
            "core/io/file_access.h",
            "core/io/dir_access.h",
            "core/io/image.h",
            "core/io/marshalls.h",
        ],
        "analysis_points": [
            "Resource vs UObject/UAsset: 资源基类的设计差异",
            "ResourceLoader vs FStreamableManager: 同步/异步加载机制对比",
            ".tres/.tscn vs .uasset: 文本格式 vs 二进制格式的 trade-off",
            "FileAccess vs FPlatformFileManager: 文件抽象层设计",
            "资源引用: ResourceUID vs FSoftObjectPath",
            "资源缓存: ResourceCache vs FAssetRegistryModule",
            "序列化: Marshalls vs FArchive 的序列化策略对比",
        ],
    },

    # ========================================================================
    # 第二层：场景与节点 (Scene & Node)
    # ========================================================================

    "06_scene_tree_core": {
        "name": "场景树核心",
        "name_en": "Scene Tree Core",
        "description": "SceneTree、Node 基类、Viewport、MainLoop、场景实例化 — 场景管理中枢",
        "ue_equivalent": "UWorld + ULevel + UGameInstance + AGameModeBase",
        "directories": ["scene/main/", "main/"],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "scene/main/scene_tree.h",
            "scene/main/scene_tree.cpp",
            "scene/main/node.h",
            "scene/main/node.cpp",
            "scene/main/viewport.h",
            "scene/main/viewport.cpp",
            "scene/main/window.h",
            "scene/main/canvas_item.h",
            "scene/main/canvas_layer.h",
            "main/main.h",
            "main/main.cpp",
            "main/main_timer_sync.h",
        ],
        "analysis_points": [
            "Node vs AActor: '一切皆节点' vs 'Actor-Component'，这是最大的思维转换",
            "SceneTree vs UWorld: 场景管理的根本差异",
            "节点生命周期: _enter_tree/_ready/_process/_exit_tree vs BeginPlay/Tick/EndPlay",
            "Viewport vs UGameViewportClient: 视口管理对比",
            "PackedScene 实例化 vs SpawnActor: 场景/Actor 创建机制",
            "MainLoop vs FEngineLoop: 主循环设计对比",
            "帧同步: main_timer_sync vs FApp::Tick 的固定/可变步长处理",
            "节点组(Group) vs GameplayTag: 节点分类机制对比",
            "_notification vs UObject::ProcessEvent: 通知/事件分发机制",
        ],
    },

    "07_scene_2d": {
        "name": "2D 场景节点",
        "name_en": "2D Scene Nodes",
        "description": "Node2D、Sprite2D、Camera2D、TileMap、粒子、光照等 2D 节点",
        "ue_equivalent": "UE Paper2D + UMG Widget 中的 2D 渲染部分",
        "directories": ["scene/2d/"],
        "exclude_patterns": ["scene/2d/physics/", "scene/2d/navigation/"],
        "priority": 2,
        "key_files": [
            "scene/2d/node_2d.h",
            "scene/2d/sprite_2d.h",
            "scene/2d/camera_2d.h",
            "scene/2d/tile_map.h",
            "scene/2d/tile_map_layer.h",
            "scene/2d/animated_sprite_2d.h",
            "scene/2d/gpu_particles_2d.h",
            "scene/2d/light_2d.h",
        ],
        "analysis_points": [
            "Node2D vs Paper2D: Godot 原生 2D vs UE 的 2D 插件方案",
            "TileMap vs UTileMapComponent: 瓦片地图实现对比",
            "Camera2D vs 2D 视口: Godot 的 2D 相机 vs UE 的正交投影",
            "CanvasItem 绘制管线: draw_* API vs Slate/UMG 渲染",
        ],
    },

    "08_scene_3d": {
        "name": "3D 场景节点",
        "name_en": "3D Scene Nodes",
        "description": "Node3D、MeshInstance3D、Camera3D、Light3D、骨骼、IK 等 3D 节点",
        "ue_equivalent": "AActor + USceneComponent + UStaticMeshComponent + USkeletalMeshComponent",
        "directories": ["scene/3d/"],
        "exclude_patterns": ["scene/3d/physics/", "scene/3d/navigation/", "scene/3d/xr/"],
        "priority": 2,
        "key_files": [
            "scene/3d/node_3d.h",
            "scene/3d/visual_instance_3d.h",
            "scene/3d/mesh_instance_3d.h",
            "scene/3d/camera_3d.h",
            "scene/3d/light_3d.h",
            "scene/3d/skeleton_3d.h",
            "scene/3d/skeleton_modifier_3d.h",
            "scene/3d/world_environment.h",
            "scene/3d/lightmap_gi.h",
            "scene/3d/voxel_gi.h",
        ],
        "analysis_points": [
            "Node3D vs USceneComponent: 3D 变换节点的继承体系对比",
            "MeshInstance3D vs UStaticMeshComponent: 网格渲染节点对比",
            "Skeleton3D vs USkeleton: 骨骼系统设计差异",
            "SkeletonModifier3D/IK vs AnimInstance: 骨骼修改器 vs 动画蓝图",
            "Light3D vs ULightComponent: 光源类型和阴影策略对比",
            "LightmapGI/VoxelGI vs Lightmass/Lumen: 全局光照方案对比",
        ],
    },

    "09_gui_system": {
        "name": "GUI/UI 系统",
        "name_en": "GUI / UI System",
        "description": "Control 节点体系、布局容器、Theme 主题、RichTextLabel、各种 UI 控件",
        "ue_equivalent": "UE UMG (Unreal Motion Graphics) + Slate 框架",
        "directories": ["scene/gui/", "scene/theme/"],
        "priority": 2,
        "key_files": [
            "scene/gui/control.h",
            "scene/gui/control.cpp",
            "scene/gui/container.h",
            "scene/gui/box_container.h",
            "scene/gui/label.h",
            "scene/gui/button.h",
            "scene/gui/line_edit.h",
            "scene/gui/text_edit.h",
            "scene/gui/rich_text_label.h",
            "scene/gui/tree.h",
            "scene/gui/scroll_container.h",
            "scene/theme/theme_db.h",
        ],
        "analysis_points": [
            "Control vs UWidget: UI 基类的设计差异",
            "锚点/边距布局 vs UMG Slot/Anchor: 布局系统对比",
            "Container 自动布局 vs UMG Panel: 容器布局策略",
            "Theme vs UMG Style: 主题/样式系统对比",
            "Control 焦点系统 vs UMG Navigation: UI 导航机制",
            "信号驱动 vs 事件委托: UI 事件处理模式差异",
        ],
    },

    # ========================================================================
    # 第三层：服务器架构 (Server Architecture)
    # ========================================================================

    "10_rendering_server": {
        "name": "渲染服务器",
        "name_en": "Rendering Server",
        "description": "RenderingServer API、RenderingDevice、场景渲染、Canvas 渲染、Shader 编译",
        "ue_equivalent": "UE RHI + FSceneRenderer + FCanvasRenderer",
        "directories": ["servers/rendering/"],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "servers/rendering/rendering_server.h",
            "servers/rendering/rendering_server_default.h",
            "servers/rendering/rendering_device.h",
            "servers/rendering/rendering_device_commons.h",
            "servers/rendering/rendering_device_driver.h",
            "servers/rendering/rendering_method.h",
            "servers/rendering/renderer_scene_cull.h",
            "servers/rendering/renderer_canvas_cull.h",
            "servers/rendering/renderer_viewport.h",
            "servers/rendering/shader_language.h",
            "servers/rendering/shader_compiler.h",
        ],
        "analysis_points": [
            "Server 架构: 为什么 Godot 用 Server 模式隔离渲染？UE 没有对应概念",
            "RenderingServer vs FSceneRenderer: 渲染 API 抽象层级对比",
            "RenderingDevice vs RHI: 图形 API 抽象层对比",
            "Forward+ / Mobile / Compatibility 三管线 vs UE Deferred/Forward/Mobile",
            "Shader Language vs HLSL/USF: 着色器语言和编译管线对比",
            "RendererSceneCull vs FSceneRenderer::Render: 场景剔除和渲染流程",
            "RendererViewport vs FSceneViewport: 视口渲染管理",
            "Canvas 渲染 vs Slate/UMG 渲染: 2D 渲染管线对比",
        ],
    },

    "11_graphics_drivers": {
        "name": "图形驱动层",
        "name_en": "Graphics Drivers",
        "description": "Vulkan/D3D12/Metal/OpenGL 驱动实现、EGL、GL Context",
        "ue_equivalent": "UE RHI 实现层 (VulkanRHI, D3D12RHI, MetalRHI)",
        "directories": ["drivers/"],
        "priority": 3,
        "key_files": [
            "drivers/vulkan/rendering_device_driver_vulkan.h",
            "drivers/d3d12/rendering_device_driver_d3d12.h",
            "drivers/metal/rendering_device_driver_metal.h",
            "drivers/gles3/rasterizer_gles3.h",
            "drivers/gles3/storage/mesh_storage.h",
        ],
        "analysis_points": [
            "Vulkan 驱动 vs VulkanRHI: 封装粒度和抽象层级对比",
            "GLES3 兼容层: Godot 保留 OpenGL 的策略 vs UE 放弃 OpenGL",
            "Metal 驱动 vs MetalRHI: Apple 平台图形支持对比",
            "RenderingDeviceDriver 接口 vs RHI 接口: 驱动抽象设计对比",
        ],
    },

    "12_physics_2d": {
        "name": "2D 物理引擎",
        "name_en": "2D Physics Engine",
        "description": "PhysicsServer2D 接口 + GodotPhysics2D 实现 + 2D 物理节点",
        "ue_equivalent": "UE Chaos 2D / PhysX 2D 子系统",
        "directories": [
            "servers/physics_2d/",
            "scene/2d/physics/",
            "modules/godot_physics_2d/",
        ],
        "priority": 3,
        "key_files": [
            "servers/physics_2d/physics_server_2d.h",
            "scene/2d/physics/rigid_body_2d.h",
            "scene/2d/physics/character_body_2d.h",
            "scene/2d/physics/collision_shape_2d.h",
            "scene/2d/physics/area_2d.h",
        ],
        "analysis_points": [
            "PhysicsServer2D vs FPhysicsInterface: 物理服务器抽象 vs 直接调用",
            "CharacterBody2D vs ACharacter: 角色物理控制器对比",
            "RigidBody2D vs UPrimitiveComponent(Simulate): 刚体模拟对比",
            "Area2D vs UTriggerComponent: 触发区域对比",
        ],
    },

    "13_physics_3d": {
        "name": "3D 物理引擎",
        "name_en": "3D Physics Engine",
        "description": "PhysicsServer3D 接口 + GodotPhysics3D/Jolt 实现 + 3D 物理节点",
        "ue_equivalent": "UE Chaos Physics / PhysX 集成",
        "directories": [
            "servers/physics_3d/",
            "scene/3d/physics/",
            "modules/godot_physics_3d/",
            "modules/jolt_physics/",
        ],
        "priority": 2,
        "key_files": [
            "servers/physics_3d/physics_server_3d.h",
            "scene/3d/physics/rigid_body_3d.h",
            "scene/3d/physics/character_body_3d.h",
            "scene/3d/physics/collision_shape_3d.h",
            "scene/3d/physics/area_3d.h",
            "scene/3d/physics/vehicle_body_3d.h",
        ],
        "analysis_points": [
            "PhysicsServer3D vs FPhysScene: 物理世界抽象对比",
            "GodotPhysics vs Jolt vs Chaos vs PhysX: 物理后端选择策略",
            "CharacterBody3D vs ACharacter+CMC: 角色移动控制器对比",
            "物理材质 vs PhysicalMaterial: 摩擦/弹性参数系统",
            "射线检测: PhysicsRayQueryParameters3D vs FCollisionQueryParams",
        ],
    },

    "14_audio_system": {
        "name": "音频系统",
        "name_en": "Audio System",
        "description": "AudioServer、音频总线(Bus)、音频流、音效、空间音效",
        "ue_equivalent": "UE AudioEngine + USoundWave + USoundCue + AudioMixer",
        "directories": ["servers/audio/", "scene/audio/"],
        "priority": 3,
        "key_files": [
            "servers/audio/audio_server.h",
            "servers/audio/audio_stream.h",
            "servers/audio/effects/audio_effect_reverb.h",
            "scene/audio/audio_stream_player.h",
        ],
        "analysis_points": [
            "AudioServer Bus 架构 vs UE AudioMixer: 音频混合管线对比",
            "AudioStreamPlayer vs UAudioComponent: 音频播放节点对比",
            "空间音效: AudioStreamPlayer3D vs Attenuation Settings",
            "音频效果链 vs USoundEffectPreset: 音效处理对比",
        ],
    },

    # ========================================================================
    # 第四层：脚本与扩展 (Script & Extension)
    # ========================================================================

    "15_gdextension": {
        "name": "GDExtension 扩展系统",
        "name_en": "GDExtension System",
        "description": "GDExtension 原生扩展接口、动态库加载、C ABI 绑定",
        "ue_equivalent": "UE Plugin/Module 系统 + IModuleInterface",
        "directories": ["core/extension/"],
        "priority": 2,
        "key_files": [
            "core/extension/gdextension.h",
            "core/extension/gdextension.cpp",
            "core/extension/gdextension_interface.cpp",
            "core/extension/gdextension_manager.h",
            "core/extension/gdextension_library_loader.h",
        ],
        "analysis_points": [
            "GDExtension vs UE Plugin: 原生扩展机制对比",
            "C ABI 接口 vs UE Module C++ 接口: 为什么 Godot 选择 C ABI",
            "GDExtensionManager vs FModuleManager: 扩展生命周期管理",
            "godot-cpp 绑定 vs UE C++ API: 开发体验对比",
        ],
    },

    "16_gdscript": {
        "name": "GDScript 脚本系统",
        "name_en": "GDScript System",
        "description": "GDScript 词法分析、语法分析、编译器、字节码生成、虚拟机",
        "ue_equivalent": "UE Blueprint VM + Kismet 编译器 + UFunction 执行",
        "directories": ["modules/gdscript/"],
        "priority": 1,
        "highlight": True,
        "key_files": [
            "modules/gdscript/gdscript.h",
            "modules/gdscript/gdscript_tokenizer.h",
            "modules/gdscript/gdscript_parser.h",
            "modules/gdscript/gdscript_analyzer.h",
            "modules/gdscript/gdscript_compiler.h",
            "modules/gdscript/gdscript_byte_codegen.h",
            "modules/gdscript/gdscript_function.h",
            "modules/gdscript/gdscript_vm.cpp",
            "modules/gdscript/gdscript_cache.h",
        ],
        "analysis_points": [
            "GDScript 编译管线: Tokenizer→Parser→Analyzer→Compiler→ByteCode 全流程",
            "GDScript VM vs Blueprint VM: 字节码指令集和执行效率对比",
            "GDScript 类型推断 vs Blueprint 强类型: 类型系统差异",
            "GDScript 热重载 vs UE Live Coding: 开发迭代体验对比",
            "GDScript 协程(await) vs UE Latent Action: 异步编程模型",
            "为什么自研脚本语言: GDScript vs Lua/Python/C# 的选型分析",
        ],
    },

    # ========================================================================
    # 第五层：动画与导航 (Animation & Navigation)
    # ========================================================================

    "17_animation_system": {
        "name": "动画系统",
        "name_en": "Animation System",
        "description": "AnimationPlayer、AnimationTree、AnimationMixer、状态机、BlendSpace",
        "ue_equivalent": "UE AnimInstance + AnimBlueprint + AnimMontage + BlendSpace",
        "directories": ["scene/animation/"],
        "priority": 2,
        "key_files": [
            "scene/animation/animation_player.h",
            "scene/animation/animation_tree.h",
            "scene/animation/animation_mixer.h",
            "scene/animation/animation_node_state_machine.h",
            "scene/animation/animation_blend_tree.h",
            "scene/animation/animation_blend_space_2d.h",
            "scene/animation/tween.h",
        ],
        "analysis_points": [
            "AnimationPlayer vs UAnimSequence: 关键帧动画播放对比",
            "AnimationTree vs AnimBlueprint: 动画混合树 vs 动画蓝图",
            "AnimationNodeStateMachine vs AnimStateMachine: 状态机对比",
            "BlendSpace2D vs UBlendSpace: 混合空间实现对比",
            "Tween vs UE Timeline: 程序化动画/插值对比",
            "AnimationMixer: Godot 4.x 新增的动画混合基类设计",
        ],
    },

    "18_input_system": {
        "name": "输入系统",
        "name_en": "Input System",
        "description": "InputEvent 事件体系、InputMap 动作映射、键盘/鼠标/手柄/触摸",
        "ue_equivalent": "UE EnhancedInput + UPlayerInput + InputAction/InputMapping",
        "directories": ["core/input/"],
        "priority": 3,
        "key_files": [
            "core/input/input.h",
            "core/input/input_event.h",
            "core/input/input_map.h",
            "core/input/input_enums.h",
        ],
        "analysis_points": [
            "InputEvent 继承树 vs FInputEvent: 输入事件类型体系对比",
            "InputMap vs EnhancedInput InputAction: 动作映射机制对比",
            "_input/_unhandled_input vs APlayerController::InputComponent: 输入处理链",
            "输入传播: 节点树冒泡 vs UE InputComponent 优先级",
        ],
    },

    "19_navigation_system": {
        "name": "导航系统",
        "name_en": "Navigation System",
        "description": "NavigationServer2D/3D、导航网格、寻路、避障、导航节点",
        "ue_equivalent": "UE NavigationSystem (Recast/Detour) + AIController::MoveTo",
        "directories": [
            "servers/navigation_2d/",
            "servers/navigation_3d/",
            "modules/navigation_2d/",
            "modules/navigation_3d/",
            "scene/2d/navigation/",
            "scene/3d/navigation/",
        ],
        "priority": 3,
        "key_files": [
            "servers/navigation_3d/navigation_server_3d.h",
            "servers/navigation_2d/navigation_server_2d.h",
        ],
        "analysis_points": [
            "NavigationServer vs UNavigationSystemV1: 导航系统架构对比",
            "NavigationMesh vs UNavMeshData: 导航网格生成和使用",
            "NavigationAgent vs AIController MoveTo: 寻路 Agent 对比",
            "避障: NavigationObstacle vs RVO/Detour Crowd",
        ],
    },

    # ========================================================================
    # 第六层：编辑器与工具 (Editor & Tools)
    # ========================================================================

    "20_editor_framework": {
        "name": "编辑器框架",
        "name_en": "Editor Framework",
        "description": "EditorNode 主框架、EditorPlugin 插件、Inspector、Dock、编辑器 GUI",
        "ue_equivalent": "UE Editor Module (FEditorModeTools, IModuleInterface, DetailCustomization)",
        "directories": ["editor/"],
        "exclude_patterns": ["editor/import/", "editor/translations/", "editor/icons/"],
        "priority": 3,
        "key_files": [
            "editor/editor_node.h",
            "editor/editor_interface.h",
            "editor/editor_data.h",
            "editor/plugins/node_3d_editor_plugin.h",
            "editor/inspector/editor_inspector.h",
            "editor/gui/editor_file_dialog.h",
        ],
        "analysis_points": [
            "EditorNode vs FLevelEditorModule: 编辑器主框架对比",
            "EditorPlugin vs IModuleInterface: 编辑器插件机制对比",
            "Inspector vs DetailsPanel: 属性面板实现对比",
            "编辑器 GUI: Godot 用自己的 Control 节点 vs UE 用 Slate",
            "@tool 脚本 vs Editor Utility Widget: 编辑器扩展方式",
        ],
    },

    "21_import_pipeline": {
        "name": "导入管线",
        "name_en": "Import Pipeline",
        "description": "资源导入器：纹理/模型/音频/字体/glTF/FBX 导入流程",
        "ue_equivalent": "UE UFactory + FAssetImportData + Interchange Framework",
        "directories": ["editor/import/", "modules/gltf/", "modules/fbx/"],
        "priority": 3,
        "key_files": [
            "core/io/resource_importer.h",
            "editor/import/resource_importer_scene.h",
            "editor/import/resource_importer_texture.h",
        ],
        "analysis_points": [
            "ResourceImporter vs UFactory: 导入器注册和执行机制对比",
            "glTF/FBX 导入 vs Interchange: 3D 模型导入管线对比",
            ".import 文件 vs .uasset: 导入缓存策略对比",
        ],
    },

    # ========================================================================
    # 第七层：平台与网络 (Platform & Networking)
    # ========================================================================

    "22_display_server": {
        "name": "显示服务器",
        "name_en": "Display Server",
        "description": "DisplayServer 窗口管理、原生菜单、剪贴板、系统对话框",
        "ue_equivalent": "UE FGenericApplication + FGenericWindow + FSlateApplication",
        "directories": ["servers/display/"],
        "priority": 3,
        "key_files": [
            "servers/display/display_server.h",
            "servers/display/native_menu.h",
        ],
        "analysis_points": [
            "DisplayServer vs FGenericApplication: 窗口管理抽象对比",
            "多窗口支持: Godot 原生多窗口 vs UE SWindow",
            "系统集成: 剪贴板/对话框/IME 等平台功能",
        ],
    },

    "23_platform_layer": {
        "name": "平台抽象层",
        "name_en": "Platform Abstraction Layer",
        "description": "各平台入口和适配：Windows/macOS/Linux/Android/iOS/Web",
        "ue_equivalent": "UE GenericPlatform → WindowsPlatform/AndroidPlatform 等",
        "directories": ["platform/"],
        "priority": 4,
        "key_files": [
            "platform/windows/os_windows.h",
            "platform/linuxbsd/os_linuxbsd.h",
            "platform/android/os_android.h",
            "platform/web/os_web.h",
        ],
        "analysis_points": [
            "平台入口: platform/*/godot_*.cpp vs Launch 模块",
            "OS 子类 vs FGenericPlatformMisc 子类: 平台适配方式对比",
            "Web 平台: Godot 原生 Web 导出 vs UE Pixel Streaming",
            "Android/iOS: 平台集成和构建流程对比",
        ],
    },

    "24_networking": {
        "name": "网络与多人",
        "name_en": "Networking & Multiplayer",
        "description": "High-level Multiplayer API、RPC、状态同步、ENet、WebSocket、WebRTC",
        "ue_equivalent": "UE Replication + RPC + NetDriver + OnlineSubsystem",
        "directories": [
            "scene/multiplayer/",
            "modules/multiplayer/",
            "modules/enet/",
            "modules/websocket/",
            "modules/webrtc/",
        ],
        "priority": 3,
        "key_files": [
            "scene/multiplayer/multiplayer_api.h",
            "scene/multiplayer/multiplayer_peer.h",
            "scene/multiplayer/multiplayer_spawner.h",
            "scene/multiplayer/multiplayer_synchronizer.h",
        ],
        "analysis_points": [
            "MultiplayerAPI vs UE Replication: 高层多人 API 对比",
            "RPC 机制: @rpc 注解 vs UFUNCTION(Server/Client/NetMulticast)",
            "MultiplayerSynchronizer vs UE Property Replication: 状态同步对比",
            "MultiplayerSpawner vs SpawnActor Replication: 网络对象生成",
            "ENet/WebSocket vs UE NetDriver: 传输层对比",
        ],
    },

    # ========================================================================
    # 第八层：专项系统 (Specialized Systems)
    # ========================================================================

    "25_text_server": {
        "name": "文本渲染服务器",
        "name_en": "Text Server",
        "description": "TextServer 文本排版、字体管理、BiDi、HarfBuzz 整形",
        "ue_equivalent": "UE FreeType + ICU + Slate Font 渲染",
        "directories": [
            "servers/text/",
            "modules/text_server_adv/",
            "modules/text_server_fb/",
            "modules/freetype/",
        ],
        "priority": 4,
        "key_files": [
            "servers/text/text_server.h",
        ],
        "analysis_points": [
            "TextServer vs Slate Font: 文本渲染抽象层对比",
            "HarfBuzz 整形 vs ICU: 复杂文本排版支持",
            "多语言/BiDi 支持: Godot 的国际化文本能力",
        ],
    },

    "26_xr_system": {
        "name": "XR/VR 系统",
        "name_en": "XR / VR System",
        "description": "XRServer、XRInterface、OpenXR 集成、VR 节点",
        "ue_equivalent": "UE XR Framework (IXRTrackingSystem, UHeadMountedDisplay)",
        "directories": [
            "servers/xr/",
            "scene/3d/xr/",
            "modules/openxr/",
            "modules/mobile_vr/",
        ],
        "priority": 4,
        "key_files": [
            "servers/xr/xr_server.h",
            "servers/xr/xr_interface.h",
        ],
        "analysis_points": [
            "XRServer vs IXRTrackingSystem: XR 抽象层对比",
            "OpenXR 集成: Godot vs UE 的 OpenXR 支持方式",
        ],
    },

    "27_scene_resources": {
        "name": "场景资源类型",
        "name_en": "Scene Resource Types",
        "description": "Mesh/Material/Shader/Texture/Environment 等场景资源类型定义",
        "ue_equivalent": "UE UStaticMesh/UMaterialInterface/UTexture/UShaderMap",
        "directories": ["scene/resources/"],
        "priority": 2,
        "key_files": [
            "scene/resources/mesh.h",
            "scene/resources/material.h",
            "scene/resources/shader.h",
            "scene/resources/texture.h",
            "scene/resources/environment.h",
            "scene/resources/packed_scene.h",
            "scene/resources/font.h",
        ],
        "analysis_points": [
            "Mesh vs UStaticMesh: 网格资源的数据结构对比",
            "Material/ShaderMaterial vs UMaterialInterface: 材质系统对比",
            "PackedScene vs ULevel/UBlueprint: 场景打包和实例化对比",
            "Shader vs UShadowMap/MaterialExpression: 着色器资源对比",
            "Environment vs UPostProcessVolume: 环境/后处理设置对比",
        ],
    },

    "28_optional_modules": {
        "name": "可选功能模块",
        "name_en": "Optional Modules",
        "description": "CSG、GridMap、Noise、Regex、图像格式编解码等可选模块",
        "ue_equivalent": "UE Plugin / Feature Pack 体系",
        "directories": ["modules/"],
        "exclude_patterns": [
            "modules/gdscript/",
            "modules/navigation_2d/",
            "modules/navigation_3d/",
            "modules/godot_physics_2d/",
            "modules/godot_physics_3d/",
            "modules/jolt_physics/",
            "modules/multiplayer/",
            "modules/enet/",
            "modules/websocket/",
            "modules/webrtc/",
            "modules/openxr/",
            "modules/mobile_vr/",
            "modules/text_server_adv/",
            "modules/text_server_fb/",
            "modules/freetype/",
            "modules/gltf/",
            "modules/fbx/",
            "modules/mono/",
        ],
        "priority": 5,
        "key_files": [
            "modules/csg/csg_shape.h",
            "modules/gridmap/grid_map.h",
            "modules/noise/noise.h",
            "modules/regex/regex.h",
        ],
        "analysis_points": [
            "CSG vs UE BSP/ProBuilder: 构造实体几何对比",
            "GridMap vs UE GridMap/Voxel: 3D 网格地图对比",
            "模块注册机制: config.py + register_types vs UE .uplugin",
            "Mono/C# 集成: Godot C# vs UE C# (via UnrealCLR)",
        ],
    },
}

# 分析时每个文件的最大 token 数（超出则截断）
MAX_FILE_TOKENS = 8000

# LLM 分析的批次大小
ANALYSIS_BATCH_SIZE = 5

# 输出目录
OUTPUT_DIR = "output"

# 源码根目录（运行时通过 --source 参数指定）
SOURCE_ROOT = ""

# 目标读者背景
TARGET_READER_BACKGROUND = """
目标读者是有 Unreal Engine 4 开发经验的游戏开发者。
他们熟悉以下 UE 概念：
- UObject 反射系统和 GC
- AActor / UActorComponent 世界构建模式
- TSharedPtr / TWeakObjectPtr 智能指针
- FProperty 序列化和反射
- Blueprint / C++ 混合开发
- Chaos Physics / PhysX
- 渲染线程和 RHI 抽象
- GameplayAbilitySystem / EnhancedInput
- AnimBlueprint / AnimMontage / BlendSpace
- UMG / Slate UI 框架
- Replication / RPC 网络同步

对比时请多用 UE 概念类比帮助理解。
"""
