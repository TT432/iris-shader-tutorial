---
title: 5.4 — 自定义雾效：让远处的东西慢慢消失在底色里
description: 用指数雾和高度雾替换原版线性雾——在 gbuffers 或 composite 中计算衰减因子，实现有层次的大气透视
---

这一节我们会讲解：

- 原版 Minecraft 的雾为什么"平"——以及为什么你要替换它
- 指数雾公式：$$e^{-d \cdot c}$$ 的直觉——为什么不直接用线性
- 高度雾：低处雾浓、高处雾淡——为什么真实雾气贴着地面
- `blindFactor` 和 `darknessFactor`：Iris 提供的两个现成变量
- 雾要写在哪：gbuffers 逐块做 vs composite 全屏做
- 雾色从哪来：跟天空色挂钩才能让远景自然融入

好吧，你现在有了漂亮的天空、闪烁的星星、穿过树叶的光束。但远处的那座山呢？它还是干干净净地站在 100 米外，清晰得像 5 米外。现实里，远处的东西应该发灰、发蓝，细节消失在空气里。这个现象叫大气透视，在游戏里叫雾。

原版 Minecraft 是有雾的——线性雾，远=灰白，近=无色。它的问题是：太机械了。50 米全清，80 米全灰，中间随便混一混。我们要做一个有层次感的雾：近处干净，中距离开始发白（指数），低处浓高处淡（高度）。

---

## 雾的直觉：不是在"加"，而是在"混"

内心独白走一遍：雾其实不是在画面上面叠一层白——如果是叠加，雾里透出来的颜色就永远是对比度正常的原色加一个白底。看起来当然不对。

雾是混合。远处的东西发灰，不是因为上面多盖了一层白，而是因为物体本身的颜色被"稀释"进了大气的颜色里。正确做法是：

$$
\text{finalColor} = \operatorname{mix}(\text{fogColor}, \text{sceneColor}, \text{factor})
$$

其中 `factor = 1.0` 表示完全清晰（看不到雾），`factor = 0.0` 表示完全被雾遮住（全雾色）。而 `factor` 由两个东西决定：距离和高度。

> 雾的本质是 mix(sceneColor, fogColor, factor)。加上去是错的，混进去是对的。

---

## 指数雾：距离驱动的透明度衰减

原版的线性雾公式大致是：

$$
factor = \frac{\text{far} - \text{distance}}{\text{far} - \text{near}}
$$

它在近处到远处均匀地衰减，像一条直线。问题：真实大气对光的衰减是指数的。每穿过一段等厚的空气，亮度乘以一个固定的衰减因子。穿两段就乘两次，穿三段乘三次——这天然就是指数行为。

指数雾的核心公式：

$$
factor = e^{-d \cdot c}
$$

其中 $$d$$ 是距离，$$c$$ 是雾密度。如果 $$d = 0$$，`factor = 1`，完全透明，没有雾。如果 $$d$$ 很大但 $$c$$ 很小（薄雾），因子慢慢降低。如果 $$c$$ 很大（浓雾），因子很快降到 0。

还有平方指数雾——衰减更快：

$$
factor = e^{-(d \cdot c)^2}
$$

它让近处和中距离的变化更柔和，但到一定距离后"啪"一下就全没了。这两种各有用途：指数雾适合一般的远景淡出，平方指数雾适合营造"前方是一堵雾墙"的压迫感。

在 gbuffers 里（比如 `gbuffers_terrain.fsh`），你需要从深度重建距离。如果你已经有世界空间坐标（从 G-Buffer 重建的），直接用 `length(position)` 就行。

```glsl
// gbuffers_terrain.fsh 中的雾计算片段
uniform float fogDensity;  // Iris 提供的雾密度参数

// depth 是从深度缓冲读取或传递的
float dist = length(viewPos);  // 眼睛到像素的距离

float fogFactor = exp(-dist * fogDensity);
// 或平方版：float fogFactor = exp(-pow(dist * fogDensity, 2.0));

vec3 fogColor = vec3(0.7, 0.8, 1.0);  // 淡蓝白雾色

outColor.rgb = mix(fogColor, outColor.rgb, fogFactor);
```

![指数雾效果：近处清晰，中距开始变淡，远处融入淡蓝天际](/images/screenshots/ch5_4_fog.png)

---

## 高度雾：低处有雾，高处没雾

纯距离驱动的雾有一个致命缺陷：你站在山巅，山脚完全被雾裹住了，蓝天白云清清楚楚——真实。但反过来看，你站在山脚往上看，山顶应该清晰可见——而纯指数雾会让山顶也发白，因为距离不够就判断它有雾。

真实雾贴着地面：低处浓，高处淡。这是因为雾气里的水珠密度随高度指数下降。

高度雾在距离衰减的基础上乘一个高度惩罚：

$$
factor = e^{-d \cdot c \cdot e^{-h \cdot h\_falloff}}
$$

其中 $$h$$ 是像素的世界 Y 坐标（高度），`h_falloff` 控制雾在什么高度开始散掉。

翻译成 GLSL：

```glsl
// worldPos 是重建的世界空间坐标，或从 gbuffers 传来的
float height = worldPos.y;

// 高度衰减：越低越有雾，越高越没雾
float heightAttenuation = exp(-height * 0.02);  // 0.02 是高度衰减速率的经验值

float fogFactor = exp(-dist * fogDensity * heightAttenuation);
```

内心独白一下：如果 `height = 64`（地面），`heightAttenuation` 接近某个值，雾正常出现。如果 `height = 200`（山顶），`exp(-200*0.02) = exp(-4) ≈ 0.018`——高度衰减接近 0，`fogFactor ≈ 1`，雾几乎完全消失。山脚有雾，山顶清爽。

你试一下调 `0.02`。改成 `0.01` 的话，高度衰减更温和，连山顶都会有些许雾；改成 `0.05` 的话，雾 30 米以上就几乎没了，像个低洼雾洼。这个参数的命名一般叫 fogHeightFalloff，你可以扔进 `shaders.properties` 做滑块，让玩家自己调。

> 高度雾 = 指数雾 × 高度惩罚。两个轴，一个是距离，一个是海拔。

---

## Iris 提供的现成变量：blindFactor 和 darknessFactor

在探索这些变量之前，你需要了解 Minecraft 原版的雾系统——这不是 Iris 的，而是 Minecraft 从 1.18 开始独立使用的雾逻辑。在大型光影包里，大多数作者会自己算雾，这两个变量只用做调试参考。但了解一下没坏处。

如果你在 composite pass（不是 gbuffers）里，有两个方便的东西可以直接用：

```glsl
uniform float blindFactor;   // 失明药水、水下、虚空时的雾强度
uniform float darknessFactor;  // 黑暗效果的程度
```

`blindFactor` 是原版用来控制"这个区域的雾该多浓"的综合因子。它在普通地表时接近 0，在水下和虚空中接近 1。它不会给你指数衰减——它给的是一个乘数，你可以把它乘在你的雾密度上。

`darknessFactor` 和 `blindFactor` 类似，由当前生物群系和环境支配——黑暗效果和亮度调节会改变它。

严格来说，在专业光影包里，这两个变量通常只被当作"应急参考"。大多数光影作者最后还是自己算雾密度和雾颜色——因为原版的因子太粗糙了，不能区分"水底的蓝雾"和"山腰的白雾"。

---

## 雾写在哪：gbuffers vs composite

同样的岔路口，和星星一样。

如果你把雾写在 `gbuffers_terrain.fsh` 里，好处是你这时还拿着世界空间坐标和深度，距离和高度都有现成的变量。缺点是：每个方块单独算雾，天空和水面在各自的 pass 里雾色可能不一致——画面可能开缝。另外，实体（`gbuffers_entities`）里的生物用的是另一个 pass，如果你忘了在实体 pass 里加同一套雾逻辑，半透明的史莱姆在远方会显得异常清楚。

如果你把雾写在 composite pass 里，此时你只有屏幕 UV 和深度缓冲里的深度。深度可以通过 `depthtex0` 取出，再通过 `gbufferProjectionInverse` 重建世界空间坐标，拿到距离和高度。但这里有个硬伤：天空没有深度。在 composite 里你用同一套逻辑处理天空像素时，`depthtex0` 读出来可能没有值，你得手动判断"这是天空像素，雾色等于天空背景色"。

所以，常见的专业做法是：

- gbuffers pass 里算方块雾：占画面 90% 的像素，拿空间坐标方便。
- composite pass 里做全局的色调统一：确保天空、水面、实体在同一个雾色下对齐。
- 如果实体罕见且不重要（比如你只做方块的光影），gbuffers 里写完就算了。

对你现在这个阶段，写进 `gbuffers_terrain.fsh` 最划算。

---

## 雾色从天空来

最后一个但是很重要的事：雾色不能写死。

如果你的天空是深蓝的，雾就不该是纯灰白的——那样远景的山看起来会很怪，好像天空是蓝的但山墙是白的。雾色应该采样自你 5.1 节的天空颜色。简单版：取地平线附近的天空色作为雾色：

```glsl
// 在 gbuffers 里，你可以用天空方向判断雾色
vec3 upDir = normalize(upPosition);
float horizonBlend = abs(dot(normalize(viewPos), upDir));  // 0=水平看，1=垂直看
horizonBlend = smoothstep(0.0, 0.3, horizonBlend);  // 只有接近地平线才取雾色
vec3 fogColor = mix(vec3(0.7, 0.8, 1.0), vec3(0.5, 0.5, 0.6), horizonBlend);
```

或者如果你是进阶玩家，在 gbuffers 里存一张天空色的 uniform（通过 composite 提前算好再传过来）。这一步我们留到管线进阶部分再说。

---

## 本章要点

- 雾是 `mix(fogColor, sceneColor, factor)`，不是叠加，是混合。
- 指数雾 $$e^{-d \cdot c}$$ 比原版线性雾更接近真实大气衰减。
- 高度雾用 $$e^{-h \cdot h\_falloff}$$ 做惩罚项：低处浓，高处淡。
- `blindFactor` 和 `darknessFactor` 是 Iris 的辅助变量，可以乘在自己的雾参数上。
- gbuffers 里做雾有坐标方便但需要分 pass 处理；composite 做能全局统一但天空需要特殊判空。
- 雾色不要写死。和天空色挂钩，地平线找天空地平线色，或者直接采样。

下一节：[5.5 — 实战：动态天空](/05-atmosphere/05-project/)
