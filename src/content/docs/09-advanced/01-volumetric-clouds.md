---
title: 9.1 — 体积云：让天空不再是贴图
description: 用 Ray Marching 在天空穿行，Worley/FBM 噪声生成云朵——从平的贴图到能钻进去的立体云
---

这一节我们会讲解：

- 为什么 2D 云的"单张纹理"不够真实
- Ray Marching 是什么，以及为什么它能在全屏 pass 里跑
- Worley 噪声和 FBM 噪声怎样联手制造云朵的形状
- 云的覆盖率、高度、厚度如何参数化
- 光照散射：云怎样从太阳方向偷光

在第 10 章（天空与大气）我们已经给天空换过颜色了，在第 10 章（体积光与雾）我们也做了光柱和雾气。现在你可能会想：那片贴在天顶上的 2D 平面云，和别人家的立体云，中间到底差了什么？

答案就两个字：体积。2D 云知道位置和颜色，但它不知道"深度"。你飞不起来，也穿不进去。体积云在屏幕上的每个像素都发射一根射线，沿路稠密的地方偏白，稀疏的地方透出天空，于是你能从侧面看到云的厚度、从下面看到云的底部、从上面看到云的顶部。

> 2D 云是一张纸，体积云是一团棉花。棉花里每一丝纤维都有位置。

好吧，我们开始吧。

---

## Ray Marching：在屏幕像素上穿行 3D

内心独白一下：如果我要在 `composite.fsh` 里画云，但我现在只有一个屏幕像素，怎么办？没错，我不能真的在 3D 世界里放一朵云，但我可以假装有一根射线从这个像素射向天空。

这就是 Ray Marching。从相机位置出发，沿着该像素的视线方向，一小步一小步往前走。每走一步，就问："这里有没有云？"如果有，就记下来；如果没有，就继续走。走完了，把所有步子的贡献加起来。

```glsl
vec3 rayOrigin = cameraPosition;
vec3 rayDirection = normalize(worldDirection);
float totalDensity = 0.0;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 samplePoint = rayOrigin + rayDirection * float(i) * stepSize;
    float density = getCloudDensity(samplePoint);
    totalDensity += density * stepSize;
}
```

`MAX_STEPS`（通常 64~128）是一次射线走多少步，`stepSize` 是每步走多远。步数太多会卡，步数太少会出现条带——这是 Ray Marching 永恒的 trade-off。顺便说一下，这里的循环不是那种"你写一万次也没用"的装饰，每次迭代真的在往前走，GPU 也在认真跑。

> Ray Marching 像往三维空间里射箭，每隔一段距离摸一下——摸到东西就记下来，摸不到就继续。

![体积云效果：从地面仰视，立体云层有厚度和光影变化，不再是平面贴图](/images/screenshots/ch9_1_volumetric_clouds.png)

---

## 云的形状：噪声是造云机

`getCloudDensity(samplePoint)` 必须回答一个问题："这个点在不在云里？"

最简单的回答是用 3D 噪声。如果 `noise(p) > 0.5`，就当有云；如果低于，就是空的。但这样造出来的云像一坨硬纸团，没有任何"蓬松感"。我们要更聪明的手法。

**FBM (Fractional Brownian Motion)** 是你在第 10 章可能见过的老面孔：把同一个噪声函数叠加若干层，每一层频率翻倍、振幅减半。低频负责大块形状，高频负责细碎边缘。

```glsl
float fbm(vec3 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 5; i++) {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}
```

**Worley 噪声** 是另一种特殊材料。它不是给出 0 到 1 的随机数，而是对每个采样点，计算"离我最近的随机特征点有多远"。这会产生像细胞壁一样的网状结构。云的底部经常用 Worley 来做扁平的分层效果。

内心独白：那为什么不用纯 FBM，或者纯 Worley？因为如果都用 FBM，云看起来像揉烂的棉絮，没有结构。如果都用 Worley，会像蜂巢或者泡泡浴。现实中的云两者都有——FBM 给出翻滚的体量，Worley 给出底部扁平、边缘丝缕的结构。

```glsl
float cloudShape = fbm(p) - worley(p) * 0.3;
float density = smoothstep(coverage, coverage - 0.2, cloudShape);
```

`smoothstep` 在这里干了一件很关键的事：它在噪声边界做软化。没它，云的边缘会像刀切的一样硬。有它，边缘逐渐消退，像蒸汽消散。

> FBM 控制云的"蓬松度"，Worley 控制云的"细胞感"。两者混在一起，你才得到一朵看起来像云的东西。

---

## 参数化：让云听话

你肯定不会想写死在代码里。云的形态至少有三个参数要暴露出来：

- **覆盖率 (coverage)**：`[0, 1]`，决定天空被云覆盖的比例。0 是全晴，1 是阴天。
- **云底高度 (cloudBase)**：云层从多高开始，通常 500~800 米。
- **厚度 (cloudThickness)**：云层从底到顶有多厚，通常 200~600 米。

还有一个容易被忽略的参数：**高度衰减**。云层底部密、顶部稀。你可以用一条随高度渐变的曲线去乘密度：

```glsl
float heightFactor = 1.0 - abs((samplePoint.y - cloudCenter) / cloudThickness);
float heightDensity = density * smoothstep(0.0, 1.0, heightFactor);
```

云底和云顶不要一刀切。用 `smoothstep` 把边界揉软，否则飞过云层时你会看到一条硬线，而不是渐渐进入雾中。

> 覆盖率、高度、厚度是云的三座大山。参数分开，你才能在下雨天、大晴天、黄昏火烧云之间自由切换。

---

## 光照：云不是发光体

云本身不会发光——它靠散射太阳光来亮。在 Ray Marching 的每一步，你不是只记录密度，还要计算这团云"吃了多少光"。

最朴素的思路：每一步沿射线往前走时，也往太阳方向再额外走一小段，看看沿途有没有云挡住光。但这样做嵌套的 Ray Marching，开销太大了。

于是很多实的做法是走捷径：用 **Beer-Lambert 法则**，也就是光穿过介质时按指数衰减。

$$
light = \exp(-\Sigma \, density \times absorption)
$$

每走一步，沿视线累积光吸收量；同时，把太阳光散射进去：

```glsl
vec3 cloudColor = vec3(0.0);
float accumulatedTransmittance = 1.0;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 samplePoint = rayOrigin + rayDirection * stepDist;
    float density = getCloudDensity(samplePoint);
    if (density > 0.0) {
        float sunScatter = scatteringPhase(dot(rayDirection, sunDirection)) * density;
        cloudColor += sunScatter * sunColor * accumulatedTransmittance * stepDist;
        accumulatedTransmittance *= exp(-density * absorption * stepDist);
    }
    stepDist += stepSize;
}
```

注意 `scatteringPhase` 是一个很重要的小函数。它决定了光"碰到云以后往哪弹"。最简单的版本叫 Henyey-Greenstein 相函数：朝向太阳的那一侧更亮，背向太阳的一侧更暗——也就是人们常说的"云边有金光"。这个效果看 BSL 的 `lib/atmospherics/clouds.glsl` 会更有实感。

> 云的光照公式可以很复杂，但骨架是：走一步 → 问有没有云 → 如果有，散射一点光，吸收一点光 → 继续走。

---

## 在哪里跑

体积云通常是在 `composite.fsh` 或 `deferred.fsh` 里实现的。你在第 10 章的天空底色之上，或者在 deferred pass 的天空位置判断 `sky == true`，然后替换天空像素。

```glsl
if (isSky) {
    vec3 skyColor = getSkyColor(rayDirection);
    vec3 cloudResult = traceClouds(rayOrigin, rayDirection);
    // 混合：云透明度高 → 透出天空；云密度大 → 盖住天空
    color = mix(skyColor, cloudResult, cloudResult.a);
}
```

顺便说一下，如果你在 gbuffers 阶段（`gbuffers_skytextured`）做云，你就需要处理 Alpha 混合的复杂度。在 composite 阶段做，可以用全屏 pass 干净地从天空颜色上叠一层云，代价是失去了真正的深度排序（但云在天空里，这几乎不是问题）。

---

## 本章要点

- 体积云不是 2D 纹理，而是在视线方向上进行 Ray Marching 逐步累积密度。
- Ray Marching 是沿射线逐步采样：步数决定质量，步长决定性能，两者需要平衡。
- FBM 噪声通过频率倍增、振幅减半的叠加产生自然的不规则感；Worley 噪声提供细胞状结构。
- FBM 控制蓬松体量，Worley 控制底部和边缘结构，二者混合才像真云。
- 覆盖率、云底高度、云层厚度建议通过宏或 uniform 参数化，方便调节。
- 光照采用"累积吸收 + 散射"模型，Henyey-Greenstein 相函数让云在朝太阳一侧更亮。
- 体积云通常在 composite 或 deferred pass 中实现，替代天空像素。

这里的要点是：体积云不是魔法，它只是"射线在 3D 噪声场里走路"，但这一招已经够让你从平面天空跳进立体的云层。

下一节：[9.2 — 视差贴图与曲面细分](/09-advanced/02-parallax/)
