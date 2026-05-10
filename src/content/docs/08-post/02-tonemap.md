---
title: 8.2 — 色调映射：从 HDR 走进屏幕
description: 理解为什么光照值可以超过 1.0，以及 Reinhard、ACES、Uncharted 2 三种曲线如何把无限大压缩到 [0,1]
---

这一节我们会讲解：

- HDR 渲染输出凭什么能让颜色超过 `1.0`
- 为什么直接把 HDR 截断到 `[0, 1]` 是新手最容易踩的坑
- Reinhard 色调映射——最简单、最教具
- ACES 和 Uncharted 2 曲线——电影感从哪来
- 用 `eyeBrightnessSmooth` 做自动曝光——进洞穴不提灯也能看清

好吧，我们开始吧。在延迟光照 pass 里，太阳直射的亮度可能到 `3.0` 甚至 `10.0`。你在 composite 里拿到 `colortex0` 时，很多像素的 RGB 值已经远超 `1.0` 了。

这时你有一个最傻的天问：屏幕的 R、G、B 发光强度最大就是 `1.0`（8-bit 显示就是 `255`），那 `3.2` 怎办？直接 clamp？还是想个办法把 `0.0` 到 `∞` 压缩进 `0.0` 到 `1.0`？

答案当然是后者——这就是色调映射。

> 色调映射 = 把 HDR（0~∞）映射到 LDR（0~1），让亮处不过曝、暗处不丢失。

---

## 新手陷阱：直接 clamp

你可能会想："我把所有超过 1.0 的值截成 1.0 不就行了？"

```glsl
outColor.rgb = clamp(sceneColor.rgb, 0.0, 1.0); // 别这么干
```

跑一下你会发现：太阳是一坨纯白像素，完全不需要区分"亮"和"非常亮"。太阳、天空、白墙全被压扁成同一个 `RGB(1,1,1)`，画面像被洗衣粉泡过一样。这叫 gamut clipping，所有超过上限的信息直接丢失。

我们不想要一视同仁。我们希望：暗处正常、中亮微提、极亮处被柔和地下压。影调曲线的形状，决定了画面的电影感。

---

## 曲线一：Reinhard——最简单，最教具

名字可能吓人，公式简单到犯规：

$$
L_{\text{mapped}} = \frac{L}{L + 1}
$$

内心独白一下：如果 `L = 0.1`（暗），结果约等于 `0.09`，暗处基本不动。如果 `L = 1.0`（中亮），结果`0.5`，被压了一半。如果 `L = 10.0`（超亮），结果是 `10/11 ≈ 0.91`，很亮，但永远不会超过 `1.0`。数学上，当 `L` 趋近无穷大，这条曲线以 `1.0` 为渐近线。

GLSL 三行：

```glsl
vec3 toneMapped = sceneColor.rgb / (sceneColor.rgb + vec3(1.0));
```

它的缺点是画面容易"偏灰"。因为中调被压暗了，高光也被压制得很温吞。但用来教学完美——你一眼能看懂每一条曲线在做什么。

---

## 曲线二：ACES——好莱坞工业标准

ACES（Academy Color Encoding System）是好莱坞的 HDR 色调映射标准。它没有简单到 Reinhard 那种两行，但代码量也不大。最常用的拟合版本叫 ACES Film，在游戏界被大量采用：

```glsl
vec3 ACESFitted(vec3 x) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}
```

你不需要背这些常数。只需要理解它的形状：暗处微微提亮，中调保留饱和度，高光被柔和地滚降。和 Reinhard 比，ACES 的画面更有"电影感"。这并不是魔法，而是 ACES 曲线在低亮和中亮区保留了更丰富的对比度，不像 Reinhard 那样把整个中调压进地板。

```mermaid
graph LR
    subgraph "三种曲线的表现"
        A[Reinhard: 暗处准, 中调灰, 高光温吞]
        B[ACES: 暗处微提, 中调高对比, 高光滚降自然]
        C[Uncharted2: 亮区饱和度保留, 高光略带暖]
    end
    style A fill:#1e293b,stroke:#94a3b8,color:#e2e8f0
    style B fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style C fill:#1e293b,stroke:#06b6d4,color:#e2e8f0
```

---

## 曲线三：Uncharted 2——游戏界的经典

出自 Naughty Dog 的技术演讲。核心是先做一条由多项式拟合的 Filmic S-Curve，再在外面包一层曝光和白点控制：

```glsl
vec3 Uncharted2Tonemap(vec3 x) {
    float A = 0.15, B = 0.50, C = 0.10, D = 0.20, E = 0.02, F = 0.30;
    return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F;
}

vec3 filmic(vec3 color, float exposure) {
    vec3 current = Uncharted2Tonemap(color * exposure);
    vec3 whiteScale = 1.0 / Uncharted2Tonemap(vec3(11.2)); // 白点
    return current * whiteScale;
}
```

这里有个新东西：`whiteScale`。它的作用是：你指定屏幕上的"白色"（比如 `RGB(11.2, 11.2, 11.2)` 对应现实中中等亮度），色调映射后，这个亮度正好映射到 `RGB(1, 1, 1)`。比它亮的被压缩，比它暗的正常保留。

---

## 曝光控制：让眼睛适应

等等——你一直在想"算法"，忘了一件很基本的事：人的瞳孔会收缩。白天阳光下和夜里的同一个房间，感光灵敏度差几个数量级。

Minecraft 里，玩家从地面走进洞穴，眼睛适应黑暗后，洞穴会变亮。Iris 提供的 `eyeBrightnessSmooth` 就是这份"瞳孔大小"：

```glsl
uniform float eyeBrightnessSmooth; // 范围大致 0.0~1.0
```

现在，你可以把曝光和它挂钩：

```glsl
float exposure = mix(0.3, 2.5, eyeBrightnessSmooth);
vec3 mapped = ACESFitted(sceneColor.rgb * exposure);
```

`eyeBrightnessSmooth` 低（暗环境）时，曝光自动调高，洞穴被提亮；`eyeBrightnessSmooth` 高（太阳底下）时，曝光收敛，画面不至于过曝。这就相当于自动曝光，不需要你手调，Iris 帮你从游戏里读。

> **注意**：`eyeBrightnessSmooth` 在不同 Iris 版本里的取值范围略有差异，有些版本是 `0~25`，有些已归一化到类似 `0~1`。建议 `clamp(eyeBrightnessSmooth / 25.0, 0.0, 1.0)` 做一次映射，保证兼容性。

完整色调映射代码——放在 `composite.fsh` 末尾，作为最终输出的最后一道工序：

```glsl
uniform float eyeBrightnessSmooth;

void main() {
    vec3 sceneColor = texture(colortex0, texcoord).rgb;

    // 自动曝光
    float exposure = mix(0.4, 2.2, eyeBrightnessSmooth);
    sceneColor *= exposure;

    // 色调映射
    vec3 mapped = ACESFitted(sceneColor);

    outColor = vec4(mapped, 1.0);
}
```

---

## 该放在管线哪个位置？

内心小剧场：你有了 Bloom。Bloom 是叠在色调映射前还是后？

答案：**色调映射前**。Bloom 的亮区提取依赖原始 HDR 值——如果先色调映射，`3.2` 的太阳变成了 `0.95`，你根本判断不出哪些像素应该发光。整个后处理链的顺序是：

```mermaid
flowchart LR
    A[HDR 场景<br/>光照值 0~∞] --> B[Bloom 提取与模糊]
    B --> C[Bloom 叠加<br/>仍在 HDR]
    C --> D[色调映射<br/>HDR→LDR]
    D --> E[色彩分级]
    E --> F[FXAA / TAA]
    F --> G[最终输出<br/>0~1]
```

这个顺序比你想的更重要：Bloom 要 HDR 才能区分太阳和草；色调映射要把 HDR 压缩成可显示的 LDR；FXAA 要在最终 LDR 上做，因为色调映射已经把高频细节（锯齿）留在了画面上。

![色调映射效果：左侧直接 clamp 导致高光丢失层次，右侧 ACES 映射保留亮暗部丰富细节](/images/screenshots/ch8_2_tonemap.png)

---

## 本章要点

- HDR 渲染中光照值可以远超 `1.0`，直接 `clamp` 会丢失高光层次。
- 色调映射用一条曲线把 `0~∞` 压缩到 `0~1`，保留亮部和暗部细节。
- Reinhard：$L/(L+1)$，最简单，但中调偏灰。
- ACES Fit：好莱坞工业标准，暗处微提、中调高对比、高光自然，代码不长效果好。
- Uncharted 2 Filmic：多项式 S-Curve，加上白点映射，游戏界经典。
- `eyeBrightnessSmooth` 驱动自动曝光——暗环境自动提亮，亮环境自动收敛。
- 色调映射在 Bloom 之后、FXAA 之前执行。

---

下一节：[8.3 — 色彩分级：饱和度、对比度与 LUT](/08-post/03-color-grade/)
