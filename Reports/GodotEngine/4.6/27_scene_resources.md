# 27 - 场景资源类型 (Scene Resource Types)

> **核心结论：Godot 将 Mesh/Material/Shader/Texture/Environment 统一为轻量级 Resource 对象，通过 RID 代理模式委托给 RenderingServer；UE 则将它们作为重量级 UObject 资产，内嵌复杂的 LOD/Streaming/Cook 管线——Godot 追求简洁可组合，UE 追求工业级可控性。**

---

## 目录

- [第 1 章：模块概览 — "UE 程序员 30 秒速览"](#第-1-章模块概览--ue-程序员-30-秒速览)
- [第 2 章：架构对比 — "同一个问题，两种解法"](#第-2-章架构对比--同一个问题两种解法)
- [第 3 章：核心实现对比 — "代码层面的差异"](#第-3-章核心实现对比--代码层面的差异)
- [第 4 章：UE → Godot 迁移指南](#第-4-章ue--godot-迁移指南)
- [第 5 章：性能对比](#第-5-章性能对比)
- [第 6 章：总结 — "一句话记住"](#第-6-章总结--一句话记住)

---

## 第 1 章：模块概览 — "UE 程序员 30 秒速览"

### 1.1 一句话定位

Godot 的 `scene/resources/` 目录定义了所有场景级资源类型——Mesh、Material、Shader、Texture、Environment、PackedScene 等。它们全部继承自 `Resource`（对标 UE 的 `UObject` 资产），但设计哲学截然不同：**Godot 的资源是轻量级数据容器，真正的 GPU 资源由 RenderingServer 通过 RID 句柄管理**；而 UE 的资源是自包含的重量级对象，内嵌序列化、流送、Cook 等完整管线。

### 1.2 核心类/结构体列表

| # | Godot 类 | 源码路径 | 简要说明 | UE 对应物 |
|---|---------|---------|---------|----------|
| 1 | `Mesh` | `scene/resources/mesh.h` | 网格资源基类，定义 surface/blend shape 接口 | `UStaticMesh` / `USkeletalMesh` |
| 2 | `ArrayMesh` | `scene/resources/mesh.h` | 可编程网格，支持动态添加 surface | `FStaticMeshRenderData` + `FMeshDescription` |
| 3 | `Material` | `scene/resources/material.h` | 材质基类，持有 RID + next_pass 链 | `UMaterialInterface` |
| 4 | `ShaderMaterial` | `scene/resources/material.h` | 自定义 Shader 材质 | `UMaterialInstanceDynamic` (自定义 shader) |
| 5 | `BaseMaterial3D` | `scene/resources/material.h` | PBR 标准材质基类（含 MaterialKey 共享 shader） | `UMaterial` (PBR 主材质) |
| 6 | `StandardMaterial3D` | `scene/resources/material.h` | 标准 PBR 材质（非 ORM） | `UMaterialInstanceConstant` |
| 7 | `Shader` | `scene/resources/shader.h` | 着色器资源，持有 GLSL-like 代码 | `UMaterialExpression` 图 + HLSL |
| 8 | `Texture2D` | `scene/resources/texture.h` | 2D 纹理基类 | `UTexture2D` |
| 9 | `ImageTexture` | `scene/resources/image_texture.h` | 从 Image 创建的运行时纹理 | `UTexture2D::CreateTransient()` |
| 10 | `CompressedTexture2D` | `scene/resources/compressed_texture.h` | 磁盘压缩纹理（.ctex） | `UTexture2D`（cooked 资产） |
| 11 | `Environment` | `scene/resources/environment.h` | 环境/后处理设置资源 | `APostProcessVolume` + `FPostProcessSettings` |
| 12 | `PackedScene` | `scene/resources/packed_scene.h` | 场景打包/实例化资源 | `ULevel` / `UBlueprint` / `UWorld` |
| 13 | `SceneState` | `scene/resources/packed_scene.h` | PackedScene 的内部序列化状态 | `FLevelScriptBlueprint` + 序列化数据 |
| 14 | `Sky` | `scene/resources/sky.h` | 天空资源（含 radiance 大小和材质） | `ASkyAtmosphere` + `ASkyLight` |
| 15 | `Font` / `FontFile` | `scene/resources/font.h` | 字体资源（支持动态/位图字体） | `UFont` / Slate `FSlateFontInfo` |

### 1.3 Godot vs UE 概念速查表

| 概念 | Godot | UE | 关键差异 |
|------|-------|-----|---------|
| 网格资源 | `Mesh` → `ArrayMesh` | `UStaticMesh` | Godot 无内置 LOD 管线，UE 有完整 LOD 链 |
| 材质基类 | `Material` (Resource) | `UMaterialInterface` (UObject) | Godot 材质是纯数据，UE 材质含编译管线 |
| PBR 材质 | `StandardMaterial3D` | `UMaterial` + Material Editor | Godot 用 MaterialKey 共享 shader 变体 |
| 自定义着色器 | `ShaderMaterial` + `.gdshader` | Material Graph + HLSL | Godot 用文本 shader，UE 用节点图 |
| 纹理 | `Texture2D` → `ImageTexture` / `CompressedTexture2D` | `UTexture2D` | Godot 纹理是薄包装，UE 纹理含 streaming/mip 管线 |
| 后处理/环境 | `Environment` (Resource) | `APostProcessVolume` (Actor) | Godot 是资源对象，UE 是场景中的 Volume Actor |
| 场景打包 | `PackedScene` (.tscn/.scn) | `ULevel` (.umap) / `UBlueprint` | Godot 场景=节点树序列化，UE 关卡=Actor 集合 |
| 天空 | `Sky` + `ShaderMaterial` | `ASkyAtmosphere` + `ASkyLight` | Godot 天空是 Resource，UE 是 Actor 组合 |
| 着色器语言 | Godot Shading Language (类 GLSL) | HLSL + Material Expression | Godot 更接近 GLSL，UE 抽象层更厚 |
| GPU 资源管理 | RID 句柄 → RenderingServer | FRHIResource → RHI 抽象层 | Godot 单一 Server 模式，UE 多线程 RHI |

---

## 第 2 章：架构对比 — "同一个问题，两种解法"

### 2.1 Godot 的架构设计

Godot 的场景资源体系建立在 **Resource + RenderingServer** 的双层架构之上。所有场景资源（Mesh、Material、Shader、Texture、Environment）都继承自 `Resource`，而 `Resource` 继承自 `RefCounted`，使用引用计数进行生命周期管理。每个资源对象内部持有一个 `RID`（Resource ID），这是一个指向 RenderingServer 内部真实 GPU 资源的不透明句柄。

```mermaid
classDiagram
    class Resource {
        +String path
        +get_rid() RID
        +duplicate() Resource
    }
    
    class Mesh {
        -Ref~TriangleMesh~ triangle_mesh
        +get_surface_count() int
        +surface_get_arrays() Array
        +surface_get_material() Material
    }
    
    class ArrayMesh {
        -Vector~Surface~ surfaces
        -RID mesh
        +add_surface_from_arrays()
        +surface_remove()
    }
    
    class Material {
        -RID material
        -Ref~Material~ next_pass
        -int render_priority
        +get_shader_rid() RID
    }
    
    class ShaderMaterial {
        -Ref~Shader~ shader
        -HashMap params
        +set_shader_parameter()
    }
    
    class BaseMaterial3D {
        -MaterialKey current_key
        -static HashMap shader_map
        +set_albedo()
        +set_metallic()
    }
    
    class Shader {
        -RID shader_rid
        -String code
        -Mode mode
        +set_code()
        +get_mode() Mode
    }
    
    class Texture {
    }
    
    class Texture2D {
        +get_width() int
        +get_height() int
        +draw()
    }
    
    class ImageTexture {
        -RID texture
        -Image::Format format
        +set_image()
        +update()
    }
    
    class CompressedTexture2D {
        -String path_to_file
        -RID texture
        +load()
    }
    
    class Environment {
        -RID environment
        -BGMode bg_mode
        -Ref~Sky~ bg_sky
        +set_background()
        +set_fog_enabled()
        +set_glow_enabled()
    }
    
    class PackedScene {
        -Ref~SceneState~ state
        +pack() Error
        +instantiate() Node
    }
    
    class SceneState {
        -Vector~StringName~ names
        -Vector~Variant~ variants
        -Vector~NodeData~ nodes
        -Vector~ConnectionData~ connections
        +pack() Error
        +instantiate() Node
    }
    
    Resource <|-- Mesh
    Resource <|-- Material
    Resource <|-- Shader
    Resource <|-- Texture
    Resource <|-- Environment
    Resource <|-- PackedScene
    
    Mesh <|-- ArrayMesh
    Material <|-- ShaderMaterial
    Material <|-- BaseMaterial3D
    Texture <|-- Texture2D
    Texture2D <|-- ImageTexture
    Texture2D <|-- CompressedTexture2D
    
    ShaderMaterial --> Shader : uses
    BaseMaterial3D --> Shader : generates
    Material --> Material : next_pass
    ArrayMesh --> Material : per-surface
    Environment --> "Sky" : bg_sky
    PackedScene --> SceneState : state
```

**核心设计模式：RID 代理（Proxy）模式**

Godot 的每个场景资源都是一个"代理对象"。以 `Material` 为例（`scene/resources/material.h`）：

```cpp
class Material : public Resource {
    mutable RID material;  // 指向 RenderingServer 内部的真实材质
    Ref<Material> next_pass;  // 材质链（多 pass 渲染）
    int render_priority;
    
    _FORCE_INLINE_ void _set_material(RID p_material) const { material = p_material; }
    _FORCE_INLINE_ RID _get_material() const { return material; }
};
```

场景层的 `Material` 对象只是一个薄包装，真正的 shader 编译、uniform 绑定、渲染状态管理全部在 `RenderingServer` 内部完成。这种设计使得场景层代码可以在主线程安全运行，而渲染操作被隔离到服务器线程。

### 2.2 UE 对应模块的架构设计

UE 的资源体系建立在 **UObject 反射系统** 之上。所有渲染资源（`UStaticMesh`、`UMaterialInterface`、`UTexture`）都是 `UObject` 的子类，天然具备序列化、GC、反射、编辑器集成等能力。

UE 的架构是"自包含"的——`UStaticMesh` 不仅包含网格数据，还内嵌了 LOD 管线、碰撞体、Nanite 数据、距离场数据、流送配置等。`UMaterialInterface` 不仅是材质参数容器，还包含 shader 编译管线、材质表达式图、平台特化编译等。

```
UObject
├── UStreamableRenderAsset
│   └── UStaticMesh          // 含 RenderData, LOD, BodySetup, DistanceField...
├── UMaterialInterface       // 含 FMaterialRenderProxy, FMaterialResource...
│   ├── UMaterial            // 材质图编辑器的根节点
│   └── UMaterialInstance    // 材质实例（参数覆盖）
│       └── UMaterialInstanceDynamic  // 运行时动态材质
├── UTexture
│   ├── UTexture2D           // 含 Mip 链, Streaming, Platform 数据
│   └── UTextureCube
└── APostProcessVolume       // 后处理是 Actor，不是 Resource
```

### 2.3 关键架构差异分析

#### 差异 1：资源的"重量级"程度 — 薄代理 vs 自包含巨石

**Godot 的设计哲学**是将场景资源做成"薄代理"。以 `Mesh` 为例（`scene/resources/mesh.h`），基类 `Mesh` 只有约 200 行代码，定义了 surface 访问的虚函数接口。`ArrayMesh` 的 `Surface` 结构体极其精简：

```cpp
struct Surface {
    uint64_t format = 0;
    int array_length = 0;
    int index_array_length = 0;
    PrimitiveType primitive = PrimitiveType::PRIMITIVE_MAX;
    String name;
    AABB aabb;
    Ref<Material> material;
    bool is_2d = false;
};
```

**UE 的设计哲学**是将 `UStaticMesh` 做成一个"自包含的工业级资产"（`Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h`，1492 行）。它包含：
- `FStaticMeshRenderData`（多 LOD 渲染数据）
- `FStaticMeshOccluderData`（遮挡剔除数据）
- `UBodySetup`（物理碰撞体）
- LOD 组、流送配置、距离场、Nanite 数据
- 材质槽映射 `FMeshSectionInfoMap`
- 光照贴图配置

**Trade-off 分析**：Godot 的薄代理模式使得资源创建和修改极其轻量，适合快速原型和中小型项目；但缺少 LOD、流送等工业级功能。UE 的自包含模式提供了完整的生产管线，但每个资产的内存占用和复杂度都远高于 Godot。

#### 差异 2：GPU 资源管理 — RID Server 模式 vs RHI 抽象层

**Godot** 使用 `RenderingServer` 单例作为所有 GPU 资源的唯一管理者。场景层的资源对象通过 `RID` 句柄与服务器通信。这是一种**命令队列模式**——场景层发出命令，RenderingServer 在渲染线程执行。

```cpp
// Godot: Material 通过 RID 与 RenderingServer 交互
class Material : public Resource {
    mutable RID material;  // 不透明句柄
    virtual RID get_rid() const override;
};
```

**UE** 使用 **RHI（Render Hardware Interface）** 抽象层。每个渲染资源有对应的 `FRHIResource` 子类（如 `FRHITexture2D`、`FRHIBuffer`），通过 `FMaterialRenderProxy` 等代理对象在渲染线程访问。UE 的渲染线程模型更复杂，支持多线程命令提交。

**Trade-off 分析**：Godot 的 RID 模式简单统一，但所有 GPU 操作都要经过 RenderingServer 这个瓶颈。UE 的 RHI 模式更灵活，支持多线程渲染命令提交，但复杂度也更高。

#### 差异 3：材质系统 — MaterialKey 共享 vs Material Expression 图

**Godot 的 `BaseMaterial3D`** 使用了一个极其巧妙的 **MaterialKey 共享机制**（`scene/resources/material.h`）。所有 PBR 材质参数被编码为一个 `MaterialKey` 位域结构体，相同 Key 的材质共享同一个编译好的 shader：

```cpp
struct MaterialKey {
    uint64_t texture_filter : get_num_bits(TEXTURE_FILTER_MAX - 1);
    uint64_t transparency : get_num_bits(TRANSPARENCY_MAX - 1);
    uint64_t shading_mode : get_num_bits(SHADING_MODE_MAX - 1);
    uint64_t blend_mode : get_num_bits(BLEND_MODE_MAX - 1);
    // ... 更多位域
    uint32_t feature_mask;
    uint32_t flags;
};

static HashMap<MaterialKey, ShaderData, MaterialKey> shader_map;
```

这意味着 Godot 中 100 个使用相同渲染模式的 `StandardMaterial3D`，实际上只编译一个 shader，只是 uniform 参数不同。

**UE 的材质系统**基于 **Material Expression 节点图**。每个 `UMaterial` 是一个完整的 shader 图，通过 `FMaterialCompiler` 编译为平台特定的 shader 代码。`UMaterialInstance` 通过参数覆盖实现变体，但底层 shader 仍然可能因为 Static Switch 等产生大量变体。

**Trade-off 分析**：Godot 的 MaterialKey 方案极大减少了 shader 变体数量，编译速度快，内存占用低；但灵活性有限，无法像 UE 那样通过节点图实现任意复杂的材质逻辑。UE 的节点图方案功能强大，但 shader 变体爆炸是一个持续的工程挑战。

---

## 第 3 章：核心实现对比 — "代码层面的差异"

### 3.1 Mesh vs UStaticMesh：网格资源的数据结构对比

#### Godot 的实现

Godot 的网格体系以 `Mesh` 基类为核心（`scene/resources/mesh.h`），采用 **Surface 抽象**——每个 Mesh 由多个 Surface 组成，每个 Surface 有独立的顶点数据、索引数据和材质。

```cpp
// scene/resources/mesh.h - Mesh 基类的核心接口
class Mesh : public Resource {
public:
    enum ArrayType {
        ARRAY_VERTEX = RenderingServer::ARRAY_VERTEX,
        ARRAY_NORMAL = RenderingServer::ARRAY_NORMAL,
        ARRAY_TANGENT = RenderingServer::ARRAY_TANGENT,
        ARRAY_COLOR = RenderingServer::ARRAY_COLOR,
        ARRAY_TEX_UV = RenderingServer::ARRAY_TEX_UV,
        ARRAY_TEX_UV2 = RenderingServer::ARRAY_TEX_UV2,
        ARRAY_CUSTOM0 ~ ARRAY_CUSTOM3,  // 4 个自定义通道
        ARRAY_BONES, ARRAY_WEIGHTS,
        ARRAY_INDEX,
        ARRAY_MAX
    };
    
    virtual int get_surface_count() const;
    virtual Array surface_get_arrays(int p_surface) const;
    virtual Ref<Material> surface_get_material(int p_idx) const;
};
```

`ArrayMesh` 是最常用的具体实现，通过 `add_surface_from_arrays()` 方法从 Godot 的 `Array` 类型构建网格数据：

```cpp
// ArrayMesh 的 Surface 数据结构
struct Surface {
    uint64_t format = 0;           // 位掩码，标记哪些顶点属性存在
    int array_length = 0;          // 顶点数
    int index_array_length = 0;    // 索引数
    PrimitiveType primitive;       // 图元类型
    String name;
    AABB aabb;
    Ref<Material> material;
    bool is_2d = false;
};
```

关键特点：
1. **数据通过 Array 传递**：顶点位置是 `PackedVector3Array`，法线是 `PackedVector3Array`，UV 是 `PackedVector2Array`，这些被打包在一个 `Array` 中按 `ArrayType` 索引访问。
2. **无内置 LOD**：`Mesh` 基类没有 LOD 概念，LOD 需要通过 `Dictionary surface_get_lods()` 手动管理。
3. **物理形状生成**：`Mesh` 提供 `create_trimesh_shape()` 和 `create_convex_shape()` 方法从网格数据生成碰撞形状，但这是按需生成的，不像 UE 那样内嵌在资产中。

#### UE 的实现

UE 的 `UStaticMesh`（`Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h`，1492 行）是一个重量级资产类：

```cpp
UCLASS(hidecategories=Object, customconstructor, MinimalAPI, BlueprintType, config=Engine)
class UStaticMesh : public UStreamableRenderAsset, 
                    public IInterface_CollisionDataProvider, 
                    public IInterface_AssetUserData
{
    // 渲染数据（含多 LOD）
    TUniquePtr<class FStaticMeshRenderData> RenderData;
    
    // 遮挡剔除数据
    TUniquePtr<class FStaticMeshOccluderData> OccluderData;
    
    // 物理碰撞体（内嵌）
    class UBodySetup* BodySetup;
    
    // 材质槽
    TArray<FStaticMaterial> StaticMaterials;
    
    // LOD 配置
    FName LODGroup;
    FPerPlatformInt MinLOD;
    int32 LODForCollision;
    
    // 光照贴图
    int32 LightMapResolution;
    int32 LightMapCoordinateIndex;
    
    // 距离场
    float DistanceFieldSelfShadowBias;
};
```

`FStaticMeshRenderData` 内部包含 `FStaticMeshLODResources` 数组，每个 LOD 有独立的顶点缓冲、索引缓冲、Section 信息。

#### 差异点评

| 维度 | Godot `ArrayMesh` | UE `UStaticMesh` |
|------|-------------------|-------------------|
| 数据组织 | Surface 数组，每个 Surface 独立 | LOD 数组，每个 LOD 含多个 Section |
| LOD 支持 | 无内置 LOD 管线 | 完整 LOD 链 + 自动 LOD 生成 |
| 碰撞体 | 按需生成，不持久化 | `UBodySetup` 内嵌，Cook 时预计算 |
| 流送 | 无 | `UStreamableRenderAsset` 基类提供 |
| 顶点格式 | `ArrayFormat` 位掩码，运行时灵活 | `FStaticMeshVertexBuffer`，编译时固定 |
| 内存占用 | 极低（薄代理） | 较高（含所有管线数据） |
| 创建方式 | `add_surface_from_arrays()` 运行时构建 | 编辑器导入 + Cook 管线 |

**结论**：Godot 的 Mesh 系统适合快速原型和程序化生成（运行时构建网格非常方便），但缺少 LOD 和流送等大型项目必需的功能。UE 的 Mesh 系统是工业级的，但运行时修改网格数据的成本远高于 Godot。

### 3.2 Material/ShaderMaterial vs UMaterialInterface：材质系统对比

#### Godot 的实现

Godot 的材质体系分为三层：

**第一层：`Material` 基类**（`scene/resources/material.h`）
```cpp
class Material : public Resource {
    mutable RID material;          // RenderingServer 中的材质句柄
    Ref<Material> next_pass;       // 多 Pass 渲染链
    int render_priority;           // 渲染优先级
    
    enum { INIT_STATE_UNINITIALIZED, INIT_STATE_INITIALIZING, INIT_STATE_READY };
};
```

`next_pass` 是 Godot 独有的设计——材质可以形成链表，实现多 Pass 渲染（如先渲染轮廓再渲染本体）。这在 UE 中需要通过 Material Domain 或自定义渲染 Pass 实现。

**第二层：`ShaderMaterial`** — 自定义 Shader 材质
```cpp
class ShaderMaterial : public Material {
    Ref<Shader> shader;
    mutable HashMap<StringName, StringName> remap_cache;
    mutable HashMap<StringName, Variant> param_cache;
    mutable Mutex material_rid_mutex;
};
```

`ShaderMaterial` 直接引用一个 `Shader` 资源，参数通过 `HashMap<StringName, Variant>` 存储。这是一种极其灵活的设计——任何类型的值都可以作为 shader 参数。

**第三层：`BaseMaterial3D`** — PBR 标准材质

`BaseMaterial3D` 是 Godot 最复杂的材质类（约 940 行），它使用 **MaterialKey 共享 shader** 的策略：

```cpp
// 所有影响 shader 变体的参数被编码为位域
struct MaterialKey {
    uint64_t texture_filter : 3;
    uint64_t transparency : 3;
    uint64_t shading_mode : 2;
    uint64_t blend_mode : 3;
    uint64_t depth_draw_mode : 2;
    uint64_t cull_mode : 2;
    uint64_t diffuse_mode : 3;
    uint64_t specular_mode : 2;
    // ... 更多位域
    uint32_t feature_mask;  // 哪些特性启用
    uint32_t flags;         // 哪些标志启用
};

// 全局 shader 缓存：相同 Key 共享同一个编译好的 shader
static HashMap<MaterialKey, ShaderData, MaterialKey> shader_map;
static Mutex shader_map_mutex;
```

当材质参数改变时，`_compute_key()` 重新计算 Key，如果新 Key 在 `shader_map` 中已存在，直接复用；否则触发 shader 重新生成。这种设计使得 Godot 的 shader 变体数量远少于 UE。

#### UE 的实现

UE 的材质体系（`Engine/Source/Runtime/Engine/Classes/Materials/MaterialInterface.h`）：

```cpp
UCLASS(abstract, BlueprintType, MinimalAPI)
class UMaterialInterface : public UObject, 
                           public IBlendableInterface, 
                           public IInterface_AssetUserData
{
    USubsurfaceProfile* SubsurfaceProfile;
    FRenderCommandFence ParentRefFence;  // 渲染线程同步栅栏
    FLightmassMaterialInterfaceSettings LightmassSettings;
    TArray<FMaterialTextureInfo> TextureStreamingData;
    
    virtual UMaterial* GetMaterial() PURE_VIRTUAL;
    virtual FMaterialRenderProxy* GetRenderProxy() const PURE_VIRTUAL;
    virtual UPhysicalMaterial* GetPhysicalMaterial() const PURE_VIRTUAL;
};
```

UE 的材质系统有几个关键特点：
1. **Material Expression 图**：`UMaterial` 内部是一个节点图，每个节点是 `UMaterialExpression` 的子类
2. **FMaterialRenderProxy**：渲染线程通过代理对象访问材质，实现线程安全
3. **Material Instance**：`UMaterialInstance` 通过参数覆盖实现变体，支持 Static Switch 产生不同的 shader 变体
4. **物理材质**：`UMaterialInterface` 直接关联 `UPhysicalMaterial`，Godot 中物理材质是独立系统

#### 差异点评

| 维度 | Godot Material | UE UMaterialInterface |
|------|---------------|----------------------|
| Shader 编写 | 文本代码 (.gdshader) | 节点图 (Material Editor) |
| 变体管理 | MaterialKey 位域共享 | Static Switch + 排列组合 |
| 多 Pass | `next_pass` 链表 | 自定义渲染 Pass / Stencil |
| 参数存储 | `HashMap<StringName, Variant>` | 类型化参数 (Scalar/Vector/Texture) |
| 线程安全 | Mutex + RID 代理 | FMaterialRenderProxy + 渲染线程 |
| 物理材质 | 独立系统 | 内嵌在 MaterialInterface 中 |
| 编辑器集成 | 属性面板 + Shader 编辑器 | 完整的 Material Editor |

### 3.3 PackedScene vs ULevel/UBlueprint：场景打包和实例化对比

#### Godot 的实现

`PackedScene`（`scene/resources/packed_scene.h`）是 Godot 最独特的资源类型之一。它将一棵节点树序列化为可复用的资源，既是"关卡"也是"预制体"。

核心数据结构是 `SceneState`：

```cpp
class SceneState : public RefCounted {
    Vector<StringName> names;          // 字符串池
    Vector<Variant> variants;          // 值池
    Vector<NodePath> node_paths;       // 节点路径池
    
    struct NodeData {
        int parent = 0;    // 父节点索引
        int owner = 0;     // 所有者索引
        int type = 0;      // 类型名索引（指向 names）
        int name = 0;      // 节点名索引
        int instance = 0;  // 嵌套 PackedScene 索引
        int index = 0;     // 子节点排序索引
        Vector<Property> properties;  // 属性列表
        Vector<int> groups;           // 组列表
    };
    
    Vector<NodeData> nodes;
    
    struct ConnectionData {
        int from, to, signal, method, flags, unbinds;
        Vector<int> binds;
    };
    
    Vector<ConnectionData> connections;
};
```

**实例化流程**：`PackedScene::instantiate()` 调用 `SceneState::instantiate()`，遍历 `nodes` 数组，为每个 `NodeData` 创建对应类型的 `Node` 实例，设置属性，建立父子关系，连接信号。

关键特点：
1. **统一的场景/预制体概念**：Godot 中没有 UE 的 Level/Blueprint/Prefab 区分，一切都是 PackedScene
2. **嵌套实例化**：`NodeData::instance` 可以引用另一个 PackedScene，实现嵌套
3. **文本格式**：`.tscn` 是人类可读的文本格式，`.scn` 是二进制格式
4. **继承**：PackedScene 支持场景继承（`base_scene_idx`），子场景可以覆盖父场景的属性

#### UE 的实现

UE 中对应的概念分散在多个系统中：
- **ULevel / UWorld**：关卡/世界，包含 Actor 集合
- **UBlueprint**：蓝图类，可以实例化为 Actor
- **AActor 的 SpawnActor**：运行时实例化

UE 的关卡序列化基于 UObject 的 `FArchive` 序列化系统，每个 Actor 和 Component 都通过反射系统序列化。Blueprint 则通过 `UBlueprintGeneratedClass` 存储编译后的字节码和默认属性。

#### 差异点评

| 维度 | Godot PackedScene | UE Level/Blueprint |
|------|-------------------|-------------------|
| 概念统一性 | 场景=预制体=关卡 | Level ≠ Blueprint ≠ Prefab |
| 序列化格式 | 自定义紧凑格式（字符串池+值池） | UObject FArchive 序列化 |
| 文本格式 | .tscn（人类可读） | 无标准文本格式 |
| 嵌套 | 原生支持嵌套 PackedScene | Actor 嵌套 + Child Actor |
| 继承 | 场景继承（覆盖属性） | Blueprint 继承 |
| 实例化速度 | 快（简单的数组遍历） | 较慢（UObject 创建 + 反射） |

### 3.4 Shader vs Material Expression：着色器资源对比

#### Godot 的实现

Godot 的 `Shader`（`scene/resources/shader.h`）是一个简洁的资源类：

```cpp
class Shader : public Resource {
    enum Mode {
        MODE_SPATIAL,       // 3D 着色器
        MODE_CANVAS_ITEM,   // 2D 着色器
        MODE_PARTICLES,     // 粒子着色器
        MODE_SKY,           // 天空着色器
        MODE_FOG,           // 雾着色器
        MODE_MAX
    };
    
    mutable RID shader_rid;
    Mode mode = MODE_SPATIAL;
    String code;                    // 着色器源代码
    String include_path;
    HashSet<Ref<ShaderInclude>> include_dependencies;
    HashMap<StringName, HashMap<int, Ref<Texture>>> default_textures;
};
```

Godot 使用自己的 **Godot Shading Language**（类似 GLSL），着色器代码是纯文本。`Shader` 资源持有源代码字符串，通过 `set_code()` 设置后，RenderingServer 负责编译。

关键特点：
1. **文本着色器**：直接编写类 GLSL 代码，无需节点图
2. **5 种模式**：Spatial（3D）、CanvasItem（2D）、Particles、Sky、Fog
3. **Include 支持**：通过 `ShaderInclude` 资源实现代码复用
4. **默认纹理**：shader 可以声明默认纹理参数

#### UE 的实现

UE 的着色器系统远比 Godot 复杂：
- `UMaterial` 内部是 `UMaterialExpression` 节点图
- 节点图通过 `FMaterialCompiler` 编译为 HLSL
- HLSL 通过 `FShaderCompileJob` 编译为平台特定的 shader 字节码
- 编译结果存储在 `FShaderMap` 中
- 支持 Global Shader、Material Shader、Mesh Material Shader 等多种类型

#### 差异点评

Godot 的 Shader 系统追求**简洁直接**——一个文本文件就是一个完整的着色器。UE 的系统追求**可视化和工业级**——节点图对美术友好，但编译管线极其复杂。对于程序员来说，Godot 的文本 shader 更高效；对于美术团队来说，UE 的节点图更直观。

### 3.5 Environment vs APostProcessVolume：环境/后处理设置对比

#### Godot 的实现

Godot 的 `Environment`（`scene/resources/environment.h`）是一个 **Resource**，将所有环境和后处理设置集中在一个对象中：

```cpp
class Environment : public Resource {
    RID environment;
    
    // 背景
    BGMode bg_mode;
    Ref<Sky> bg_sky;
    
    // 环境光
    Color ambient_color;
    AmbientSource ambient_source;
    
    // 色调映射
    ToneMapper tone_mapper;
    float tonemap_exposure;
    
    // SSR, SSAO, SSIL, SDFGI
    bool ssr_enabled; float ssr_max_steps; ...
    bool ssao_enabled; float ssao_radius; ...
    bool ssil_enabled; float ssil_radius; ...
    bool sdfgi_enabled; int sdfgi_cascades; ...
    
    // Glow（泛光）
    bool glow_enabled; float glow_intensity; ...
    
    // 雾
    bool fog_enabled; FogMode fog_mode; ...
    
    // 体积雾
    bool volumetric_fog_enabled; float volumetric_fog_density; ...
    
    // 颜色校正
    bool adjustment_enabled; float adjustment_brightness; ...
};
```

`Environment` 是一个纯数据资源，通过 `WorldEnvironment` 节点或 `Camera3D` 的 `environment` 属性应用到场景中。每个属性变化都通过对应的 `_update_xxx()` 方法同步到 RenderingServer。

#### UE 的实现

UE 的后处理系统基于 `APostProcessVolume`（`Engine/Source/Runtime/Engine/Classes/Engine/PostProcessVolume.h`），这是一个 **Actor**（不是 Resource）：

```cpp
class APostProcessVolume : public AVolume, public IInterface_PostProcessVolume
{
    FPostProcessSettings Settings;  // 后处理设置（巨大的结构体）
    float Priority;                 // 优先级
    float BlendRadius;              // 混合半径
    float BlendWeight;              // 混合权重
    uint32 bEnabled : 1;
    uint32 bUnbound : 1;           // 是否全局生效
};
```

`FPostProcessSettings` 是一个包含数百个参数的巨大结构体，涵盖了 Bloom、DOF、Motion Blur、Color Grading、AO、SSR 等所有后处理效果。

#### 差异点评

| 维度 | Godot Environment | UE PostProcessVolume |
|------|-------------------|---------------------|
| 类型 | Resource（数据对象） | Actor（场景实体） |
| 空间混合 | 无（全局或 Camera 绑定） | Volume 空间混合 + 优先级 |
| 参数数量 | ~80 个参数 | ~300+ 个参数 |
| 应用方式 | WorldEnvironment 节点 / Camera | 放置在场景中的 Volume |
| 多区域混合 | 不支持 | 支持多 Volume 混合 |
| 天空系统 | `Sky` Resource + `ShaderMaterial` | `ASkyAtmosphere` + `ASkyLight` |

**关键差异**：UE 的 PostProcessVolume 支持**空间混合**——玩家走进不同区域时，后处理效果平滑过渡。Godot 的 Environment 是全局的，不支持基于空间位置的混合（需要通过脚本手动实现）。

---

## 第 4 章：UE → Godot 迁移指南

### 4.1 思维转换清单

| # | UE 思维 | Godot 思维 | 说明 |
|---|--------|-----------|------|
| 1 | "资产是 UObject，有完整的生命周期管理" | "资源是 RefCounted，引用计数自动管理" | 忘掉 GC、忘掉 `UPROPERTY()` 宏，Godot 用 `Ref<T>` 智能指针 |
| 2 | "Mesh 有 LOD 链，Cook 时预处理" | "Mesh 是原始数据，LOD 需要手动管理" | 忘掉自动 LOD 生成，Godot 中需要用 `LODGroup` 节点或手动切换 |
| 3 | "材质用节点图编辑" | "材质用文本 Shader 或属性面板" | 重新学习 Godot Shading Language，它比 HLSL 简单但功能也更有限 |
| 4 | "后处理是场景中的 Volume" | "后处理是 Environment 资源" | 忘掉空间混合，Godot 的 Environment 是全局设置 |
| 5 | "场景和预制体是不同的东西" | "一切都是 PackedScene" | 重新理解 Godot 的"场景即预制体"哲学 |
| 6 | "纹理有 Streaming 和 Mip 管线" | "纹理是简单的 Image 包装" | 忘掉纹理流送，Godot 纹理全量加载 |
| 7 | "渲染线程通过 RHI 访问 GPU" | "一切通过 RenderingServer RID" | 重新学习 RID 代理模式 |

### 4.2 API 映射表

| UE API | Godot 等价 API | 备注 |
|--------|---------------|------|
| `UStaticMesh` | `ArrayMesh` | Godot 无 LOD，需手动管理 |
| `UStaticMesh::GetRenderData()` | `ArrayMesh::surface_get_arrays()` | Godot 返回 Array，UE 返回 RenderData |
| `UMaterialInterface` | `Material` | Godot 基类更简单 |
| `UMaterial` (PBR) | `StandardMaterial3D` | Godot 用属性面板，UE 用节点图 |
| `UMaterialInstanceDynamic` | `ShaderMaterial` | Godot 直接引用 Shader + 设参数 |
| `UMaterialInstanceDynamic::SetScalarParameterValue()` | `ShaderMaterial::set_shader_parameter()` | Godot 用 Variant 统一类型 |
| `UTexture2D` | `ImageTexture` / `CompressedTexture2D` | 运行时用 ImageTexture，磁盘用 Compressed |
| `UTexture2D::CreateTransient()` | `ImageTexture::create_from_image()` | 运行时创建纹理 |
| `APostProcessVolume` | `Environment` + `WorldEnvironment` 节点 | Godot 是 Resource，需要节点承载 |
| `FPostProcessSettings::BloomIntensity` | `Environment::set_glow_intensity()` | Godot 叫 Glow 不叫 Bloom |
| `SpawnActor<T>()` | `PackedScene::instantiate()` | Godot 从 PackedScene 实例化 |
| `UWorld::SpawnActor()` | `Node::add_child(scene.instantiate())` | 实例化后需手动添加到场景树 |
| `UStaticMeshComponent` | `MeshInstance3D` | Godot 用节点而非组件 |
| `UMaterial::GetShaderMapId()` | `Material::get_shader_rid()` | 获取底层 shader 标识 |

### 4.3 陷阱与误区

#### 陷阱 1：不要期望 Godot 有自动 LOD

UE 程序员习惯了 `UStaticMesh` 的自动 LOD 生成和 Nanite。在 Godot 中，`ArrayMesh` 没有内置 LOD 管线。你需要：
- 使用 `GeometryInstance3D` 的 `lod_bias` 属性
- 手动创建多个 Mesh 并用 `VisibilityNotifier3D` 切换
- 或使用 `ImporterMesh` 在导入时生成 LOD

#### 陷阱 2：MaterialKey 共享意味着"相同设置=相同 Shader"

在 UE 中，每个 `UMaterial` 都是独立编译的。在 Godot 中，`StandardMaterial3D` 使用 `MaterialKey` 共享 shader。这意味着：
- 修改一个材质的 `transparency` 模式可能触发新 shader 编译
- 但修改 `albedo_color` 不会触发编译（只是 uniform 变化）
- 理解哪些参数影响 Key、哪些只是 uniform，对性能优化至关重要

#### 陷阱 3：Environment 不支持空间混合

UE 程序员习惯了在场景中放置多个 `APostProcessVolume` 实现区域化后处理。Godot 的 `Environment` 是全局的：
- 一个 `WorldEnvironment` 节点控制整个场景
- 如果需要区域化效果，必须通过脚本在 `Camera3D` 的 `environment` 属性上做插值
- 这是 Godot 相比 UE 的一个明显短板

#### 陷阱 4：PackedScene 的实例化是同步的

UE 的 `SpawnActor` 可以配合异步加载使用。Godot 的 `PackedScene::instantiate()` 是同步的——它会在当前帧创建所有节点。对于大型场景，这可能导致卡顿。解决方案：
- 使用 `ResourceLoader::load_threaded_request()` 异步加载 PackedScene
- 分帧实例化（手动拆分节点创建）

### 4.4 最佳实践

1. **材质管理**：优先使用 `StandardMaterial3D`，只在需要自定义效果时才用 `ShaderMaterial`。`StandardMaterial3D` 的 MaterialKey 共享机制能显著减少 shader 变体。

2. **纹理格式**：导入纹理时让 Godot 自动转换为 `.ctex`（CompressedTexture2D），不要在运行时频繁创建 `ImageTexture`。

3. **场景组织**：善用 PackedScene 的嵌套和继承。一个 PackedScene 既是预制体也是子关卡，不需要像 UE 那样区分 Blueprint 和 Level。

4. **Environment 配置**：创建多个 `Environment` 资源文件，通过脚本在不同区域切换 `Camera3D.environment`，模拟 UE 的 PostProcessVolume 混合效果。

5. **Mesh 优化**：对于静态场景，使用 `MeshLibrary` + `GridMap` 代替大量独立的 `MeshInstance3D`。对于需要 LOD 的场景，在导入时配置 LOD 或使用 `MultiMeshInstance3D` 进行实例化渲染。

---

## 第 5 章：性能对比

### 5.1 Godot 场景资源的性能特征

#### Mesh 性能

Godot 的 `ArrayMesh` 在**运行时创建和修改**方面性能优秀。`add_surface_from_arrays()` 直接将 Array 数据上传到 GPU，没有中间转换步骤。但缺少以下优化：

- **无 LOD 自动管理**：所有距离的网格都以最高精度渲染，除非手动实现 LOD
- **无 Mesh Streaming**：大型网格全量加载到内存
- **无 Nanite 等虚拟几何体**：无法处理电影级别的几何复杂度

`ArrayMesh` 的 Surface 数据结构非常紧凑（`scene/resources/mesh.h`），每个 Surface 只有 ~64 字节的元数据，实际顶点数据存储在 RenderingServer 中。

#### Material 性能

`BaseMaterial3D` 的 **MaterialKey 共享机制** 是 Godot 材质性能的核心优势：

```cpp
static HashMap<MaterialKey, ShaderData, MaterialKey> shader_map;
```

- 相同渲染配置的材质共享 shader，大幅减少 shader 编译次数
- `_queue_shader_change()` 使用脏标记延迟更新，避免频繁重编译
- `dirty_materials` 链表批量处理材质更新

但 `ShaderMaterial` 的参数存储使用 `HashMap<StringName, Variant>`，每次参数查找都有哈希开销。UE 的类型化参数（`FScalarParameterValue`、`FVectorParameterValue`）在这方面更高效。

#### Texture 性能

Godot 的纹理系统性能瓶颈主要在：
- **无 Mip Streaming**：纹理全量加载，大型项目内存压力大
- **CompressedTexture2D 的延迟加载**：首次访问时才从磁盘加载，可能导致卡顿
- **ImageTexture 的 CPU→GPU 传输**：`update()` 方法每次都重新上传整个纹理

#### Environment 性能

`Environment` 的每个属性变化都会调用对应的 `_update_xxx()` 方法，通过 RenderingServer 同步到渲染端。频繁修改 Environment 参数（如实时调整 fog 密度）会产生大量 RenderingServer 调用。

### 5.2 与 UE 的性能差异

| 性能维度 | Godot | UE | 差异原因 |
|---------|-------|-----|---------|
| Mesh 加载速度 | 快（简单格式） | 较慢（复杂 Cook 数据） | UE 含 LOD/碰撞/距离场等预计算数据 |
| Mesh 运行时创建 | 极快 | 较慢 | Godot 直接上传 Array，UE 需要创建 UObject |
| 大场景渲染 | 较慢（无 LOD/Nanite） | 快（LOD + Nanite + Streaming） | UE 有完整的几何优化管线 |
| Shader 编译 | 快（变体少） | 慢（变体多） | Godot MaterialKey 共享，UE 排列组合爆炸 |
| 材质参数更新 | 中等（HashMap 查找） | 快（类型化数组） | UE 参数存储更紧凑 |
| 纹理内存 | 高（全量加载） | 低（Mip Streaming） | UE 按需加载 Mip 级别 |
| 后处理切换 | 快（直接替换 Resource） | 中等（Volume 混合计算） | Godot 无混合开销，但也无混合功能 |

### 5.3 性能敏感场景的建议

1. **大量相似物体**：使用 `MultiMeshInstance3D`（对标 UE 的 `UInstancedStaticMeshComponent`），避免为每个物体创建独立的 `MeshInstance3D`。

2. **材质变体控制**：尽量让 `StandardMaterial3D` 的渲染模式（transparency、blend_mode 等）保持一致，只通过 uniform 参数（albedo、metallic 等）区分，这样可以最大化 MaterialKey 共享。

3. **纹理内存管理**：
   - 使用 `CompressedTexture2D` 而非 `ImageTexture`
   - 合理设置纹理导入的 `size_limit` 参数
   - 对于大型开放世界，考虑手动实现纹理流送

4. **PackedScene 实例化优化**：
   - 预加载常用的 PackedScene（`preload()`）
   - 使用对象池模式复用实例，避免频繁 `instantiate()` / `queue_free()`

5. **Environment 参数动画**：如果需要实时调整后处理参数（如日夜循环），批量设置参数后再触发更新，避免每个参数单独触发 RenderingServer 调用。

---

## 第 6 章：总结 — "一句话记住"

### 核心差异

**Godot 的场景资源是"轻量级数据容器 + RID 代理"，UE 的场景资源是"自包含的工业级资产"——前者追求简洁可组合，后者追求完整可控。**

### 设计亮点（Godot 做得比 UE 好的地方）

1. **MaterialKey 共享机制**：`BaseMaterial3D` 通过位域编码自动共享 shader 变体，这是一个极其优雅的设计。UE 的 shader 变体管理需要开发者手动优化（减少 Static Switch、使用 Shared Material 等），而 Godot 在框架层面就解决了这个问题。

2. **PackedScene 的统一性**：场景=预制体=关卡的统一概念，消除了 UE 中 Level/Blueprint/Prefab 的概念割裂。嵌套 PackedScene 和场景继承使得内容组织非常灵活。

3. **运行时 Mesh 创建**：`ArrayMesh::add_surface_from_arrays()` 让程序化生成网格变得极其简单。UE 中运行时创建 Mesh 需要处理 `FMeshDescription`、`FStaticMeshRenderData` 等复杂数据结构。

4. **文本 Shader**：Godot Shading Language 对程序员友好，一个 `.gdshader` 文件就是完整的着色器，无需 Material Editor 的节点图。

### 设计短板（Godot 不如 UE 的地方）

1. **无 LOD/Nanite**：Godot 缺少自动 LOD 生成和虚拟几何体技术，大型场景的几何优化完全依赖开发者手动处理。

2. **无纹理 Streaming**：所有纹理全量加载到内存，大型开放世界项目会面临严重的内存压力。

3. **Environment 无空间混合**：不支持 UE 的 PostProcessVolume 空间混合，无法实现"走进洞穴时后处理平滑过渡"等效果。

4. **材质系统灵活性有限**：`StandardMaterial3D` 虽然覆盖了常见 PBR 需求，但无法像 UE Material Editor 那样通过节点图实现任意复杂的材质逻辑（如程序化纹理混合、自定义光照模型等）。

5. **缺少 Cook 管线**：Godot 没有 UE 的 Cook/Package 管线，资源在编辑器和运行时使用相同格式，无法针对目标平台做深度优化。

### UE 程序员的学习路径建议

**推荐阅读顺序：**

1. **`scene/resources/material.h`** ★★★ — 从材质系统入手，理解 MaterialKey 共享机制和 RID 代理模式，这是 Godot 资源架构的精髓
2. **`scene/resources/mesh.h`** ★★★ — 理解 Surface 抽象和 ArrayMesh 的数据组织方式
3. **`scene/resources/packed_scene.h`** ★★★ — 理解 SceneState 的序列化格式和实例化流程，这是 Godot 最独特的设计
4. **`scene/resources/shader.h`** ★★ — 理解 Godot Shading Language 的资源封装
5. **`scene/resources/texture.h`** + **`image_texture.h`** ★★ — 理解纹理层次结构
6. **`scene/resources/environment.h`** ★★ — 理解后处理参数的组织方式
7. **`scene/resources/font.h`** ★ — 了解 Godot 的字体系统（与 UE 的 Slate 字体系统差异较大）

**实践建议：**
- 先用 `StandardMaterial3D` 的属性面板熟悉 Godot 的 PBR 参数
- 然后尝试写一个简单的 `.gdshader`，体验文本 shader 的开发流程
- 用 `ArrayMesh` 程序化生成一个简单网格，感受运行时 Mesh 创建的便捷性
- 创建嵌套的 PackedScene，理解"场景即预制体"的设计哲学
