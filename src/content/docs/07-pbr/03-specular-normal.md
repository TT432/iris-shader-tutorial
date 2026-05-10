---
title: 7.3 — specular 贴图与法线贴图：把 PBR 参数读进 shader
description: 从 RGBA 通道解包粗糙度和金属度，切空间法线变换到世界空间——在 gbuffers 里一次喂饱光照管线
---

这一节我们会讲解：

- 在 gbuffers 里怎样用 `texture(specular, texcoord)` 读取 LabPBR 的四个通道
- 光滑度为什么要翻转成粗糙度——以及"1 减"这行代码的物理直觉
- 法线贴图的数据在切空间里，怎样用 TBN 矩阵把它转到世界空间
- GLSL 代码从采样、解包到输出 G-Buffer 的完整写法
- 常见踩坑：贴图缺失、通道误解、法线翻转

好吧，我们开始吧。第 7.1 节你知道了 LabPBR 在通道里塞了什么，第 7.2 节你拿到了 GGX 的数学公式。现在的问题是：怎么把这两者接起来？GGX 需要 roughness、F0 和法线——这些数据就在 `_s` 和 `_n` 贴图的像素里等着你。你要做的就是用 `texture()` 把它们捞出来，稍微做一点格式转换，再喂给光照 pass。

---

## 读取 specular 贴图：四个通道四个角色

内心独白来一下：我面前有一张 specular 贴图，四个通道分别存了光滑度、金属度、自发光、SSS。我先不管后面两个（它们属于进阶话题），先把前两个读出来：

```glsl
uniform sampler2D specular;   // ← MC_SPECULAR_MAP 自动绑定

// 在 main() 里：
vec4 specSample = texture(specular, texcoord);

float smoothness = specSample.r;   // R: 光滑度 [0, 1]
float metalness  = specSample.g;   // G: 金属度 [0, 1]
float emission   = specSample.b;   // B: 自发光 (先暂存)
float sss        = specSample.a;   // A: 次表面 (先暂存)
```

等一下——你注意到一个问题没有？GGX 公式要的是**粗糙度** (roughness)，不是光滑度。光滑度 1 表示镜面般光滑（roughness = 0），光滑度 0 表示极粗糙（roughness = 1）。两者是互补关系：

```glsl
float roughness = 1.0 - smoothness;
```

你可能会想：为什么贴图存光滑度而不是直接存粗糙度？因为**人眼对粗糙变化在高端（接近镜面）更敏感**。存光滑度让画贴图的艺术家在接近镜面的区域有更多精度。对 shader 程序员来说，你只需要记住一行转换就行。

> 贴图存储格式服务于艺术家体验。shader 里的格式转换是为了数学方便。你只是中间那个翻译官。

---

## 读取法线贴图：从 [0,1] 还原到 [-1,1]

法线贴图稍微多一点步骤。normal 贴图的 R 和 G 通道存的是切空间 (tangent-space) 的法线分量，值域映射到了 `[0, 1]`。你需要先把它还原到 `[-1, 1]`：

```glsl
uniform sampler2D norm;   // ← MC_NORMAL_MAP 自动绑定

vec4 normalSample = texture(norm, texcoord);
vec3 tsNormal = vec3(normalSample.rg * 2.0 - 1.0, 1.0);
```

等等，这里 B 通道我写了 `1.0`？没错——因为切空间法线总是朝"外"（指向片元表面外侧），它的 Z 分量永远是正的。所以我们可以只存 X 和 Y，Z 通过 `sqrt(1 - x² - y²)` 算出来。但很多资源包会在 B 通道塞高度图，并且 shader 约定中 Z 通道直接填 1.0（或者从 B 通道取），取决于你对精度和质量的要求。

简化方案就是上面这样：XY 还原，Z 填 1，然后归一化。这对大多数方块已经够用了。

```glsl
tsNormal = normalize(tsNormal);
```

---

## 切空间到世界空间：TBN 矩阵

现在有了切空间法线，但 GGX 和光照需要的是**世界空间法线**。你需要一个 TBN 矩阵把法线转过去。

TBN 代表 Tangent（切线）、Bitangent（副切线）、Normal（面法线）。这三个向量各指向方块表面的"右"、"上"、"朝外"，构成一个局部坐标系。Iris 在 `gbuffers_terrain` 里可以通过 `at_tangent` 拿到切线方向：

```glsl
in vec3 at_tangent;   // Iris 提供：方块表面的切线方向（世界空间）

// 在 main() 的某个位置：
vec3 N = normalize(normal);                         // 面法线（世界空间）
vec3 T = normalize(at_tangent - N * dot(at_tangent, N));  // Gram-Schmidt 正交
vec3 B = cross(N, T);                              // 副切线 = 法线 × 切线

mat3 TBN = mat3(T, B, N);                          // TBN 矩阵
vec3 worldNormal = normalize(TBN * tsNormal);       // 切空间 → 世界空间
```

`at_tangent` 是 Iris 从方块模型里传出来的切线，但它可能不和面法线完全垂直。所以我们在用之前做了一次 Gram-Schmidt 正交化：把切线中和法线"重影"的部分减掉，剩下一个严格垂直的 T。这样 T、B、N 才是一个标准正交基。

顺便说一下，`normal` 这个变量是你从 `.vsh` 传下来的世界空间法线。第 2.2 节我们已经在 `gbuffers_terrain.vsh` 里写过 `normal = gl_NormalMatrix * gl_Normal;`——注意它是**眼空间**而非世界空间的。如果你想得到世界空间法线，可以在 vsh 里换成 `normal = mat3(gl_ModelViewMatrixInverse) * (gl_NormalMatrix * gl_Normal);` 或用 Iris 提供的 `gbufferModelViewInverse` 矩阵。

> 法线是矢量的"异类"——它不随平移而变，只随旋转和缩放而变。所以变换法线时要小心使用矩阵，不能用普通 4×4 的模型矩阵直接乘。

---

## 组装：完整的 PBR 材质采样器

把前面说的全部拼在一起，你的 `gbuffers_terrain.fsh` 里 PBR 相关的部分大致长这样：

```glsl
uniform sampler2D texture;   // 原版颜色 atlas
uniform sampler2D norm;      // MC_NORMAL_MAP
uniform sampler2D specular;  // MC_SPECULAR_MAP
uniform sampler2D lightmap;

in vec2 texcoord;
in vec4 vertexColor;
in vec3 normal;              // 世界空间面法线
in vec2 lmcoord;
in vec3 at_tangent;          // Iris 提供的切线

/* RENDERTARGETS: 0,1,2,3 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outLightmap;
layout(location = 3) out vec4 outPBR;

void main() {
    vec4 albedo = texture(texture, texcoord) * vertexColor;

    // ── PBR 参数 ──
    vec4 specSample  = texture(specular, texcoord);
    float roughness  = 1.0 - specSample.r;  // 光滑度 → 粗糙度
    float metalness  = specSample.g;
    float F0_dielectric = 0.04;             // 绝缘体默认反射率

    // ── 法线 ──
    vec4 normalSample = texture(norm, texcoord);
    vec3 tsNormal = normalize(vec3(normalSample.rg * 2.0 - 1.0, 1.0));

    vec3 N = normalize(normal);
    vec3 T = normalize(at_tangent - N * dot(at_tangent, N));
    vec3 B = cross(N, T);
    vec3 worldNormal = normalize(mat3(T, B, N) * tsNormal);

    // ── lightmap ──
    vec4 bakedLight = texture(lightmap, lmcoord);

    // ── 写入 G-Buffer ──
    outColor    = albedo;
    outNormal   = vec4(worldNormal * 0.5 + 0.5, 1.0);
    outLightmap = bakedLight;
    outPBR      = vec4(roughness, metalness, F0_dielectric, 0.0);
}
```

注意这里我们多了一个 `outPBR` 输出——把 roughness、metalness 和 F0 打包放进 colortex3（或其他你指定的 G-Buffer 槽位）。这样 deferred 或 composite pass 读到它们时就不需要重新采样 specular 贴图了，直接从 G-Buffer 里拿即可。

> 在 gbuffers 里一次性把 raw 数据转成光照-ready 的参数，是延迟渲染的核心设计：让光照 pass 只用做"数学"，不用再做"查找"。

![specular 贴图与法线贴图效果：左侧普通纹理，右侧叠加了法线贴图后呈现微观凹凸感](/images/screenshots/ch7_3_specular_maps.png)

---

## 常见踩坑提醒

不要着急——你第一次跑这段代码大概率不会完美。以下是几个最常见的坑，提前告诉你：

**贴图缺失**。不是每个资源包都给所有方块提供 `_s` 和 `_n` 贴图。对于缺失的方块，采样会得到默认值（通常是全黑），导致 roughness=1、metalness=0——这恰好是"粗糙绝缘体"，表现接近原版，所以不算灾难性。

**法线方向翻转**。如果发现方块凹凸好像反了（凸的变凹），检查两件事：TBN 矩阵的 B 向量方向（试试 `cross(T, N)` 还是 `cross(N, T)`），以及 normal 贴图采样时 R 或 G 通道是否需要取反。

**世界空间还是眼空间**。法线向量在不同空间中值不一样。如果你在 `.vsh` 里传的是眼空间法线，那在 `.fsh` 里构造的 TBN 矩阵也必须是眼空间的。空间不一致会导致光照方向完全错误。

---

## 本章要点

- specular 贴图 R=光滑度（需翻转成粗糙度）、G=金属度、B=自发光、A=SSS。
- 法线贴图 RG 存切空间法线 XY，需 `× 2 - 1` 从 `[0,1]` 还原到 `[-1,1]`。
- TBN 矩阵由切线 (T)、副切线 (B)、面法线 (N) 组成，用于将切空间法线变换到世界空间。
- `at_tangent` 是 Iris 从方块模型传出的切线，使用前应 Gram-Schmidt 正交化以保证和法线垂直。
- 建议在 gbuffers 阶段把 PBR 参数（roughness、metalness、F0）提前算好写进 G-Buffer，光照 pass 直接读取。
- 贴图缺失时默认表现为粗糙绝缘体（与原版相近），法线方向错误通常源于 TBN 构造顺序或空间不一致。

这里的要点是：PBR 贴图采样的本质是"格式翻译"——把艺术家友好格式（光滑度、[0,1] 法线）翻译成物理公式友好的格式（粗糙度、[-1,1] 世界空间法线）。翻译对了，后面整条管线才能跑通。

下一节：[7.4 — 能量守恒：镜面 + 漫反射不能超过 100%](/07-pbr/04-energy/)
