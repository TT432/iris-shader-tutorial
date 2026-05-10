---
title: 9.4 — 实战：体积云天空
description: 把 9.1 节的体积云理论变成能跑的代码——从天空底色到 Ray Marching 到光照散射的完整实现
---

这一节我们会讲解：

- 如何在 `composite.fsh` 里加入体积云系统
- 怎样把 Ray Marching 循环、FBM/Worley 噪声、光照散射串成一条完整的管线
- 参数化云层：用宏控制覆盖率、高度、厚度、步数
- 常见调试陷阱和自测清单

在 9.1 节我们聊了一堆理论，现在是把它们捏成一个能跑的东西的时候了。这次我们的目标很明确：天空底色不变，但在天空上叠一层能穿过去看的立体云。

先别急着写代码。你心里应该先把流程走一遍。天空底色是之前就有的（第 10 章的散射、第 9 章的 sky pass），云是新增的一层。在 composite pass 里，当你判断当前像素属于天空时，先算出原本的天空颜色，再在同样的视线方向上跑 Ray Marching，算出云的密度和颜色，最后把两样东西混合。

> 天空 = 底色 + 云的密度遮罩。密度高的地方透不出天空，密度低的地方云只是薄薄一层白。

![体积云实战效果：体积云叠加在天空底色之上，呈现立体的棉花云质感](/images/screenshots/ch9_4_cloud_project.png)

好吧，我们开始吧。

---

## 第一步：噪声地基

你需要在你的 shader 文件顶部（或者 `lib/noise.glsl` 这类共享文件）准备两个噪声函数。不用担心写得跟论文一样严谨——我们的目标是"视觉上像云"。

```glsl
// 基础 3D 值噪声：用三角函数取小数部分的伪随机
float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x),
            mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
        mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
            mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y),
        f.z
    );
}
```

这一段看起来长，但它做的事很朴素：把 3D 空间切成小格子，每个格子八个角各存一个随机值，然后用三次平滑在格子内部做过渡。这就是值噪声。

从值噪声搭 FBM：

```glsl
float fbm(vec3 p) {
    float value = 0.0;
    float amplitude = 0.6;
    for (int i = 0; i < 5; i++) {
        value += amplitude * noise3D(p);
        p *= 2.2;
        amplitude *= 0.45;
    }
    return value;
}
```

和 2D Worley（这里用 2D 就够了，因为云的细胞结构主要体现在水平面）：

```glsl
float worley2D(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float minDist = 1.0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 point = hash(i + neighbor); // 重用上面的 hash
            vec2 diff = neighbor + point - f;
            float d = dot(diff, diff);
            minDist = min(minDist, d);
        }
    }
    return sqrt(minDist);
}
```

> 噪声函数是云的骨架。骨架搭好了，云才有形态。

---

## 第二步：密度函数

有了噪声，就可以写出 `getCloudDensity(worldPos)` 了。这个函数被 Ray Marching 每一步调用。

```glsl
#define CLOUD_COVERAGE 0.45
#define CLOUD_BASE 500.0
#define CLOUD_THICKNESS 300.0

float getCloudDensity(vec3 pos) {
    // 高度检查
    float heightFrac = (pos.y - CLOUD_BASE) / CLOUD_THICKNESS;
    if (heightFrac < 0.0 || heightFrac > 1.0) return 0.0;

    // 高度梯度：中间厚、上下薄
    float heightGradient = 1.0 - abs(heightFrac - 0.5) * 2.0;
    heightGradient = smoothstep(0.0, 1.0, heightGradient);

    // 水平方向的 FBM + Worley 混合
    vec3 samplePos = pos * 0.003;
    float cloudNoise = fbm(samplePos) - worley2D(samplePos.xz) * 0.25;
    float density = CLOUD_COVERAGE - cloudNoise;
    density = smoothstep(0.0, 0.15, density) * heightGradient;

    return max(density, 0.0);
}
```

内心独白：`smoothstep(0.0, 0.15, density)` 这里为什么偏要加一个平滑？因为不加，云的边界是硬线，看起来像一坨橡皮泥。`smoothstep` 让"有云"到"无云"渐变 15% 的光谱宽度，边缘就有了融化开的感觉。

---

## 第三步：Ray Marching + 光照

```glsl
#define RAY_STEPS 80
#define STEP_SIZE 5.0

// 相函数：朝向太阳的时候散射更强
float phaseHenyeyGreenstein(float cosAngle) {
    float g = 0.3;
    return (1.0 - g * g) / (4.0 * 3.1416 * pow(1.0 + g * g - 2.0 * g * cosAngle, 1.5));
}

vec4 marchClouds(vec3 rayOrigin, vec3 rayDir, vec3 sunDir, vec3 sunColor) {
    // 找到射线与云层的交点
    float t = (CLOUD_BASE - rayOrigin.y) / rayDir.y;
    if (t < 0.0) t = (CLOUD_BASE + CLOUD_THICKNESS - rayOrigin.y) / rayDir.y;
    if (t < 0.0) return vec4(0.0);

    float dist = 0.0;
    float transmittance = 1.0;
    vec3 scatteredLight = vec3(0.0);

    for (int i = 0; i < RAY_STEPS; i++) {
        vec3 samplePos = rayOrigin + rayDir * (t + dist);
        float density = getCloudDensity(samplePos);

        if (density > 0.001) {
            float phase = phaseHenyeyGreenstein(dot(rayDir, sunDir));
            scatteredLight += density * phase * sunColor * transmittance;
            transmittance *= exp(-density * 0.02 * STEP_SIZE);
        }

        dist += STEP_SIZE;
        if (dist > CLOUD_THICKNESS * 2.0) break;
    }

    float cloudAlpha = 1.0 - transmittance;
    return vec4(scatteredLight, cloudAlpha);
}
```

注意 `t = (CLOUD_BASE - rayOrigin.y) / rayDir.y` 这句话。它计算的是"你的视线从当前位置走到云底需要多少步"。如果你站在云上面往下看，`t` 会是负数——这种情况需要另外处理（从云顶往下走）。

---

## 第四步：集成到 composite.fsh

```glsl
// 在 composite.fsh 的主逻辑里
if (isSky) {
    vec3 skyColor = getSkyColor(rayDir, sunDir);
    vec4 cloudResult = marchClouds(
        cameraPosition, rayDir, normalize(sunPosition), sunColor
    );
    color.rgb = mix(skyColor, cloudResult.rgb, cloudResult.a);
}
```

如果你想把云也接进雾系统（比如远处云也该被雾减弱），就在 mix 之后再乘雾。也可以把云计算写进 deferred pass，让后续的 composite 用它做进一步调色。

---

## 自测清单

把这个 `composite.fsh` 丢到 Iris 里跑一下，然后回答这些问题：

- [ ] 白天抬头能看到白色的立体云朵（不只是平面贴图）
- [ ] 飞进云层顶部时视野变白，底部飞出时恢复天空色
- [ ] 朝太阳方向的云边缘比背向太阳的方向更亮
- [ ] 飞得足够快时云不会闪烁（如果闪烁，调大 `RAY_STEPS` 或换更平滑的噪声）
- [ ] 阴天（把 `CLOUD_COVERAGE` 调高）时，云应该几乎连成一片

如果某一条不满足，对照附录里相应的片段排查。最常见的坑是噪声函数有对称性（例如只用 sin 没加 hash），导致云看起来像人工条纹；解决方法是确认你的 hash 函数在 3D 空间里各向统计均匀。

---

## 本章要点

- 体积云系统由三部分构成：噪声（FBM + Worley）、密度函数（高度梯度 + 覆盖率 + smoothstep 软化边缘）、Ray Marching（步进 + 光照散射）。
- 噪声函数不需要完美，但需要各向均匀——`hash` 函数是关键。
- `getCloudDensity` 里要同时考虑水平噪声和垂直高度梯度，否则云是均匀立方块。
- Ray Marching 里的相函数 `phaseHenyeyGreenstein` 让云在朝向太阳的方向更亮。
- 集成时在 composite 判断 `isSky`，云叠在天空底色上，透明度由累积吸收决定。
- 性能靠 `RAY_STEPS` 和 `STEP_SIZE` 号：步数多效果细但慢，步数少有条带但快。

这里的要点是：体积云看似复杂，但它本质上是"一个 Ray Marching 循环 + 一个噪声场 + 一个光照函数"。把这三块分开写好，再拼起来，你就拥有了一片属于自己的天空。

下一章：[10.1 — 维度分离](/10-ship/01-dimensions/)
