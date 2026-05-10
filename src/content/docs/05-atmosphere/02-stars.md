---
title: 5.2 — 星星渲染：给夜空撒一把闪烁的胡椒
description: 在 skybasic 中用随机点生成星空，实现基于 worldTime 的旋转和随机闪烁
---

这一节我们会讲解：

- 为什么用 hash 函数而不是真正的随机数——以及 GPU 上的伪随机怎么来
- 如何把一堆"随机散点"变成天空上的星星
- `worldTime` 驱动的缓慢旋转：让天空看起来真的在转
- 闪烁效果：亮暗交替的星星才像活的，不是一成不变的贴图
- 代码写在哪：skybasic 还是 composite？各自的利弊

好吧，在 5.1 节你的夜空已经深蓝发黑了。但是——太干净了。一个只有渐变色的夜空，像游戏开场前的空白幕布。Minecraft 原版的夜空有小点点，我们也得有。而且我们要比原版更漂亮：随机分布、大小不一、会眨眼的星星。

---

## 星星的本质：一堆发光的散点

先想清楚一件事：星星不是 3D 天体。至少在本教程里不是。屏幕上的星星是一堆像素被点亮的坐标。我们要做的事只有三件：

1. 决定哪些屏幕位置有星星。
2. 决定每颗星有多亮。
3. 让它们转和闪。

内心独白：既然屏幕坐标是连续的，我需要一个办法把"很多很多随机点"映射到像素上。一个像素如果恰好落在某颗星的"位置"附近，就亮起来；否则保持背景色。这个"附近"就是星的大小，越近越亮，远了就暗。

---

## GPU 上的伪随机：hash 函数

CPU 上有 `rand()`，GPU 上没有——准确说，GLSL 没有内置的随机数。但我们可以写一个伪装的。一个常用的 trick 是 hash 函数：输入一个二维坐标，输出一个看起来完全没规律的 0~1 值。比如这个经典的三角学混叠：

```glsl
float hash(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));
    return fract(sin(h) * 43758.5453);
}
```

说实话，我第一次看这个函数心里是拒绝的。拿两个很大且不是整数的数字做点积，扔进 `sin`，再乘一个更大的数，最后取小数部分——这看起来像在凑一个碰巧能过的期末考试答案。但它确实有效：相邻的 `p` 会产出看起来完全不相关的输出。

> hash 不是真随机，但你的眼睛分不出来。这就够了。

这里的要点是：`fract(sin(dot(p, magic)))` 是 GLSL 里最常用、最轻量的伪随机模式。记住它，后面做噪声、做抖动、做采样偏移，还要回来找它。

---

## 在屏幕上撒点

思路是这样的：对于每个屏幕像素，把它在天空上的"位置"当作输入，hash 出一个值。这个值决定它附近有没有星星。

但直接对屏幕坐标做 hash 有个问题：hash 是纯函数，同一个屏幕位置永远产出同一个值。这本身是好的（稳定），但如果我想让星星随时间旋转，我就得在输入里混入旋转。

我们先写一个最简单的、不动的星空，放在 `gbuffers_skybasic.fsh` 里：

```glsl
// 放在 main() 外面，当作工具函数
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float starField(vec2 uv) {
    // 把 uv 放大，这样星星不会挤在一个像素格子里
    vec2 starUV = uv * 200.0;

    // 取整数部分作为"格子编号"
    vec2 cell = floor(starUV);
    // 小数部分表示在格子里的位置
    vec2 fracPart = fract(starUV);

    // 每个格子里最多一颗星
    // 用 hash 来决定这颗星在这个格子里的具体位置
    vec2 starPos = vec2(hash(cell), hash(cell + 0.1));

    // 像素离星星中心有多远
    float dist = length(fracPart - starPos);

    // 越近越亮，越远越暗
    float brightness = smoothstep(0.02, 0.0, dist);

    // 用 hash 给每颗星一个基础亮度，有的亮有的暗
    brightness *= hash(cell + 0.2) * 0.6 + 0.4;

    return brightness;
}
```

内心独白一下这段代码的每一步。

首先，`uv * 200.0`。原始屏幕坐标是 0~1，直接 hash 的话星星会大得像月亮。放大 200 倍，相当于把天空切成 200×200 个小格子。

其次，`cell = floor(starUV)`，`fracPart = fract(starUV)`。每个像素属于某个格子，格子里有一个小坐标 `fracPart`，从 `(0,0)` 到 `(1,1)`。

然后，用 `hash(cell)` 在这格子里随机放一颗星。`hash(cell)` 返回 0~1，星星可能在这个格子的任何位置。`hash(cell + 0.1)` 同理，两组 hash 给了星星一个随机的 `(x, y)`。

最后，`dist = length(fracPart - starPos)`——如果当前像素恰好离星星中心很近，`dist` 小，`brightness` 就高。`smoothstep(0.02, 0.0, dist)` 做了锐利的边缘：距离大于 0.02 就全黑，小于 0.0 就全亮，中间平滑过渡。

> 每格最多一颗星，hash 决定位置，distance 决定亮度。这就是 GPU 星空的全套秘密。

---

## 让星星转起来：`worldTime` 驱动旋转

天空应该转。或者准确说，你的视角在转——Minecraft 的白天黑夜是太阳和月亮绕着你转，但星星跟着天空一起转。这需要把 uv 旋转一下。

Iris 提供了 `worldTime`，它是一个随游戏 tick 不断增长的浮点数。另外，如果你只是想让天空旋转方向和 Minecraft 原版一致，`sunAngle` 也可以直接用。

```glsl
uniform float worldTime;
```

把旋转加进输入坐标：

```glsl
// 旋转矩阵
mat2 rotate2D(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat2(c, -s, s, c);
}

float starField(vec2 uv) {
    // 用 worldTime 做缓慢旋转
    float rotationSpeed = 0.01;
    float angle = worldTime * rotationSpeed;

    // 以天顶为中心旋转
    vec2 centered = uv - 0.5;
    centered = rotate2D(angle) * centered;
    centered += 0.5;

    // GIF 交付里星星必须足够可读，所以这里用较低密度配合更大的星点半径。
    vec2 starUV = centered * 90.0;
    // ... 后面的逻辑不变 ...
}
```

`worldTime` 每 tick 增加约 0.05，所以 `rotationSpeed = 0.01` 意味着约每 1200 ticks（一分钟）转差不多一整圈。你可以调这个速度也可以不调，看你想让星星转多快。

顺便说一下，旋转中心选在 `uv = (0.5, 0.5)` 也就是屏幕正中——这通常接近天顶方向。如果你想让北极星不动、其他星绕它转（像真实星空一样），就把旋转中心放在 `(0.5, 0.8)` 之类靠近北极点的位置。Minecraft 里北极大致在屏幕上方偏一侧，具体取决于你怎么拿天空投影。

---

## 让星星眨眼：闪烁效果

稳定的星星像贴图。会眨眼的星星像真的。闪烁来自于大气湍流导致星光抖动，但在我们的简化模型里，你可以用一个随时间变化的噪声项来模仿。

```glsl
// 在 starField 函数里，给每颗星加独立的闪烁
float twinkle = sin(worldTime * 2.8 + hash(cell + 0.3) * 6.2832);
twinkle = twinkle * 0.5 + 0.5; // 映射到 0~1
twinkle = twinkle * 0.55 + 0.45; // 0.45~1.0，GIF 里能看出闪烁

brightness *= twinkle;
```

每颗星用一个独立的相位偏移 `hash(cell + 0.3) * 6.2832`，这样它们不会同时眨眼——有的正亮起来，有的正暗下去。`twinkle * 0.55 + 0.45` 把亮度变化压在 0.45 到 1.0 之间，GIF 里能明显看到闪烁，但星星最低亮度也不会完全消失。你想让某些星星闪得更剧烈？给 hash 结果映射到更大的范围就行。

---

## 放哪：skybasic 还是 composite？

这里有两条路。写在哪取决于你的架构。

如果在 `gbuffers_skybasic.fsh` 里写，星星会直接画在天空背景上。好处是简单，不需要额外的纹理或 pass。坏处是你的 composite pass 没法单独处理星星——比如 Bloom 泛光，你想让亮星星向外发光，就必须在 composite 里能拿到"哪亮哪不亮"的信息。

另一个做法是在 composite pass 里跑星空。拿到屏幕 UV，重建天空方向，然后再跑 hash 和旋转。这样做的好处是你可以把星星亮度和天空底色分开写到不同的 colortex，或者在同一帧里把亮星提取出来做 Bloom。

对现在这个阶段，我们先放在 skybasic 里。简单，直接能跑，而且效果已经足够好了。

```glsl
// gbuffers_skybasic.fsh 里的完整调用
void main() {
    vec3 sky = /* 你 5.1 节的天空颜色代码 */;

    // skybasic 的 texcoord 可能不是稳定的屏幕 0~1 坐标；截图/GIF 里用屏幕坐标更可靠。
    vec2 screenUV = gl_FragCoord.xy / vec2(viewWidth, viewHeight);
    float stars = starField(screenUV);
    sky += vec3(0.95, 0.96, 1.0) * stars * 7.5;  // 冷白星光，GIF 中保持可读
    outColor = vec4(sky, 1.0);
}
```

![星空效果：深蓝夜空背景上随机分布着闪烁光点](/images/screenshots/ch5_2_stars.gif)

---

## 更进一步的思路（可选）

- 加不同颜色的星：再取一次 `hash(cell + 0.4)` 映射到冷白到暖白的光谱。
- 加银河：在特定 UV 范围里提高星星密度，模仿银河带。
- 加流星：一颗移动的亮点，位置由 `worldTime` 漂移，后面拖一条衰减的尾巴。
- 真实星图：你甚至可以做一个六面体天空盒贴图来替代程序化星星——但这得等到后面讲天空盒的时候。

---

## 本章要点

- 星星不复杂：hash 函数决定哪些坐标有星，距离决定亮度，旋转加闪烁让它看起来活着。
- `fract(sin(dot(p, magic)))` 是 GLSL 里最常见的伪随机模式，背下来可以到处用。
- `floor` + `fract` 把屏幕切成格子，每个格子一颗星，保证均匀分布。
- `worldTime` 控旋转速度，每颗星用独立 hash 做相位偏移来错开闪烁时间。
- skybasic 和 composite 都可以放星星，各有利弊；初学者选 skybasic 更简单。

下一节：[5.3 — 体积光：当阳光穿过树叶变成实体](/05-atmosphere/03-light-shafts/)
