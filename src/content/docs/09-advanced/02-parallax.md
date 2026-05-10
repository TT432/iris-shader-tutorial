---
title: 9.2 — 视差贴图与曲面细分
description: 用一张高度图假装方块表面有起伏——以及如何把假起伏变成真起伏
---

这一节我们会讲解：

- 为什么普通纹理贴图的方块看起来"面板一样平"
- 视差贴图怎样用高度图偏移纹理坐标，制造深度错觉
- 视差遮蔽贴图 (POM) 的分层步进——让凸起真的挡住后面
- 顶点动画：草叶摆动、树叶震颤——在几何体被画之前就动它
- 曲面细分 (Tessellation) 如何把一个大三角拆成许多小三角，让起伏变成真的

在前面的章节里，你已经用法线贴图和 PBR 材质让方块"看起来有凹凸"。但这终究是光照的诡计——如果你转到一个很斜的角度，你就会发现它还是平的，像一张墙纸贴在一个立方体上。

视差贴图就是来解决这个问题的。它不去骗光照，而是去骗贴图坐标。没错，它的思路非常直接：既然从斜角度看，凸的地方应该挡住凹的地方，那我为什么不故意偏移 `texcoord`，让"凸"处的贴图抽到更远的地方去？

好吧，我们开始吧。

---

## 视差贴图：贴图坐标偏移

先做一个思想实验。想象你站在一张崎岖的石头地板上方，斜眼看着一块凸起的石头。从你的角度看，石头凸起的部分，它的贴图应该挡在石头背后的凹槽贴图之上。但如果你拿的 `texcoord` 永远是平面的，那你永远看不到这种前后关系。

内心独白一场：那我能不能不在平面上采贴图，而是假装把视线射进表面，碰到"高"的地方就停，停在那个高度再去采贴图？

这就是视差贴图的核心。

```glsl
vec3 viewDir = normalize(viewPosition - worldPos);
float height = texture(heightmap, texcoord).r;
vec2 offset = viewDir.xy / viewDir.z * (height * parallaxStrength);
vec2 parallaxTexcoord = texcoord - offset;
vec4 albedo = texture(albedoMap, parallaxTexcoord);
```

最朴素的版本就这么几行。`viewDir.xy / viewDir.z` 是在做透视矫正——越斜的视角，偏移越大。`height` 从高度图读出来，`parallaxStrength` 是你可以调节的强度。读出来的高度越高，贴图坐标就推得越远，模拟"凸起来"的效果。

但这个版本有个很明显的缺陷：如果高度连续变化，偏移就是一次性的大跳，视角太斜时甚至可能跳到完全错误的砖缝上去。这就是为什么我们要聊 POM。

> 普通视差贴图是一刀下去直接偏。POM 是拿小刀一刀一刀刮，刮到哪算哪。

---

## POM：分层步进

视差遮蔽贴图 (Parallax Occlusion Mapping) 的改进在于：它不一次跳到位，而是沿着视线方向一层一层地找。

把高度从 0 到 1 切成很多层。从表面开始，沿视线方向往里走。每一步都问：当前层的高度和表面高度图相比，我"穿进"表面了吗？如果还没穿进去，就继续走。穿过的那一步和前一步之间，做一次线性插值，精确定位到真正的交点。交点处的贴图坐标，就是被遮蔽校正后的。

![视差贴图效果：左侧方块表面平坦如墙纸，右侧通过高度图偏移纹理坐标呈现立体深度感](/images/screenshots/ch9_2_parallax.png)

```glsl
float currentLayer = 0.0;
float layerStep = 1.0 / numLayers;
vec2 deltaTexcoord = viewDir.xy / viewDir.z * parallaxStrength / numLayers;
vec2 currentTexcoord = texcoord;
float currentDepth = 1.0 - texture(heightmap, currentTexcoord).r;

while (currentLayer < currentDepth) {
    currentTexcoord -= deltaTexcoord;
    currentDepth = 1.0 - texture(heightmap, currentTexcoord).r;
    currentLayer += layerStep;
}

// 上一步
vec2 prevTexcoord = currentTexcoord + deltaTexcoord;
float prevDepth = 1.0 - texture(heightmap, prevTexcoord).r;
float afterDepth = currentDepth - currentLayer;
float beforeDepth = prevDepth - (currentLayer - layerStep);
float weight = afterDepth / (afterDepth - beforeDepth);
vec2 finalTexcoord = mix(currentTexcoord, prevTexcoord, weight);
```

内心独白一下：为什么要用 `1.0 - texture(...).r`？因为高度图通常白=最高、黑=最低，而深度是越低越深。我们反转一下，让"低"对应"还没穿进去"，"高"对应"已经穿过表面了"。这样 `currentDepth > currentLayer` 就自然表示"我还在表面上面，没穿进去"。

顺便说一下，`numLayers` 是你调节性能和质量的旋钮。层数太少，会看到一层一层的条纹；层数太多，shader 跑不动。通常 8~16 层在方块尺度上效果不错，32 层以上用于近处特写。

> POM 是"在贴图里走路"——从表面出发，沿视线方向一步一步踩，直到踩进贴图的高度里。

---

## 顶点动画：在 vsh 里动起来

贴图的深浅是一个维度，几何体本身的移动是另一个维度。你在第 2 章已经知道，`gbuffers_terrain.vsh` 拿得到 `gl_Vertex`。如果你在顶点着色器里改 `gl_Vertex`，整个三角形就会移动。

草叶的摆动就是这么做出来的。在 `.vsh` 里，用 `frameTimeCounter` 和一些噪声对顶点的 X 或 Z 分量做小幅度偏移：

```glsl
float wave = sin(gl_Vertex.x * 0.5 + frameTimeCounter * 2.0)
           * sin(gl_Vertex.z * 0.5 + frameTimeCounter * 1.7)
           * 0.05;
vec4 displaced = gl_Vertex;
displaced.x += wave;
gl_Position = gl_ModelViewProjectionMatrix * displaced;
```

注意 `gl_Vertex.y` 不动，只动水平方向，模拟风吹草地的感觉。不同植物可以有不同的频率和振幅——高的草摆得大，矮的花几乎不动。BSL 的 `lib/vertex/waving.glsl` 就为不同方块定义了不同的摆动函数。

树叶震颤是类似的想法，只是频率更高、振幅更小——像哆哆嗦嗦的抖动，而不是大弧度的摇摆。

还有一个比较特殊的用法叫**世界曲率**：把远方的地平线微微向下弯，模拟地球曲面。这当然不是物理上真实的，但在 Minecraft 这种视距有限的游戏里，它能增加一点"世界是圆的"感觉。

> 顶点动画不需要在 fsh 里做什么——在画图之前，圆圈已经动了。这就是 vsh 的魔力。

---

## 曲面细分 (Tessellation)：假变真的终极武器

前面讲的都是视觉欺骗。POM 是靠贴图假装有几何，顶点动画是靠已有的顶点做偏移。但如果方块真的需要更多三角形呢？

曲面细分就是为此设计的。Iris 支持 `.tcs`（Tessellation Control Shader，曲面细分控制着色器）和 `.tes`（Tessellation Evaluation Shader，曲面细分评估着色器）。它们运行在顶点着色器之后、片元着色器之前，把一个输入三角形（或四边形）拆成许多小的子三角形。

你可以在一个细分评估着色器里真正地升高顶点：

```glsl
// .tes 文件的片段示意
layout(quads) in;
void main() {
    vec4 pos = mix(
        mix(gl_in[0].gl_Position, gl_in[1].gl_Position, gl_TessCoord.x),
        mix(gl_in[2].gl_Position, gl_in[3].gl_Position, gl_TessCoord.x),
        gl_TessCoord.y
    );
    float height = texture(heightmap, texcoord).r;
    pos += vec4(normal * height * displacementScale, 0.0);
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * pos;
}
```

内心独白一下：这跟前面对比有什么不同？POM 在 fsh 里骗像素，"看起来"有凸起，但阴影和高光还是在同一个平面上。Tessellation 是真正地升高了顶点，阴影 shadow map 会捕捉到它，SSAO 会遮蔽它，其他物体的反射也能看到它。

但代价也很大——三角形数量可能增加几十倍。而且不是所有显卡驱动都喜欢 tessellation，尤其是较旧的 Intel 核显。这是为什么大多数光影把 tessellation 放在实验性功能里。

> POM 是 fsh 里的障眼法，Tessellation 是几何体级的手术。一个骗眼睛，一个骗整个世界。

---

## 本章要点

- 普通视差贴图通过视线方向和高度图偏移 `texcoord`，让斜角度看时产生凸起错觉。
- POM 沿视线方向分层步进，在高度图中找到真正的交点，支持自遮蔽效果。
- 层数太少会出现条纹，层数太多影响性能；8~32 层是常见选择，取决于距离和视角。
- 顶点动画在 `.vsh` 中修改 `gl_Vertex` 位置，常用于草摆、叶颤等环境动画。
- 曲面细分 (`.tcs`/`.tes`) 将三角形拆分为更多子三角形，实现真正的几何位移，但开销大，兼容性有限。
- 选择方案时先考虑 POM（开销低），再考虑 Tessellation（开销高但真实）。

这里的要点是：深度感是渲染里最昂贵的东西之一。POM 用少量 shader 指令换来大量视觉深度，是你工具箱里非常高性价比的一件。

下一节：[9.3 — 其他 gbuffers Pass](/09-advanced/03-other-gbuffers/)
