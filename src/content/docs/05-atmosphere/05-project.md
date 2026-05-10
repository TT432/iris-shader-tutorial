---
title: 5.5 — 实战：动态天空
description: 组合本章所学——昼夜循环天空渐变 + 星星闪烁，做一个完整的、随游戏时间自然变化的天空系统
---

这一节我们会讲解：

- 本实战的目标：一个随 `sunAngle` 平滑过渡的完整天空系统
- 蓝→橙红→深夜→晨曦的四阶段配色策略
- 把 5.1 的渐变和 5.2 的星星拼在一起
- 完整的 `gbuffers_skybasic.fsh` 代码
- 自检清单：怎么确认你的天空过渡是平滑的
- 扩展方向：如果时间充裕可以加什么

好吧，你在 5.1 认识了天空渐变，在 5.2 学会了撒星星。现在把它们拼在一起，做一个能自己判断"现在是白天、傍晚、深夜还是清晨"的天空。跑起来之后，你按着时间的快进键，天空会从头顶的湛蓝慢慢变成地平线的橙红，再沉入深夜，最后在天边冒出一缕鱼肚白。这种体验比看一万篇理论文章都更能让你理解大气散射。

---

## 目标拆解

我们这次只写一个文件：`gbuffers_skybasic.fsh`。它需要输出四个时间段的颜色：

1. 白天：天顶深蓝，地平线淡白蓝，靠近太阳的方向有暖白晕。
2. 傍晚：天顶变暗，地平线剧烈偏橙和红，太阳方向最亮。
3. 深夜：全天空接近黑蓝，头顶甚至偏黑紫色，地平线有非常轻的暖残留或完全消失。
4. 清晨：和傍晚镜像——天边先亮，然后蓝色慢慢从头顶压下来。

这四个阶段不是四个 `if` 分支。它们是同一个连续函数的四个区间。我们用一个数值——`sunAngle`——加上一段 `smoothstep` 的魔法，让所有颜色自然地流过这些阶段。

> 要点：不是“四段选一”，而是“一个函数跨四个区间”。

---

## 内心独白：为什么不用 `if`，要写连续函数

你可能会想：`if (sunAngle > 0.2 && sunAngle < 0.3) { 傍晚 }` 不就行了吗？可以，但这是机器在换档。傍晚前的最后一个像素是白天色，傍晚后的第一个像素是黄昏色——你肉眼一定会看到一道分界线。游戏里一天持续 20 分钟（默认），如果在傍晚那一两秒里天空突然变色，玩家会注意到。

`smoothstep(edge0, edge1, x)` 做的就是这件事：它不是一个开关，而是一个平缓的坡。在 `edge0` 之前全是 0，在 `edge1` 之后全是 1，中间平滑过渡。我们用好几个 `smoothstep` 来定义不同颜色的"出现区间"，然后让它们互相叠加。

---

## 配色设计：四个时间段的参考值

在做代码之前，先把你在草稿纸上比划的颜色写下来。下面这些值不是物理公式，是美术直觉加上在游戏里反复调出来的——你可以随意改它们。

| 阶段 | sunAngle 范围 | 天顶色 | 地平线色 | 太阳方向晕色 |
|------|--------------|--------|---------|-------------|
| 白天 | 0.25 ~ 0.75 | 深蓝 (0.2, 0.5, 1.0) | 淡蓝白 (0.75, 0.85, 1.0) | 暖白 (1.0, 0.9, 0.7) |
| 傍晚 | 0.60 ~ 0.80 | 暗蓝 (0.08, 0.15, 0.4) | 深橙红 (0.9, 0.3, 0.05) | 暖金 (1.0, 0.6, 0.2) |
| 深夜 | 0.80 ~ 0.20 | 蓝黑 (0.02, 0.03, 0.12) | 深蓝黑 (0.03, 0.04, 0.10) | 几乎没有 |
| 清晨 | 0.15 ~ 0.30 | 淡紫蓝 (0.15, 0.3, 0.7) | 淡橙粉 (0.7, 0.35, 0.2) | 淡金 (0.9, 0.65, 0.3) |

注意 `sunAngle` 的语义。Iris 的 `sunAngle`：0.0 是日出前，0.25 是正午，0.5 是日落前，0.75 是午夜。具体值可能因版本微调，但就按这个理解。

---

## 完整代码

以下是 `gbuffers_skybasic.fsh` 的完整实现：

```glsl
#version 330 compatibility

// FORCE_* 宏：方便截图时锁定特定时段
// 在实际游戏里不定义任何宏，shader 会跟随 sunAngle 自动变化

uniform float sunAngle;
uniform vec3 sunPosition;
uniform vec3 upPosition;
uniform int worldTime;
uniform float viewWidth;
uniform float viewHeight;

in vec4 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

// ---- 工具函数 ----
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

mat2 rotate2D(float a) {
    float s = sin(a), c = cos(a);
    return mat2(c, -s, s, c);
}

float starField(vec2 uv, float rotation) {
    vec2 centered = uv - 0.5;
    centered = rotate2D(rotation) * centered;
    centered += 0.5;

    vec2 starUV = centered * 90.0;
    vec2 cell = floor(starUV);
    vec2 fracPart = fract(starUV);

    vec2 starPos = vec2(hash(cell), hash(cell + 0.1));
    float dist = length(fracPart - starPos);
    float brightness = smoothstep(0.055, 0.0, dist);

    brightness *= hash(cell + 0.2) * 0.45 + 0.55;

    float twinkle = sin(float(worldTime) * 2.8 + hash(cell + 0.3) * 6.2832);
    twinkle = twinkle * 0.5 + 0.5;
    twinkle = twinkle * 0.55 + 0.45;
    brightness *= twinkle;

    brightness *= smoothstep(0.0, 0.04, uv.y);  // 地平线附近淡化
    return brightness;
}

void main() {
    // ---- 1. 时间参数 ----
    float h = texcoord.y;
    float t = clamp(sunAngle, 0.0, 1.0);

    // 四个阶段的权重：smoothstep 乘法和减法构造平滑过渡
    float dayWeight  = smoothstep(0.15, 0.40, t)
                     * (1.0 - smoothstep(0.50, 0.65, t));
    float duskWeight = smoothstep(0.50, 0.58, t)
                     * (1.0 - smoothstep(0.72, 0.85, t));
    float nightWeight = smoothstep(0.80, 0.92, t)
                      + (1.0 - smoothstep(0.02, 0.10, t));
    nightWeight = clamp(nightWeight, 0.0, 1.0);
    float dawnWeight = smoothstep(0.04, 0.12, t)
                     * (1.0 - smoothstep(0.24, 0.34, t));

    // ---- 2. 各阶段天顶色和地平线色 ----
    vec3 dayZenith    = vec3(0.22, 0.50, 0.98);
    vec3 dayHorizon   = vec3(0.60, 0.78, 1.00);
    vec3 duskZenith   = vec3(0.08, 0.15, 0.40);
    vec3 duskHorizon  = vec3(0.90, 0.30, 0.05);
    vec3 nightZenith  = vec3(0.008, 0.012, 0.08);
    vec3 nightHorizon = vec3(0.015, 0.020, 0.10);
    vec3 dawnZenith   = vec3(0.12, 0.28, 0.68);
    vec3 dawnHorizon  = vec3(0.68, 0.32, 0.18);

    // 加权混合
    vec3 zenithColor  = dayZenith  * dayWeight
                      + duskZenith  * duskWeight
                      + nightZenith * nightWeight
                      + dawnZenith  * dawnWeight;
    vec3 horizonColor = dayHorizon  * dayWeight
                      + duskHorizon  * duskWeight
                      + nightHorizon * nightWeight
                      + dawnHorizon  * dawnWeight;

    // 垂直渐变：h=0→地平线, h=1→天顶
    float vBlend = smoothstep(0.0, 1.0, h * 1.5);
    vec3 sky = mix(horizonColor, zenithColor, vBlend);

    // ---- 3. 日落/日出 地平线暖光 ----
    float horizonWeight = exp(-pow(h * 3.0, 2.0));
    sky = mix(sky, vec3(1.0, 0.35, 0.06), duskWeight * horizonWeight * 0.55);
    sky = mix(sky, vec3(0.82, 0.38, 0.20), dawnWeight * horizonWeight * 0.35);

    // ---- 4. Mie 散射光晕 + 太阳光盘 ----
    vec3 sunDir = normalize(sunPosition);
    vec3 upDir  = normalize(upPosition);
    float mieAngle = dot(upDir, sunDir);
    float mie = pow(clamp(mieAngle * 0.5 + 0.5, 0.0, 1.0), 12.0);
    float glowStr = mie * (dayWeight + duskWeight * 1.5 + dawnWeight * 0.7)
                  * (1.0 - h * 0.65);
    sky += vec3(1.0, 0.80, 0.45) * glowStr * 0.35;

    float sunDisk = pow(clamp(mieAngle, 0.0, 1.0), 100.0);
    sky += vec3(1.0, 0.92, 0.68)
         * sunDisk * (dayWeight + duskWeight * 0.8) * 0.7;

    // ---- 5. 星星（夜间 + 晨昏过渡） ----
    vec2 screenUV = gl_FragCoord.xy / vec2(viewWidth, viewHeight);
    float rotation = float(worldTime) * 0.007;
    float stars = starField(screenUV, rotation);

    float starVisibility = nightWeight + duskWeight * 0.25 + dawnWeight * 0.35;
    starVisibility = clamp(starVisibility, 0.0, 1.0);

    sky += vec3(0.95, 0.96, 1.0) * stars * starVisibility * 7.5;

    // ---- 6. 输出 ----
    outColor = vec4(sky, 1.0);
}
```

![动态天空效果：四个不同时间的截图对比——正午蓝天、傍晚橙红、深夜星空、晨曦淡紫](/images/screenshots/ch5_5_skycycle.png)

---

## 内心独白：这段代码的几个关键抉择

你可能注意到了，四个阶段的权重不是简单地 `if` 切，而是用了 `smoothstep` 的加减法。每段的定义是"从这个时间开始出现，到那个时间结束消失"。重叠的区间里两种颜色都会贡献一些，最终是两者的自然混合。

举个例子：`dayWeight = smoothstep(0.15, 0.40, t) * (1.0 - smoothstep(0.50, 0.65, t))`。第一部分 `smoothstep(0.15, 0.40, t)` 让白天从天亮时开始进入（t=0.15 到 0.40 之间平滑上升），第二部分 `(1.0 - smoothstep(0.50, 0.65, t))` 让白天在日落后退出（t=0.50 到 0.65 之间平滑下降）。这两项相乘产生一个梯形：白天在 0.40~0.50 之间是完全明亮的（两个 smoothstep 都给出 1.0），在 0.15 之前和 0.65 之后都是 0。

星空的可见度也做了类似处理：`starVisibility = nightWeight + dawnWeight * 0.3 + duskWeight * 0.3`。夜深时 nightWeight = 1，星星最亮。清晨和傍晚各乘 0.3，表示在过渡时段星星正在慢慢隐去，不是突然消失。

---

## 自检清单

跑起来之后，用下面这些步骤确认一切正常：

1. **白天正午 (sunAngle ≈ 0.25 ~ 0.30)**：天顶是否深蓝？地平线是否白蓝？太阳方向是否有一圈暖白？
2. **傍晚 (sunAngle ≈ 0.55 ~ 0.70)**：天顶是否开始变暗变紫？地平线是否剧烈偏橙？暖晕是否偏金橙色？
3. **深夜 (sunAngle ≈ 0.75 ~ 0.10)**：天空是否接近黑蓝？是否有稀疏但分布均匀的闪烁星星？
4. **清晨 (sunAngle ≈ 0.10 ~ 0.25)**：天边是否先亮起淡橙？蓝色是否从头顶慢慢压回来？地平线是否比傍晚偏粉？
5. **过渡平滑性**：把时间速度调到最快（游戏中 `/gamerule randomTickSpeed` 或某些调试 mod 的快进），盯着地平线。颜色跳变不能超过肉眼能察觉的范围——如果有断崖，检查你的 `smoothstep` 的 edge0 和 edge1 是否太近。
6. **天顶和地平线的一致性**：转一圈，确保地平线颜色在东西南北四个方向大致均匀（排除太阳方向的光晕效应后）。

如果有任何一点不对，先调数值别动结构。颜色是调出来的，只要你理解了这个权重系统，剩下的就是盯着屏幕改数字的快乐时光。

---

## 扩展方向

如果你做完了上面的内容还有时间（和热情），试试这些：

- **把星星颜色随机化**：用 hash(cell + 0.4) 给每颗星一个色温，从蓝白到暖白之间分布。
- **加入极光**：在高纬度方向（天空 UV 的某条带状区域）叠加用 `sin` 驱动的绿-紫渐变。
- **加入云**：先在 `gbuffers_skybasic` 中无关紧要的地方画一个简单的云层，用噪声函数控制形状。真正的体积云在后面第 16 章，但现在的简单尝试会让你对后面的内容更有胃口。
- **和雾联动**：把 `zenithColor` 和 `horizonColor` 的加权平均作为雾色写进一个 uniform，传给 gbuffers_terrain 的雾计算用。

---

## 本章要点

- 动态天空的核心是用一个连续函数（`sunAngle`）跨越四个时间段，而不是用 `if` 在时段间硬切换。
- `smoothstep` 加减法构造时段权重——每次重叠都保证过渡平滑。
- 天顶和地平线是两个独立的颜色轴：天顶深蓝→昼夜变化，地平线更敏感于太阳高度角。
- 星空可见度跟随时段权重：全夜最亮，清晨傍晚弱，白天消失。
- 调色是经验活：先定义参考色表，再用正确的数学结构把平滑过渡做出来。

---

> **"天空不是一层布。它是一个活着的渐变，从你头顶的湛蓝，到天边的橙红，再到头顶的星空。用对了权重，它自己就会呼吸。"**

下一章：[6.1 — 水面渲染：水为什么是特殊的](/06-water/01-water-intro/)
