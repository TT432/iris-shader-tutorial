---
title: 1.3 — uniform：GPU 的输入参数
description: 掌握 Iris 提供的各种 uniform 变量——时间、分辨率、相机位置——让着色器"活"起来
---

这一节我们会讲解：

- Iris 给你提供了哪些"免费"的 uniform 变量
- 时间类 uniform：让效果动起来
- 分辨率类 uniform：适配任意窗口大小
- 相机类 uniform：知道玩家在哪、看哪
- 实战：把灰度滤镜升级成"随时间呼吸"的动态效果

好吧，现在是时候让你的着色器脱离"静态滤镜"的层次了。

---

## 回顾：uniform 是什么？

在 1.1 节，我们见到了 `uniform sampler2D colortex0`——一个告诉 GPU"从哪张纹理取色"的 uniform。

`uniform` 的意思是：**在整个着色器执行期间，这个值不会变。** 200 万个像素看到的是同一个 `colortex0`。

但 `colortex0` 不是唯一的 uniform。Iris 为你提供了**几十个**预定义的 uniform 变量，涵盖了时间、屏幕尺寸、相机位置、世界状态……就像 Minecraft 给你开了一扇窗，让你可以伸手进去拿各种"当前世界的状态"。

你不需要自己计算它们——你只需要**声明**它们，Iris 会自动帮你填值。

---

## 时间类 uniform：让你的世界动起来

最常用的 uniform 之一是 `frameTimeCounter`：

```glsl
uniform float frameTimeCounter;
```

把它加到你的 `composite.fsh` 里（放在 `void main()` 之前），你就可以在着色器中使用它了。

`frameTimeCounter` 的值是**从游戏启动开始经过的秒数**。它是一个单调递增的浮点数：0.00, 0.01, 0.02……60.0, 61.0……3600.0（一小时）……

因为它一直在变，所以你用它做任何计算——颜色、位置、亮度——都会产生**随时间变化**的效果。在动画和图形学里，这是最简单也最强大的动画来源。

### 让你的画面随时间变色

试试这个：

```glsl
#version 330 compatibility

uniform sampler2D colortex0;
uniform float frameTimeCounter;  // ← 新加的

in vec2 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 color;

void main() {
    color = texture(colortex0, texcoord);

    // 用 sin() 产生在 0~1 之间来回振荡的值
    float wave = sin(frameTimeCounter) * 0.5 + 0.5;

    // 根据 wave 的值在灰度和彩色之间混合
    color.rgb = mix(color.rgb, vec3(dot(color.rgb, vec3(0.299, 0.587, 0.114))), wave);
}
```

保存，F3+R。

你的画面会**在彩色和黑白之间来回渐变**。大概 6 秒一个周期（因为 `sin()` 的周期是 2π  6.28 秒）。

### 内心独白：这段代码在干什么？

让我们拆开来看：

```glsl
float wave = sin(frameTimeCounter) * 0.5 + 0.5;
```

`sin(t)` 的输出范围是 `[-1, 1]`。我们想要的是 `[0, 1]`——方便后续做混合。

- `sin(t)` → `[-1, 1]`
- `sin(t) * 0.5` → `[-0.5, 0.5]`
- `sin(t) * 0.5 + 0.5` → `[0, 1]` 

这是一个非常常见的模式。几乎任何时候你需要把一个振荡信号映射到 `[0, 1]`，你都会写 `sin(t) * 0.5 + 0.5`。

```glsl
color.rgb = mix(color.rgb, vec3(dot(color.rgb, vec3(0.299, 0.587, 0.114))), wave);
```

`mix(a, b, t)` 是 GLSL 的线性插值函数。当 `t=0`，结果是 `a`；当 `t=1`，结果是 `b`；当 `t=0.5`，结果是 `a` 和 `b` 各一半。

在这里：
- `a` = 原始彩色画面 `color.rgb`
- `b` = 灰度画面 `vec3(dot(...))`
- `t` = 振荡信号 `wave`

所以 `wave=0` → 彩色，`wave=1` → 灰度，`wave=0.5` → 半灰半彩。

---

## 其他有用的时间类 uniform

| Uniform | 类型 | 含义 |
|---|---|---|
| `frameTimeCounter` | `float` | 游戏启动后的秒数（连续递增） |
| `frameCounter` | `int` | 当前是第几帧（每帧 +1） |
| `worldTime` | `int` | 世界时间（0~24000，0=日出，12000=日落，18000=午夜） |
| `timeAngle` | `float` | 世界时间换算为角度（0~2π） |
| `timeBrightness` | `float` | 天空亮度（1=正午，0=午夜） |

> ⚠️ `timeAngle` 和 `timeBrightness` 并非标准 Iris uniform——它们仅存在于 BSL/Complementary 兼容层（`HardcodedCustomUniforms.java`）中，**不保证在所有光影包中可用**。

`frameTimeCounter` 适合做**平滑动画**（渐变、振荡）。`frameCounter` 适合做**离散效果**（每 N 帧触发一次）。

---

## 屏幕分辨率类 uniform

```glsl
uniform float viewWidth;   // 窗口宽度（像素）
uniform float viewHeight;  // 窗口高度（像素）
uniform float aspectRatio; // 宽高比 = viewWidth / viewHeight
```

这些变量在你需要**知道当前像素在屏幕上的位置**时非常有用。

比如，你想做一个"屏幕中心亮、边缘暗"的暗角效果：

```glsl
// 计算当前像素距离屏幕中心的距离（归一化到 [0, 1]）
vec2 centerOffset = (texcoord - 0.5) * 2.0;  // 映射到 [-1, 1]
float distToCenter = length(centerOffset);     // 到中心的距离

// 距离越远，越暗
float vignette = 1.0 - distToCenter * 0.5;
color.rgb *= vignette;
```

如果你不做任何分辨率适配——比如在 `texcoord.x > 0.5` 的时候做某种效果——那在全屏和窗口模式下效果会不一致。因为你写的是比例（0.5 永远是正中间），所以 `texcoord` 天然就是分辨率无关的。

> 在大多数情况下，**用 `texcoord` 比用 `viewWidth/viewHeight` 更方便**——因为 `texcoord` 已经是归一化坐标了。

---

## 相机与世界类 uniform

| Uniform | 类型 | 含义 |
|---|---|---|
| `cameraPosition` | `vec3` | 相机在世界中的位置 |
| `sunPosition` | `vec3` | 太阳的方向向量 |
| `shadowLightPosition` | `vec3` | 阴影光源的方向 |
| `rainStrength` | `float` | 雨的强度（0=晴天，1=暴雨） |
| `eyeBrightnessSmooth` | `ivec2` | 玩家所在位置的天空光和方块光强度 |
| `isEyeInWater` | `int` | 玩家是否在水下（0=否，1=是） |

这些 uniform 让你可以根据**游戏世界中的实际状态**来改变效果。比如：
- `rainStrength > 0.5` → 增强雾效 → 雨天能见度降低
- `isEyeInWater == 1` → 画面偏蓝 → 模拟水下视觉
- `cameraPosition.y < 0` → 地下 → 关闭天空渲染

---

## 实战：彩虹呼吸屏

让我们把刚学到的组合起来，做一个真正有趣的效果——**屏幕色调随时间在红-绿-蓝之间缓慢旋转。**

```glsl
#version 330 compatibility

uniform sampler2D colortex0;
uniform float frameTimeCounter;

in vec2 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 color;

void main() {
    color = texture(colortex0, texcoord);

    // 三个正弦波，相位各差 2π/3（120°），产生彩虹旋转
    float r = sin(frameTimeCounter * 0.5) * 0.5 + 0.5;
    float g = sin(frameTimeCounter * 0.5 + 2.094) * 0.5 + 0.5;
    float b = sin(frameTimeCounter * 0.5 + 4.189) * 0.5 + 0.5;

    // 用灰度作为"亮度基底"
    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));

    // 把灰度画面染色
    color.rgb = gray * vec3(r, g, b);
}
```

保存，F3+R。

![彩虹呼吸屏效果：世界以单色调呈现，色调随 sin(frameTimeCounter) 在红绿蓝之间旋转](/images/screenshots/ch1_3_rainbow.gif)

你的世界变成了**单色调但色调在不断旋转**——一会儿偏红、一会儿偏绿、一会儿偏蓝。灰度值越高的地方（比如天空）颜色越明显，灰度值越低的地方（比如暗处）越接近黑色。

这就是着色器编程的核心循环：**声明 uniform → 用数学函数处理 → 输出颜色。** 所有的"高级特效"——Bloom、体积光、色调映射——都是这个循环的变体。

---

## 本章要点

1.  **uniform 是 Iris 给你的"免费数据"**——声明就能用，不需要自己算
2.  **`frameTimeCounter`** = 时间引擎——一切动画的基础
3.  **`sin(t) * 0.5 + 0.5`** = 最常用的振荡映射——把 [-1,1] 变成 [0,1]
4.  **`mix(a, b, t)`** = 线性插值——在两种颜色/效果之间平滑过渡
5.  **`viewWidth/viewHeight`** = 屏幕尺寸——大部分时候用 `texcoord` 更方便
6.  **世界类 uniform** = 感知游戏状态——下雨、水下、日出日落……

> **这里的要点是：uniform 让你的着色器从"静态滤镜"变成"活的东西"。它能感知时间、感知分辨率、感知玩家的状态——你只需要声明它、然后自由地进行数学创作。**

---

下一节：[1.4 — vertex shader 的秘密：全屏四边形的骗局](/01-composite/04-vertex-shader/)
