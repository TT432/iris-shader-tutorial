---
title: 9.3 — 其他 gbuffers Pass：实体、天气、手持物品与信标
description: gbuffers 不止 terrain——实体渲染、雨雪效果、手持物品、信标光束都在各自的 gbuffers 变体里
---

这一节我们会讲解：

- 为什么这么多东西要分别用不同的 gbuffers pass
- `gbuffers_entities` 如何处理生物和物品实体
- 发光实体 `gbuffers_entities_glowing` 和盔甲闪烁 `gbuffers_armor_glint`
- `gbuffers_weather` 怎样给雨和雪上色
- `gbuffers_hand` 和 `gbuffers_hand_water` 如何独立渲染你手里的东西
- `gbuffers_beaconbeam` 怎样处理信标光束

你已经花了大量时间在 `gbuffers_terrain` 上。好吧，这是对的——方块占了你视野的绝大多数。但光影不只画方块。Minecraft 还有生物、玩家、盔甲、雨、你手里捏着的剑、一束直冲云霄的信标光。它们不是`gbuffers_terrain`能处理的，因为它们的几何结构、渲染规则、透明度需求完全不同。

> 一种物体 = 一个 gbuffers pass。这不是冗余，是渲染管线需要给每种物体独立的着色逻辑。

![gbuffers Pass 总览：地形、实体、天气、手持物品、信标光束各自有独立的渲染 pass](/images/screenshots/ch9_3_gbuffers_overview.png)

内心独白：如果你试着把所有东西塞进一个 `gbuffers_terrain.fsh`，你会发现自己写了一堆 `if` 判断——如果这个三角形是实体，算光照的方法跟方块不一样；如果是发光实体，又不一样……你很快会写出一个无法维护的怪物。这就是为什么 Iris 把 pass 分开了。

---

## gbuffers_entities：实体渲染

这是生物（僵尸、猪、玩家模型）和物品实体（掉在地上的钻石剑、扔出的鸡蛋）的主入口。从着色器的角度看，`gbuffers_entities` 和 `gbuffers_terrain` 的结构非常像——它也有 `.vsh` 和 `.fsh`，也拿到 `gl_Vertex`、`gl_Normal`、`gl_MultiTexCoord0` 等属性。

但有一个关键区别：实体的光照通常和方块不一样。你大概不会想让僵尸的脸跟石头的侧面用同样的法线光——那会让僵尸看起来像雕塑。所以很多光影会在 `gbuffers_entities.fsh` 里单独设计一套针对生物的漫反射或 PBR。

顺便说一下，第 2 章的 `gbuffers_terrain.fsh` 用的 `in vec2 lmcoord` 和 `uniform sampler2D lightmap` 在这里也是同一个套路。实体也需要拿到 Minecraft 的 baked light，否则站在火把旁边的僵尸和在暗处的僵尸看起来会一样亮——那可不行。

> 实体跟方块的着色逻辑可以完全分开，这是光影深度的一个标志。

---

## gbuffers_entities_glowing 和 gbuffers_armor_glint

这两个 pass 名字里带"特殊效果"。

`gbuffers_entities_glowing` 处理被"发光"状态效果标记的实体——就是那种在黑暗中依然轮廓分明的白色描边效果。在 gbuffers 阶段，你不需要额外画一层描边；你只需要确保发光实体输出一个独立的、不受环境光影响的颜色。然后后面的 composite pass 可以从 G-Buffer 里把它提出来做 Bloom 或其他处理。

`gbuffers_armor_glint` 是盔甲的闪光效果。你知道穿钻石甲或附魔甲时表面会有一道紫光来回滑过——这不是一个"调色"效果，而是一个真实的纹理叠加在 armour texture 上。`gbuffers_armor_glint` 可以拿到盔甲本身的贴图，以及那道闪光的条纹，单独控制它的节奏和颜色偏移。

内心独白：那你能不能直接在主 `gbuffers_entities` 里做这些？技术上可以——但分开来，你就能在不同 pass 的控制流里写干净的独立逻辑，不用每次加效果都要在主 pass 里塞更多 `if`。

---

## gbuffers_weather：雨和雪

下雨和下雪在 Minecraft 里是两种完全不同的视觉现象，但它们在 `gbuffers_weather` 里统一处理。

雨是半透明的竖条纹：深度浅、速度快、织成一片幕帘。雪是缓慢飘落的白色小片：速度慢、有旋转、积聚在地面。着色器里区分它们的关键是**生物群系温度**和**海拔高度**。

```glsl
uniform float rainStrength;
uniform float wetness;

in float isSnow;       // 从 vsh 传下来的标记
in vec2 weatherCoord;  // 雨/雪的 UV

if (isSnow > 0.5) {
    // 雪：白色、慢速、大颗粒
    float snowflake = texture(noisetex, weatherCoord).r;
    color.rgb = mix(albedo.rgb, vec3(1.0), snowflake * rainStrength);
} else {
    // 雨：半透明暗色条纹、降低天空亮度
    float raindrop = texture(noisetex, weatherCoord).r;
    color.rgb *= 1.0 - raindrop * rainStrength * 0.3;
}
```

`rainStrength` 是 Iris 给的 uniform，0 是没有雨、1 是倾盆大雨。`weatherCoord` 通常是基于 `frameTimeCounter` 滚动的 UV，保证雨幕在动。

顺便说一下，BSL 的天气系统比这复杂得多——有雨幕深度模糊、积水反光、雨滴打在方块上的溅射粒子。但作为你自己的光影起点，先用 `rainStrength` 控制透明度、用 `weatherCoord` 控制动画，足够让雨天看起来不像"原版贴图直接翻白"。

---

## gbuffers_hand 和 gbuffers_hand_water

你手里拿的东西——方块、工具、食物——是在一个独立的 pass 里渲染的：`gbuffers_hand`。为什么不是 `gbuffers_entities`？因为手部需要特殊处理。

第一，手离相机非常近，光照处理应该和远处的方块不一样。如果你把环境光遮蔽 (AO) 应用在手部上，你的剑可能会半黑，像被一个无形的箱子罩住。

第二，手持物的渲染顺序也不同。它必须出现在世界几何体之上，但又需要正确的深度，让它在某些角度能被方块遮挡。

而 `gbuffers_hand_water` 更进一步——当你拿着一桶水或一块玻璃时，它是半透明的。半透明意味着：你可以透过手看到后面的方块。标准的 solid gbuffers 不处理 alpha 混合，所以 Iris 单独开了这个 pass。

内心独白：那你可能会问："我是不是每个 pass 都要单独维护一份着色逻辑？"某种意义上是的，但好消息是你可以用 `#include` 把通用函数（光照计算、法线处理、颜色映射）抽到共享文件里，然后在每个 gbuffers pass 里只写差异部分。我们在第 10 章的 BSL 导读里会看到这种做法已经非常成熟了。

---

## gbuffers_beaconbeam：信标光束

信标光束是一个特殊的东西：它是一个向上的光束，但本质上是一个半透明圆柱体。它不是方块、不是实体、不是粒子——它是信标方块周围发射出来的。

在 `gbuffers_beaconbeam` 里，你可以控制光束从底到顶的颜色渐变、透明度衰减，以及是否加一点体积散射让它看起来更像穿透雾气的光柱。有些光影甚至在这里加入噪声偏移，让信标光束微微扭动，像能量在流动。

> 每一种物体的渲染都有它的小脾气。把它们的着色器分开，你不是在偷懒，而是在给未来的自己留一条好走的维护路。

---

## 本章要点

- `gbuffers_entities` 处理所有生物和物品实体，结构和 `gbuffers_terrain` 类似但光照逻辑通常独立。
- `gbuffers_entities_glowing` 处理被"发光"标记的实体，方便后续 Bloom 处理。
- `gbuffers_armor_glint` 控制附魔盔甲的闪光纹理叠加。
- `gbuffers_weather` 统一处理雨和雪，用 `rainStrength` 控制强度、`weatherCoord` 驱动动画。
- `gbuffers_hand` 和 `gbuffers_hand_water` 独立渲染手持物品，解决深度和半透明问题。
- `gbuffers_beaconbeam` 处理信标光柱的颜色渐变和体积效果。
- 不同 gbuffers pass 之间可以用 `#include` 共享光照、法线等通用逻辑。

这里的要点是：当你遇到一个新的渲染对象，先去 Iris 文档里找到它对应哪个 gbuffers pass。你不必一次全部实现，但知道它们存在，你的光影就不会停在"只会画方块"的水平。

下一节：[9.4 — 实战：体积云天空](/09-advanced/04-project/)
