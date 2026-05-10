---
title: 6.2 — 法线贴图水波：让水面动起来
description: 用噪声纹理扰动法线，双层叠加不同速度方向，frameTimeCounter 驱动——让静态水面变成活的波浪
---

这一节我们会讲解：

- 为什么法线贴图比直接挪顶点更适合做水波
- 从一张噪声图变出"波浪法线"的三步拆解
- 双层叠加——不同速度、不同方向——为什么一层不够
- `frameTimeCounter` 如何成为波浪跳动的心脏
- 完整 `gbuffers_water.fsh` 中的水波法线生成代码

好吧，我们开始吧。第 6.1 节说水是"会动的"。现在我们要真的让它动起来。你的第一反应可能是：那我直接在顶点着色器里把 `gl_Vertex` 的 Y 坐标按正弦波上下推，不就行了？

内心独白一下：推动顶点确实能造出几何波浪，但在 Minecraft 里，水面通常只是一个薄片——就那么几个顶点。如果只挪顶点，你看到的会是整块水面像一块板子一样上下平移，而不是细腻的涟漪。真正的波浪感，来自**法线贴图**。

---

## 为什么是法线，而不是顶点

想一想：你在屏幕上看水面，最让你感觉"它在动"的是什么？不是整块水面升了 1 像素或降了 1 像素——那是整个水方块在动。而是光照在每一帧都在闪烁：亮斑来回跑，暗纹在漂移。

这些亮暗变化来自哪里？来自法线。回顾 2.3 节，`dot(N, L)` 决定了表面有多亮。如果你能让法线微微扰动，同一个像素这一帧朝向光源多一点，下一帧朝向光源少一点——它就会闪。无数个像素一起闪，看上去就是波光粼粼。

> 水波不需要真的移动顶点。扰动法线就足以骗过眼睛。

---

## 从噪声图到波浪法线

现在我们需要的是一张噪声纹理——一片随机灰度斑点，像电视雪花一样，但更平滑。实际光影包里通常会用一张 512×512 或更小的平铺噪声图。没有这张图也没关系，你可以用程序化噪声（比如基于 `texcoord` 的正弦积）临时造一个。

拿到噪声以后，关键操作是把**亮度差转化成法线偏移**。内心独白一下：一张图是纯白的地方和纯黑的地方之间，存在一个"坡度"。如果我把这个坡度的方向和大小算出来，然后把它加在原本的法线上——原本平平朝上的水面法线 `(0, 1, 0)` 就会开始往四周晃。

具体来说，分三步：

1. **采样**：在噪声图上取当前位置 `uv` 和它右边、上边各 1 个纹素的值。
2. **差分**：右减中、上减中，得到水平方向 `dx` 和垂直方向 `dy` 的亮度变化。
3. **构造偏移**：用 `dx` 和 `dy` 捏出一个偏离 `(0, 0, 1)` 的微小方向向量。

写成 GLSL：

```glsl
float step = 0.001;  // 纹素步长，控制波浪细腻程度

float n0 = texture(noisetex, uv).r;
float n1 = texture(noisetex, uv + vec2(step, 0.0)).r;
float n2 = texture(noisetex, uv + vec2(0.0, step)).r;

float dx = n1 - n0;  // 水平方向坡度
float dy = n2 - n0;  // 垂直方向坡度

vec3 waveNormal = normalize(vec3(-dx, -dy, 1.0));
```

这里 `vec3(-dx, -dy, 1.0)` 的意思是：原本法线指向 Z（或 tangent space 里的"朝上"），我们把它往 X 和 Y 方向推一下。推的幅度是 `dx` 和 `dy`，方向取反——因为噪声图右边更亮，意味着"坡"往左翘。`1.0` 保持主要朝向不变。`normalize` 保证它还是一个单位向量。

> 核心公式：`waveNormal = normalize(vec3(-dx, -dy, 1.0))`。噪声图的亮度差变成了法线的摇晃。

---

## 为什么一层不够

你可能会想：一层噪声就够了，我调一调 `step` 的大小不就能控制波浪细密程度了吗？

你试着只跑一层，然后盯着水面看 10 秒。发现没有——它看起来像一块在流动的丝绸，而不是自然的水面。真实水面的波浪永远不会只有一个频率。远处是大块的涌浪，近处是细碎的涟漪。两个频率混在一起，才有"水"的样子。

所以标准做法是双层的：

- **低频层**：移得慢，方向斜一点，幅度大——负责"涌浪感"。
- **高频层**：移得快，方向不同，幅度小——负责"细碎感"。

```glsl
// 低频——大浪，慢移
float lowFreqN0 = texture(noisetex, uv * 2.0 + vec2(time * 0.02, time * 0.01)).r;
float lowFreqN1 = texture(noisetex, uv * 2.0 + vec2(time * 0.02 + step, time * 0.01)).r;
float lowFreqN2 = texture(noisetex, uv * 2.0 + vec2(time * 0.02, time * 0.01 + step)).r;
float dxLow = lowFreqN1 - lowFreqN0;
float dyLow = lowFreqN2 - lowFreqN0;

// 高频——细浪，快移，方向相反
float hiFreqN0 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08, time * 0.06)).r;
float hiFreqN1 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08 + step, time * 0.06)).r;
float hiFreqN2 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08, time * 0.06 + step)).r;
float dxHi = hiFreqN1 - hiFreqN0;
float dyHi = hiFreqN2 - hiFreqN0;
```

注意低频层用的是 `uv * 2.0`（拉伸贴图→波浪变宽），高频层用 `uv * 8.0`（压缩贴图→波浪变密）。低频的移动向量是 `(0.02, 0.01)`（慢），高频是 `(-0.08, 0.06)`（快，且方向相反）。

然后合并两层：

```glsl
float waveStrength = 0.8;  // 低频权重
float rippleStrength = 0.2; // 高频权重

float dx = dxLow * waveStrength + dxHi * rippleStrength;
float dy = dyLow * waveStrength + dyHi * rippleStrength;

vec3 waveNormal = normalize(vec3(-dx, -dy, 1.0));
```

---

## frameTimeCounter：跳动的心脏

上面的代码里出现了 `time`，但这个变量不是你声明的——它是 Iris 给你的：

```glsl
uniform float frameTimeCounter;
```

`frameTimeCounter` 记录的是从游戏启动到当前帧经过的总秒数（是真实的 wall clock，不受游戏暂停影响）。把它直接丢进 UV 偏移，波浪就会随着时间连续移动。

关键细节：低频和高频用了不同的乘数（`0.02` vs `0.08`），而且低频在 X 和 Y 方向的偏移系数不相等（`0.02` 和 `0.01`）。这让波浪不仅速度不同，漂移的**方向斜角**也不同。如果你让两层往同一个方向飘，出来的效果就像冲水马桶。

顺便说一下，有些光影还会额外叠加一张"水流方向"噪声来模拟河流或者海洋有方向性的水面流动。这个不着急，先把静态双层叠加跑通。

---

## 完整的水波法线生成

把上面所有东西拼进 `gbuffers_water.fsh`：

```glsl
#version 330 compatibility

uniform sampler2D noisetex;
uniform float frameTimeCounter;

in vec2 texcoord;
in vec3 normal;
in vec4 vertexColor;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outMaterial;

void main() {
    float time = frameTimeCounter;
    vec2 uv = texcoord;
    float step = 0.002;

    // ── 低频层 ──
    float nL0 = texture(noisetex, uv * 2.0 + vec2(time * 0.02, time * 0.01)).r;
    float nL1 = texture(noisetex, uv * 2.0 + vec2(time * 0.02 + step, time * 0.01)).r;
    float nL2 = texture(noisetex, uv * 2.0 + vec2(time * 0.02, time * 0.01 + step)).r;
    float dxL = nL1 - nL0;
    float dyL = nL2 - nL0;

    // ── 高频层 ──
    float nH0 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08, time * 0.06)).r;
    float nH1 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08 + step, time * 0.06)).r;
    float nH2 = texture(noisetex, uv * 8.0 + vec2(-time * 0.08, time * 0.06 + step)).r;
    float dxH = nH1 - nH0;
    float dyH = nH2 - nH0;

    // ── 合并 ──
    float dx = dxL * 0.7 + dxH * 0.3;
    float dy = dyL * 0.7 + dyH * 0.3;
    vec3 perturbedNormal = normalize(vec3(-dx, -dy, 1.0));

    // 暂写：把扰动法线编码输出
    outColor = vertexColor;  // 基础水色，后面会混反射和折射
    outNormal = vec4(perturbedNormal * 0.5 + 0.5, 1.0);
    outMaterial = vec4(1.0, 0.0, 0.0, 1.0);
}
```

注意最后两行我暂时把 `outColor` 设成了 `vertexColor`（水的基础颜色）。等我们做完 Fresnel（第 6.3 节）和反射（第 6.4 节），这里会替换成真正的反射/折射混合。

![双层水波法线效果：低频大涌浪叠加高频细涟漪，水面呈现自然的波光粼粼](/images/screenshots/ch6_2_waves.png)

> 波浪法线不是贴图直接给的颜色——是贴图亮度差经过差分运算后构造出来的新向量。

---

## 本章要点

- 法线贴图扰动比顶点动画更适合做水面波浪——细腻、廉价、自然。
- 波浪法线的核心操作：差分采样噪声图 → `(-dx, -dy, 1.0)` → normalize。
- 单层噪声不够——低频管大涌浪，高频管细涟漪，双层不同速度方向叠加才有水感。
- `frameTimeCounter` 是 Iris 提供的全局时钟 uniform，把它加进 UV 偏移就能让波浪随时间流动。
- 低频和高频层的 UV 缩放倍数、移动速度、方向角要不一样，否则波浪看起来像流水线传送带。

下一节：[6.3 — Fresnel 效应：正看透、斜看反](/06-water/03-fresnel/)
