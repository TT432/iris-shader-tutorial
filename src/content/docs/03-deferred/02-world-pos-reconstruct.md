---
title: 3.2 — 从 G-Buffer 重建世界坐标
description: 只用屏幕 UV 和深度值，配合 Iris 提供的逆矩阵，一步步反推出像素在三维世界中的真实位置
---

这一节我们会讲解：

- 为什么深度值不是世界坐标——它只是一个"到相机的距离"
- 屏幕 UV → NDC → 裁剪空间 → 视图空间 → 世界空间的正向逆推链条
- `gbufferProjectionInverse` 和 `gbufferModelViewInverse` 这两个矩阵分别做了什么
- 一步步写出坐标重建的 GLSL 代码
- 为什么光有深度不够——没有逆矩阵你就只能停在某种奇怪的"投影后的空间"里
- 一个简单的验证方法：把世界坐标直接当成颜色输出

好吧，我们开始吧。在第 2.2 节和第 2.6 节，你的 `gbuffers_terrain.fsh` 已经写入了颜色、法线和材质。第 3.1 节我们决定了要在 deferred 里算光。现在第一个实际问题出现了：**在 deferred.fsh 这样一个全屏 pass 里，我连这个像素属于哪个位置都不知道，我怎么算光照？**

光照需要知道"光从哪来"和"表面在哪"。太阳方向 `sunPosition` 是 uniform，唾手可得。但"这个表面在世界的哪个坐标"却藏得很深——它不在任何 colortex 里，只和深度纹理有关。

---

## 深度 = 距离，不是坐标

先别急着看公式。你的屏幕上每一个像素都有一个深度值，存在 `depthtex0` 里。你可以在 shader 里这样读它：

```glsl
uniform sampler2D depthtex0;
float depth = texture(depthtex0, texcoord).r;
```

这个 `depth` 是一个 0 到 1 之间的数。接近 0 就是离相机很近，接近 1 就是很远——像天边那座山。但它只是**一个数**，不是三维坐标。要把这一个数还原成 `(x, y, z)` 的世界位置，你需要一条"反推路线"。

内心独白一下：GPU 在画一个方块的时候，是怎么把它的三维位置变成屏幕上的像素位置的？它走了好几步——模型空间 → 世界空间 → 视图空间 → 裁剪空间 → NDC → 屏幕。每一步都是一个矩阵乘法。那如果我们现在手里只有屏幕 UV 和深度，想要反着走回去，该怎么做？答案也很直白：**沿着来时路，反着推回去**。

---

## 反推链条：屏幕 → 世界

让我们一步一步来。每一步都很小，但在一起威力很大。

### 第一步：屏幕 UV → NDC

屏幕坐标系里，`texcoord` 的范围是 `[0, 1]`。NDC（标准化设备坐标）的范围是 `[-1, 1]`。所以这一步就是一个线性映射：

```glsl
vec3 ndc = vec3(texcoord, depth) * 2.0 - 1.0;
```

读出来就是：`0` 变 `-1`，`0.5` 变 `0`，`1` 变 `1`。`x` 和 `y` 在 NDC 里就是屏幕上的位置，`z` 则是标准的深度表达。

注意这里有一个容易拧巴的地方：不同 API 的 NDC `z` 范围不一样。OpenGL 的 NDC `z` 范围是 `[-1, 1]`，所以上面的公式是对的。Iris 使用的是 OpenGL 兼容环境，你可以放心用。

### 第二步：NDC → 裁剪空间

NDC 是裁剪空间除以 `w` 之后的结果，也就是所谓的"透视除法"以后。要反回去，我们需要把 NDC 乘上一个 `w` 分量。但 `w` 已经丢失了——我们不知道它。

这里的技巧是：**先把 NDC 看成裁剪空间坐标，再用投影矩阵的逆矩阵把"投影"这一步反解掉**。所以我们先写成齐次坐标：

```glsl
vec4 clip = vec4(ndc, 1.0);
```

注意：`ndc` 是 `vec3`，`clip` 是 `vec4`。`1.0` 放在 `w` 分量上——这不是随便放的，它对应的是透视除法中的分母位置。做完逆投影以后，真正的 `w` 会被算出来。

### 第三步：裁剪空间 → 视图空间

从裁剪空间回到视图空间，我们需要投影矩阵的逆。Iris 贴心地提供了这个 uniform：

```glsl
uniform mat4 gbufferProjectionInverse;
```

在 Iris 源码的 `MatrixUniforms.java` 里，`gbufferProjectionInverse` 就是由 `gbufferProjection` 矩阵直接求逆得到的。所以它不是什么黑魔法——它是确确实实的数学逆矩阵。

```glsl
vec4 view = gbufferProjectionInverse * clip;
view.xyz /= view.w;  // 去掉齐次坐标的额外尺度
```

### 第四步：视图空间 → 世界空间

从视图空间回到世界空间，需要模型视图矩阵的逆：

```glsl
uniform mat4 gbufferModelViewInverse;
```

同样由 Iris 提供，它是 `gbufferModelView` 的逆矩阵。

```glsl
vec3 world = (gbufferModelViewInverse * vec4(view.xyz, 1.0)).xyz;
```

到这里，`world` 就是这个像素在 Minecraft 世界里的三维坐标了。

```mermaid
flowchart LR
    A["屏幕 UV<br/>texcoord (0~1)"] -->|"×2-1"| B["NDC<br/>x,y,z ∈ [-1,1]"]
    B -->|"变回齐次坐标<br/>vec4(ndc, 1.0)"| C["裁剪空间"]
    C -->|"gbufferProjectionInverse"| D["视图空间<br/>÷ w 去齐次"]
    D -->|"gbufferModelViewInverse"| E["世界空间<br/>worldPos"]
```

---

## 完整 GLSL 代码

把上面的链条拼起来，你会得到这样一段函数：

```glsl
uniform sampler2D depthtex0;
uniform mat4 gbufferProjectionInverse;
uniform mat4 gbufferModelViewInverse;

vec3 worldPosFromDepth(vec2 texcoord) {
    float depth = texture(depthtex0, texcoord).r;

    // 屏幕 UV → NDC
    vec3 ndc = vec3(texcoord, depth) * 2.0 - 1.0;

    // NDC → 裁剪空间 → 视图空间
    vec4 clip = vec4(ndc, 1.0);
    vec4 view = gbufferProjectionInverse * clip;
    view.xyz /= view.w;

    // 视图空间 → 世界空间
    vec3 world = (gbufferModelViewInverse * vec4(view.xyz, 1.0)).xyz;

    return world;
}
```

内心独白：这里有一个小细节你可能注意到了——为什么在视图空间那里要除以 `view.w`？因为 `gbufferProjectionInverse` 解出来的 `view` 坐标还不是"纯净"的三维坐标。它携带了一个齐次 `w` 分量，会把 `xyz` 放大或者缩小。除以 `w` 就像把放大镜取掉，让三维坐标回到"真实尺度"。

---

## 验证：把坐标当颜色

调试坐标重建最简单的方法——跟第 2.7 节法线可视化一模一样——**把算出来的世界坐标直接当颜色输出**：

```glsl
vec3 worldPos = worldPosFromDepth(texcoord);
gl_FragColor = vec4(worldPos * 0.01, 1.0);
```

乘 `0.01` 是因为 Minecraft 世界里坐标可能大到几百几千，直接输出会全部爆白。缩一下之后，你应该看到类似这样的画面：靠近原点 `(0, 0, 0)` 的区域接近黑色，往东（+X）的区域偏红，往上（+Y）偏绿，往南（+Z）偏蓝。

如果画面全黑，很可能是 `depthtex0` 没有被正确采样，或者 `depthtex0` 还没有在任何 pass 里被声明为可读。如果画面完全是乱色，检查你的 `gbufferProjectionInverse` 和 `gbufferModelViewInverse` 是否在 deferred pass 中声明了。

![世界坐标可视化：从原点向外颜色逐渐变亮——R=X, G=Y, B=Z](/images/screenshots/ch3_2_worldpos.png)

---

## 为什么光有深度不够

你可能想："既然深度就能唯一确定屏幕像素，难道不能直接用深度算光照吗？"不能。因为光照公式需要的是**方向**——从表面到光源的方向、从表面到相机的方向。而方向是两点之间的差：`lightDir = lightPos - surfacePos`。如果你没有 `surfacePos`，你连第一行光照公式都写不下去。

深度只是一维的"距离"，逆矩阵是把这一维距离还原成三维坐标的桥。没有这座桥，你的 deferred pass 就是瞎子。

---

## 本章要点

- `depthtex0` 存储的是深度值 `[0, 1]`，不是世界坐标。必须配合逆矩阵才能还原三维位置。
- 重建链条：屏幕 UV → NDC（`×2-1`）→ 裁剪空间（齐次坐标）→ 视图空间（`gbufferProjectionInverse`）→ 世界空间（`gbufferModelViewInverse`）。
- `gbufferProjectionInverse` 和 `gbufferModelViewInverse` 由 Iris 自动提供，分别是投影矩阵和模型视图矩阵的逆。
- 视图空间的 `÷ view.w` 是去掉齐次坐标的缩放，让坐标回到"真实"尺度。
- 验证方法：把世界坐标直接输出为颜色（乘上一个小系数），检查 R=X、G=Y、B=Z 是否方向对上。
- 没有世界坐标就没有光照方向，深度只是单值，不足以支撑任何光照计算。

> 坐标重建是延迟渲染的"脊椎"——它把一张二维屏幕上的像素点，还原成三维世界里的确切位置。没有它，你的 deferred pass 就只能看着 colortex 发呆。

下一节：[3.3 — 实现 Phong 光照模型](/03-deferred/03-phong-lighting/)
