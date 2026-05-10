---
title: 4.5 — 实战：初次阴影
description: 跟着步骤在 deferred.fsh 里接入阴影采样，让方块脚下出现第一块真实的阴影——像太阳真的在照
---

这一节我们会讲解：

- 从哪里开始——shaderpack 需要哪些新文件
- 创建 `shadow.vsh` / `shadow.fsh` 的最简实现
- 在 `shaders.properties` 里注册 shadow pass
- 在 `deferred.fsh` 里接入阴影采样函数
- 预期效果：方块脚下出现阴影，方向跟随太阳
- 自我检测清单——你的阴影是不是真的在"工作"

好吧，我们开始吧。前面四节你已经理解了整个 Shadow Mapping 的流程：先拍一张太阳视角的深度图，然后回到玩家视角，把每个像素投到那张图里比较深度。现在到了把这些知识变成一个真正跑在游戏里的效果的阶段。

内心独白一下：我现在有一个基于前面章节建好的 shaderpack。我有 `gbuffers_terrain.vsh/.fsh`、`deferred.fsh`、`composite.fsh`、`shaders.properties`。我要加两个新文件（shadow.vsh 和 shadow.fsh），改一个配置文件，然后在 deferred.fsh 里写一个采样函数。听起来是不是比想象中简单？

> 本章实战的目标：不是让阴影完美，而是让阴影出现。

---

## 第一步：创建 shadow.vsh

在 `shaders/` 目录下新建 `shadow.vsh`。内容如下：

```glsl
#version 330 compatibility

out vec2 texcoord;
out vec4 vertexColor;

void main() {
    gl_Position = shadowProjection * shadowModelView * gl_Vertex;
    texcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vertexColor = gl_Color;
}
```

照常，`shadowProjection` 和 `shadowModelView` 由 Iris 自动提供，你不需要声明。你只需要用它们。

---

## 第二步：创建 shadow.fsh

在同一目录下新建 `shadow.fsh`：

```glsl
#version 330 compatibility

uniform sampler2D texture;

in vec2 texcoord;
in vec4 vertexColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 shadowcolor;

void main() {
    vec4 albedo = texture(texture, texcoord) * vertexColor;
    shadowcolor = albedo;
}
```

还记得第 4.2 节的讨论吗——这个颜色输出实际上不参与阴影判断。深度是 GPU 自动写进深度缓冲的，Iris 会把那张深度缓冲暴露为 `shadowtex0`。但 OpenGL 的 FBO 要求 shadow pass 必须有一个颜色附件，所以我们照写不误。

---

## 第三步：更新 shaders.properties

打开你的 `shaders.properties`，确保 shadow pass 被注册。如果之前没有 shadow 相关的行，加进去：

```properties
# Shadow pass — 开启阴影渲染
SHADOW_ENABLED = true

# Shadow Map 分辨率（推荐从 1024 开始，后面可以调大到 2048 或 4096）
shadowMapResolution = 1024

# 阴影渲染距离（太阳光线能投射多远的阴影）
shadowDistance = 100.0
```

这些配置告诉 Iris：请在每帧渲染 shadow pass，用 1024×1024 的分辨率，覆盖半径 100 格的范围。`SHADOW_ENABLED = true` 是最关键的一行——如果没有它，Iris 根本不会跑 shadow pass。

---

## 第四步：在 deferred.fsh 里接入阴影采样

打开你的 `deferred.fsh`，在文件顶部加入需要的 uniform 声明：

```glsl
uniform sampler2D shadowtex0;
uniform mat4 shadowModelView;
uniform mat4 shadowProjection;
uniform vec3 sunPosition;
uniform sampler2D depthtex1;          // 如果 shadowtex0 是 depth 纹理
uniform vec2 shadowMapResolution;     // 可选，用于计算 texelSize
```

如果你的 `deferred.fsh` 还没有 `worldPos` 的重建——你需要在读取 G-Buffer 后，用深度和逆投影矩阵把世界坐标算出来。这在第 5 章会详细讲，现在你可以用一个简化版：如果之前已经把 `worldPos` 通过 varying 从 gbuffers 传到了 deferred（不是标准做法，但调试阶段可用），那就直接用。如果还没有，暂时用一个固定位置做测试。

现在把第 4.3 节和第 4.4 节的阴影函数放到 `deferred.fsh` 里。我们用一个渐进策略——**先跑硬阴影，确认管道通了，再加 PCF**。

### 阶段 A：最小硬阴影（确认管道通了）

```glsl
float getShadow(vec3 worldPos) {
    vec4 shadowViewPos = shadowModelView * vec4(worldPos, 1.0);
    vec4 shadowClipPos = shadowProjection * shadowViewPos;

    if (shadowClipPos.w <= 0.0) return 1.0;

    vec3 shadowNDC = shadowClipPos.xyz / shadowClipPos.w;
    vec3 shadowCoord = shadowNDC * 0.5 + 0.5;

    if (shadowCoord.x < 0.0 || shadowCoord.x > 1.0 ||
        shadowCoord.y < 0.0 || shadowCoord.y > 1.0) {
        return 1.0;
    }

    shadowCoord.z -= 0.001; // 最小 bias
    return shadow2D(shadowtex0, shadowCoord).r;
}
```

然后在光照计算的地方，乘上这个系数：

```glsl
float shadow = getShadow(worldPos);
vec3 direct = calculateDirectLight(normal, sunPosition);
vec3 ambient = calculateAmbient() * 0.2; // 环境光保留，暗面不完全黑
outColor.rgb = albedo * (direct * shadow + ambient);
```

`ambient * 0.2` 是个经验值。阴影区域应该暗，但不能全黑——真实的散射光多少会填进阴影里。

---

### 阶段 B：升级到 PCF 软阴影（管道通了之后）

确认能看到阴影后，把 `getShadow` 替换成第 4.4 节的 `calculateSoftShadow` 函数。从头到尾放一起：

```glsl
const vec2 poissonDisk[16] = vec2[16](
    vec2(-0.9420,  0.3993), vec2( 0.9456, -0.7689),
    vec2(-0.0942, -0.9294), vec2( 0.3450,  0.2939),
    vec2(-0.7155,  0.1693), vec2(-0.2640, -0.2159),
    vec2( 0.4160,  0.1829), vec2(-0.6320, -0.5269),
    vec2( 0.1280,  0.5884), vec2(-0.3870,  0.7314),
    vec2( 0.8600, -0.0890), vec2(-0.7710, -0.4020),
    vec2(-0.0880, -0.5470), vec2( 0.5880,  0.6960),
    vec2(-0.4630,  0.0860), vec2( 0.2230, -0.8290)
);

float getSoftShadow(vec3 worldPos, vec3 normal, float radius) {
    vec3 biasedPos = worldPos + normal * 0.02;

    vec4 shadowViewPos = shadowModelView * vec4(biasedPos, 1.0);
    vec4 shadowClipPos = shadowProjection * shadowViewPos;
    if (shadowClipPos.w <= 0.0) return 1.0;

    vec3 shadowNDC = shadowClipPos.xyz / shadowClipPos.w;
    vec3 shadowCoord = shadowNDC * 0.5 + 0.5;

    if (shadowCoord.x < 0.0 || shadowCoord.x > 1.0 ||
        shadowCoord.y < 0.0 || shadowCoord.y > 1.0) return 1.0;

    vec3 sunDir = normalize(sunPosition);
    float bias = max(0.005 * (1.0 - dot(normal, sunDir)), 0.0005);
    shadowCoord.z -= bias;

    float angle = fract(sin(dot(shadowCoord.xy,
        vec2(12.9898, 78.233))) * 43758.5453) * 6.283185307;
    float cs = cos(angle);
    float sn = sin(angle);

    vec2 texelSize = 1.0 / vec2(1024.0);

    float shadow = 0.0;
    for (int i = 0; i < 16; i++) {
        vec2 offset = poissonDisk[i] * texelSize * radius;
        vec2 rotated = vec2(
            offset.x * cs - offset.y * sn,
            offset.x * sn + offset.y * cs
        );
        vec3 sampleCoord = shadowCoord;
        sampleCoord.xy += rotated;
        shadow += shadow2D(shadowtex0, sampleCoord).r;
    }
    return shadow / 16.0;
}
```

在光照处调用：

```glsl
float shadow = getSoftShadow(worldPos, normal, 2.5);
outColor.rgb = albedo * (directLight * shadow + ambientLight * 0.15);
```

---

## 第五步：跑起来，观察

启动 Minecraft，加载你的 shaderpack。站在平地上，放几个方块在头顶或身边。

你应该能看到：

1. **方块脚下有阴影** — 一个方块立在地上，背向太阳的一侧地面上出现一块暗色区域。
2. **阴影方向跟随太阳** — 用 `/time set 0`（日出）、`/time set 6000`（正午）、`/time set 12000`（日落），阴影的长度和方向应该跟着变。正午阴影最短，日出日落阴影最长。
3. **自己身上也有阴影** — 如果你站在方块旁边，你的身体（实体）也会投射阴影。取决于你的 `gbuffers_entities` 是否也采样了 shadow map。

![方块脚下的第一片阴影：像太阳真的在照射，阴影投射在地面上](/images/screenshots/ch4_5_first_shadow.png)

如果没有看到阴影，回到第 4.2 节的调试技巧：在 `shadow.fsh` 里输出纯红色，在 `deferred.fsh` 里读 `shadowcolor` 到屏幕上，确认 shadow pass 的确在运行。

---

## 自我检测清单

在进入第五章之前，确认以下每一项：

- [ ] `shadow.vsh` 和 `shadow.fsh` 已创建，内容正确。
- [ ] `shaders.properties` 中 `SHADOW_ENABLED = true`。
- [ ] `deferred.fsh` 中声明了 `shadowtex0`、`shadowModelView`、`shadowProjection`、`sunPosition`，且名称与 Iris 注册的一致。
- [ ] 世界坐标 `worldPos` 正确传入阴影函数（不是 `(0,0,0)`）。
- [ ] `shadowCoord.z` 加了 bias（至少 `0.0005`），且没有看到一个像素在"自己遮自己"。
- [ ] 阴影方向确实指向太阳的反方向（正午阴影短，傍晚阴影长）。
- [ ] 环境光（ambient）保留了一部分亮度——阴影区域不完全黑。
- [ ] 升级到 PCF 后，阴影边缘柔和，没有整齐的格子条纹。
- [ ] 帧率在可接受范围内（PCF 16 点采样对大多数设备应该流畅）。

---

## 常见问题排查

### Q: 完全看不到阴影，画面和加阴影之前一样。
**A:** 最大可能是 `SHADOW_ENABLED` 没设，或者 `shadowtex0` 的名字拼错了。按第 4.2 节的调试方法，在 shadow.fsh 里输出全红，在 deferred.fsh 里直接读 `shadowcolor` 看看能不能看到红色画面。

### Q: 阴影方向反了——阴影跑到太阳同一边去了。
**A:** 检查 `shadowProjection * shadowModelView` 的乘积顺序。如果你的变换是 `shadowModelView` 在左，确认它和 shadow.vsh 里的顺序完全一致。

### Q: 方块表面全是黑色条纹/斑点。
**A:** Shadow acne。增大 bias——把 `0.0005` 调到 `0.005` 试试。如果阴影开始"漂浮"（方块底部和阴影之间有缝隙），再降回来。加上法线偏移能改善很多。

### Q: 阴影边缘有整齐的条纹，不像柔和的过渡。
**A:** 你还没加 PCF。或者 PCF 的渲染种子每次一样——确认随机旋转的 `angle` 在不同像素上确实不同。可以用 `gl_FragCoord.xy` 代替 `shadowCoord.xy` 做哈希种子。

### Q: 远处的阴影非常粗糙，像一团马赛克。
**A:** Shadow Map 分辨率太低。在 `shaders.properties` 里把 `shadowMapResolution` 调到 2048 或 4096。注意这会增加显存占用，但对于教程阶段通常够用。

---

## 本章要点

- 实战步骤：创建 `shadow.vsh` / `shadow.fsh` → 更新 `shaders.properties` → 在 `deferred.fsh` 里接入阴影采样。
- 先跑最小硬阴影确认管道通畅，再升级到 PCF 软阴影。
- `shadowtex0` 存的是深度，不是颜色；阴影判断读的是深度纹理。
- `SHADOW_ENABLED = true` 是 shadow pass 的总开关。
- `shadowModelView` 和 `shadowProjection` 必须在采样侧和 shadow pass 侧完全一致。
- 阴影不是独立效果——它乘在直接光照（direct light）上，环境光（ambient）保留以模拟散射。

> 从 0 到 1 的阴影是最难的一步。一旦它出现了，剩下的所有优化——PCF、bias 调参、CSM——都是在这个地基上添砖加瓦。

下一节：[5.1 — 延迟光照（即将推出）](/05-deferred/01-deferred-intro/)
