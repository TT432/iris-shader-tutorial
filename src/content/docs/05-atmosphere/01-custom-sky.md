---
title: 5.1 — 自定义天空：把原版的蓝白渐变扔进垃圾桶
description: 用 gbuffers_skybasic 接管天空颜色，实现基于太阳高度角的大气散射渐变
---

这一节我们会讲解：

- `gbuffers_skybasic` 和 `gbuffers_skytextured` 分别做什么，为什么 Iris 把天空拆成两个 pass
- 大气散射的简化直觉：为什么白天是蓝的，傍晚是橙的——用 Rayleigh 和 Mie 不用博士论文
- `sunPosition` 和 `timeAngle` 如何联手驱动天空颜色插值
- 从午夜到正午的一次完整渐变，代码里怎么写
- 这个效果写在哪，别写错 pass

好吧，我们开始吧。你已经画过方块，做过阴影，调过光。现在抬头看看天。原版的天空是 Minecraft 内置的一个蓝白线性渐变——技术上没什么问题，只是它和你的光照系统毫无关系。你在下面把方块的漫反射做得再精致，天空一律蓝白黑渐变，不觉得有点割裂吗？

这一节，我们自己画天。

---

## 两个天空 pass：skybasic 和 skytextured

Iris 把天空分成两件活，分别交给两个 pass。这跟第 2.1 节里 `gbuffers_terrain` 只管固体地形是一个道理——职责分离。

`gbuffers_skybasic` 负责天空背景底色。它就是你在天地线之间看到的那片"天本身"，不分太阳月亮星星，只是一片渐变色。Iris 把它放在所有天空内容的最底层。

`gbuffers_skytextured` 画太阳和月亮本体。你白天看到那个圆形的发光白盘，以及晚上的方形月亮贴图，都在这里。

> skybasic 画底色，skytextured 画日月。搞清楚这一点，你就不会把太阳的颜色写进底色文件里。

内心独白一下：既然我这节的目标是让天空从蓝到橙自然过渡，我应该关心的是背景色还是太阳本体？答案是背景色。太阳的颜色可以在 skytextured 里处理，但天空的"大气层"颜色——那是 skybasic 的活。

---

## 大气散射，博士论文和你需要的那三句话

大气散射是一门正儿八经的物理。Rayleigh 散射、Mie 散射、单次散射近似、光学深度积分——这些词可以在气象学博士论文里找到。但你要在 shader 里实现的，只需要三条直觉。

**第一条：Rayleigh 散射是蓝天。** 阳光穿过大气层，波长较短的光（蓝色、紫色）容易被空气分子弹向四面八方。你抬头看的地方没有太阳，但蓝光被散射进了你的眼睛，所以天空是蓝的。

**第二条：Mie 散射是白日晕。** 阳光碰到较大的颗粒（水滴、尘埃），散射的波长不再挑颜色，所有颜色一起被弹开。结果就是太阳周围的一圈白亮光晕。

**第三条：太阳越低，光穿过的大气越厚。** 正午太阳在头顶，光线只穿过一层薄薄的大气，蓝色占主导。傍晚太阳贴地平线，光线斜着穿过厚厚的大气层，蓝色已经被散射殆尽，只剩下红色和橙色到达你眼睛。这就是为什么日出日落是暖色调。

> 你不用算积分。你要做的只是：根据太阳有多高，在蓝色和橙红色之间插值。

---

## 太阳有多高？`sunPosition` 和 `timeAngle`

我们有两种办法知道太阳的位置。第一种是 Iris 的 `sunPosition` uniform——它直接告诉你太阳在 gbuffer 空间里的方向坐标。如果你在第 2.3 节做过 Lambert 漫反射，你对 `sunPosition` 已经很熟悉了。

第二种是 `timeAngle`。这东西和 `sunPosition` 不一样——它是一个 `float`，表示游戏里一天的时间进度，从 0 到 1 循环。大致上，`0.0` 是日出，`0.25` 是正午，`0.5` 是日落，`0.75` 是午夜。

```glsl
uniform float sunAngle;   // Iris 提供：日出角度，控制天空颜色
uniform float timeAngle;  // Iris 提供：一天进度 0~1
```

内心独白：`sunPosition` 告诉你太阳在哪个方向，适合算方向光；`timeAngle` 告诉你现在是一天的什么时候，适合驱动天空颜色跨时间渐变。这一节我们用 `sunAngle` 做颜色插值——它天然反映了太阳高度。

不管你用哪个，思路是一样的：拿一个 0 到 1 之间的值，映射到颜色上。

---

## 第一版代码：蓝到白的最简渐变

在 `gbuffers_skybasic.fsh` 里，你可以先写一个最简单的东西试试手：

```glsl
#version 330 compatibility

uniform float sunAngle;
uniform vec3 sunPosition;
uniform vec3 skyColor;    // Iris 提供的原版天空色
uniform vec3 fogColor;    // 雾色，低角度时偏灰

in vec4 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

void main() {
    // sunAngle 接近 0 时太阳在地平线以下，天空暗
    // sunAngle 接近 1.0 时太阳在头顶，天空亮
    float sunHeight = sunAngle;

    // 最简单的蓝白渐变
    vec3 daySky = vec3(0.4, 0.6, 1.0);  // 淡蓝
    vec3 nightSky = vec3(0.02, 0.02, 0.08);  // 深蓝黑

    vec3 sky = mix(nightSky, daySky, sunHeight);

    outColor = vec4(sky, 1.0);
}
```

跑一下。你大概会看到天空从头顶的蓝色向下变暗，但地平线附近死白死白的——因为 `mix` 只能做线性，而真实天空不是线性。

---

## 加入 Rayleigh 和 Mie 的简化版

真正的天空渐变需要两样东西：蓝色（Rayleigh）和一圈白亮（Mie），还有地平线附近因为大气变厚而产生的暖色。

我们不去做真正的 Rayleigh 相位函数。我们用一种美术驱动的简化：用一个垂直梯度控制蓝→白，再用太阳高度角控制蓝→橙。

```glsl
#version 330 compatibility

uniform float sunAngle;
uniform vec3 sunPosition;
uniform vec3 upPosition;  // Iris 提供的天空方向

in vec4 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

void main() {
    // ---- 1. 垂直梯度：头顶蓝，地平线白 ----
    // texcoord.y 对应天空上的垂直位置——具体哪端是天顶取决于顶点数据
    // 如果你的天是倒的（头顶白、地平线蓝），把 pow(height,0.6) 改成 pow(1.0-height,0.6) 即可
    float height = texcoord.y;

    // ---- 2. Rayleigh-like 蓝色散射 ----
    vec3 rayleigh = vec3(0.2, 0.5, 1.0);  // 深蓝
    vec3 horizon  = vec3(0.8, 0.9, 1.0);  // 淡白蓝（地平线）

    vec3 skyGradient = mix(rayleigh, horizon, pow(height, 0.6));

    // ---- 3. 加入太阳高度角驱动的暖色调 ----
    float sunHeight = clamp(sunAngle, 0.0, 1.0);

    // 太阳低时（sunHeight 小）：橙色更多
    vec3 sunsetTint = vec3(1.0, 0.4, 0.1);  // 暖橙
    float sunsetFactor = pow(1.0 - sunHeight, 3.0);  // 太阳越低，暖色越强

    skyGradient = mix(skyGradient, sunsetTint, sunsetFactor * height);

    // ---- 4. 夜晚：暗蓝黑 ----
    vec3 nightColor = vec3(0.02, 0.02, 0.08);
    float nightFactor = smoothstep(0.0, 0.1, 1.0 - sunHeight);

    skyGradient = mix(skyGradient, nightColor, nightFactor);

    // ---- 5. 地平线附近的 Mie-like 光晕 ----
    // 太阳方向对天空亮度的影响
    vec3 sunDir = normalize(sunPosition);
    vec3 upDir  = normalize(upPosition);

    // 简单版：用天空方向 dot 太阳方向判断是否在"太阳那一侧"
    float mieAngle = dot(upDir, sunDir);
    float mie = pow(clamp(mieAngle * 0.5 + 0.5, 0.0, 1.0), 8.0);

    skyGradient += vec3(0.3, 0.25, 0.15) * mie * sunHeight * 0.4;

    outColor = vec4(skyGradient, 1.0);
}
```

![自定义天空效果：白天蓝、傍晚橙、夜晚深蓝黑](/images/screenshots/ch5_1_sky.png)

---

## 内心独白：这段代码每一步在解决什么

你可能看着这一段觉得有点长，问题不大，我们把它吃进去。

第一步，`height`。`texcoord.y` 在 skybasic 这个 pass 里代表天空上的垂直位置。具体映射方向（天顶在 `0` 还是 `1`）取决于 Minecraft 天空顶点的纹理坐标布局——不同版本可能有差异。你只需要保证最终效果是"头顶蓝、地平线白"，如果天是倒的就反过来。`pow(height, 0.6)` 让颜色过渡不那么线性，拉长蓝色区域。

第二步，`sunsetFactor`。`1.0 - sunHeight` 的意思是：太阳越低，这个因子越大。乘以 `height`，就是说暖色只在地平线附近出现，头顶仍然是蓝的。`pow(..., 3.0)` 是为了让这个过渡不那么线性——傍晚的橙色来得很晚但很突然，清晨同理。

第三步，`nightFactor`。如果 `sunHeight` 接近 0（太阳很低的深夜），`1.0 - sunHeight` 接近 1，然后用 `smoothstep(0.0, 0.1, ...)`做一个小的平滑区间，不要让天空从深蓝一秒钟跳进漆黑。

第四步，Mie 光晕。`upDir` 是天空向上的方向向量，`sunDir` 是太阳的方向向量。如果你站在"太阳那边"，这两个向量的点积会偏向正值，`mie = 1`；如果太阳在地平线以下，点积可能是负的，`mie = 0`。这就做出了"太阳那半边天比另一边亮"的效果。

---

## 别混淆！`gbuffers_skybasic` 不应该画太阳

一个容易犯的错：你在 `gbuffers_skybasic` 里画了一个圆形的太阳。如果你真的画了，它会在所有天空内容的最底层，被 `gbuffers_skytextured` 里的原版太阳覆盖。更糟的是，如果你的 skybasic 输出不透明颜色，它可能完全遮挡住后面的天空内容。

记住我们在本节开头说的：skybasic 只画底色。太阳和月亮，留给 skytextured。云，留给 gbuffers_clouds。

> skybasic = 底色层。skytextured = 日月层。把层序搞错，你的太阳就永远在天花板后面。

---

## 本章要点

- `gbuffers_skybasic` 画天空底色，`gbuffers_skytextured` 画日月。分清职责。
- 大气散射的直觉只需要三条：Rayleigh（蓝）是短波散射，Mie（白）是长波散射，太阳越低光穿过的大气越厚→越红。
- 用 `sunAngle` 或 `sunPosition` 驱动颜色插值，不要写积分——没人实时验算大气光学。
- 垂直梯度（天顶到地平线）和太阳高度角（蓝到橙）是两个正交的渐变轴，乘在一起才是完整的天空。
- 地平线暖色调不是固定颜色，而是太阳高度角的函数——越低越暖，越高越淡。
- 夜晚过渡用 `smoothstep` 做平滑，不要让天空在几秒内突变。

下一节：[5.2 — 星星渲染：给夜空撒一把闪烁的胡椒](/05-atmosphere/02-stars/)
