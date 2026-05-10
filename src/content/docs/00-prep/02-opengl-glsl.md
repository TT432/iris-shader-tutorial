---
title: 0.2 — OpenGL 与 GLSL：MC 的渲染语言
description: 理解 Minecraft 底层的图形 API、GLSL 语言的版本简史，以及为什么我们选择 version 330
---

这一节我们会讲解：

- OpenGL 到底是什么——它不是软件，而是一本"菜谱"
- GLSL 和 C 的亲缘关系——以及它专门为图形做的扩展
- Minecraft 的 GLSL 版本简史——从史前时代到现代
- 为什么我们选择 `#version 330`——以及什么时候你不能用它

好吧，我们开始吧。

---

## OpenGL 不是软件

这是一个常见的误解。很多人在第一次听说 OpenGL 时以为它是一个程序、一个库、或者一个驱动程序。你可以"安装" OpenGL 吗？不能。

OpenGL 是一本**说明书**。

想象一下：你去一家餐厅，坐下，对服务员说："给我来一份宫保鸡丁。"

服务员不需要知道你的厨房是谁家的、用的是煤气还是电磁炉、厨师是四川人还是广东人。只要按照菜谱——鸡丁切多大、花生什么时候放、酱油和醋的比例是多少——做出来的东西就应该叫"宫保鸡丁"。

OpenGL 就是这本菜谱。它定义了一系列"如果你想要画一个三角形，应该怎么告诉 GPU"的规则。至于 GPU 是 NVIDIA 的、AMD 的还是 Intel 的——那是厨房的事。每个硬件厂商负责按照 OpenGL 的菜谱来实现自己的"厨房"（也就是驱动程序）。

这就是为什么你能在完全不同的显卡上运行同一个 Minecraft 光影包——因为不管底层硬件是什么，大家都遵循同一本菜谱。

> **OpenGL 不是软件。它是一个规范（specification）——一本描述"如何让 GPU 画东西"的说明书。硬件厂商负责实现它。**

---

## GLSL：OpenGL 的"方言"

如果 OpenGL 是菜谱，那 GLSL（OpenGL Shading Language）就是写菜谱用的语言。

GLSL 的语法和 C 语言非常像——如果你会写 C，看 GLSL 代码时会有一种"这好像是 C 但又有一些奇怪的词"的感觉。事实上，GLSL 就是基于 C 的，但它加入了很多专门为图形计算设计的东西。

比如：

```glsl
vec3 color = vec3(1.0, 0.0, 0.0);  // 一个三维向量——存 RGB
vec4 position = vec4(x, y, z, 1.0); // 一个四维向量——存齐次坐标
mat4 transform;                       // 一个 4×4 矩阵——做空间变换

float brightness = dot(normal, lightDirection); // 点积——算光照
vec3 reflected = reflect(viewDir, normal);      // 反射——算镜面高光
```

在普通的 C 语言里，你要做向量运算得自己写循环或者调库。在 GLSL 里，`vec3`、`mat4`、`dot()`、`normalize()` 这些都是**内置的**——因为图形编程的核心就是向量和矩阵运算。如果每次算个点积都要写三行，那着色器会变得又臭又长。

顺便说一下：如果你觉得"向量"这个词很抽象——别怕。一个 `vec3` 在 Minecraft 里可能就是"草方块的绿色"（RGB）、或者"太阳光的方向"（XYZ）、或者"这个表面的朝向"（法线）。它只是把三个数字打包在一起，方便你同时操作。

---

## Minecraft 的 GLSL 进化史

Minecraft 已经 17 岁了（2009 年发布）。在这 17 年里，它用的 OpenGL 版本经历了三次重大变化。这个历史对你的光影开发有直接影响——因为你写的 GLSL 代码必须匹配 Minecraft 用的 OpenGL 版本。

### 远古时代：OpenGL 2.0 + GLSL 120

在 Minecraft 1.16 及以前的版本中，Minecraft 使用的是 OpenGL 2.0，对应的 GLSL 版本是 120。这个版本的 GLSL 语法非常古老，充满了现在已经废弃的写法：

```glsl
// GLSL 120——史前风格
varying vec2 texcoord;      // 用 varying 传数据
uniform sampler2D texture;

void main() {
    gl_FragColor = texture2D(texture, texcoord); // 用内置变量输出
}
```

看到那些 `varying`、`gl_FragColor`、`texture2D` 了吗？这些都是 GLSL 120 的遗迹。如果你现在在网上搜到一些老的 Minecraft 着色器教程，里面全是这种写法——赶紧关掉。那是给你爸爸那辈的光影开发者看的。

### 过渡期：OpenGL 3.2 + GLSL 150

Minecraft 1.17 是个分水岭。Mojang 终于把底层渲染引擎从 OpenGL 2.0 升级到了 OpenGL 3.2，对应的 GLSL 版本是 150。这是一个巨大的飞跃——OpenGL 3.2 引入了"核心模式"（core profile），移除了大量陈旧的功能。

不过这个版本在我们的教程里不会用到。它只是历史中的一个中转站。

### 现代：GLSL 330（我们的选择）

Iris 和 OptiFine 作为光影加载器，允许你使用**高于 Minecraft 原生版本**的 GLSL。只要你的显卡支持，你就可以用更新的版本。

我们选择 `#version 330`（对应 OpenGL 3.3），原因有三：

1. **任何近 10 年生产的电脑都支持。** OpenGL 3.3 要求的最低硬件是"DirectX 10 级别"——也就是 2008 年以后的显卡。除非你在博物馆里玩 Minecraft，否则都能跑。

2. **语法干净。** 330 版本使用 `in`/`out` 代替老式的 `varying`，用 `texture()` 代替 `texture2D()`——这些是现代 GLSL 的标准写法。

3. **Iris 官方教程用的也是 330。** 跟着主流走，查资料、问问题都方便。

看看 330 版本的代码长什么样：

```glsl
// GLSL 330——干净、现代
#version 330 compatibility

uniform sampler2D colortex0;

in vec2 texcoord;  // 从顶点着色器接收数据

layout(location = 0) out vec4 color;  // 输出到 colortex0

void main() {
    color = texture(colortex0, texcoord);  // 注意：没有 '2D' 后缀
}
```

看到区别了吗？`varying` → `in`，`gl_FragColor` → 自定义 `out` 变量，`texture2D()` → `texture()`。写法更统一，更"像现代语言"。

注意第一行的 `compatibility` 关键字。它告诉 GLSL 编译器："我知道我在用 330 的新语法，但请保留一些旧版的功能，因为 Minecraft 的渲染管线需要它们。" 如果你不加 `compatibility`，某些 Minecraft 特有的宏（比如 `gl_TextureMatrix`）可能会不可用。

>  **始终使用 `#version 330 compatibility`，不要只用 `#version 330 core`。** 这是 Minecraft 光影开发中最常见的"莫名其妙编译不过"的原因之一。

---

## macOS 用户注意

如果你用的是 Mac，有一件事你需要提前知道：Apple 已经停止更新 macOS 上的 OpenGL 驱动了。最新的官方 macOS 只支持到 OpenGL 4.1（2010 年的标准），而且对某些高级特性（比如 compute shader）的支持不完整。

这意味着：
- `#version 330` 仍然可以正常使用
- 但如果你在教程后面看到我们用 compute shader（`.csh` 文件），在你的 Mac 上可能无法运行
- 这不是你的问题，是 Apple 的问题

如果你用的是 Windows 或 Linux——不用担心，一切正常。

---

## GLSL 和 C 的关键区别

如果你已经会 C 语言（或 C++、Java、C#），这里有几点你需要快速适应：

| C 语言 | GLSL |
|--------|------|
| `float x = 3.14f;` | `float x = 3.14;`（没有 `f` 后缀） |
| 需要 `#include <math.h>` 才能用数学函数 | `sin()`, `cos()`, `pow()` 等全部内置 |
| 没有向量类型 | `vec2`, `vec3`, `vec4` 是原生类型 |
| 没有矩阵类型 | `mat2`, `mat3`, `mat4` 是原生类型 |
| `printf()` 调试 | **没有 `printf`。** GPU 不能打印。调试靠颜色输出 |
| `int a = 1; int b = 2; int c = a / b;` → `c = 0` | 同样——整数除法截断，小心！ |
| 循环遍历数组 | 可以循环，但性能极差。尽量用向量操作代替 |

最后一点值得展开说一下——**GPU 上不能 `printf`。** 调试着色器的方式是把你想看的值直接输出为颜色。比如你想知道深度值是多少：

```glsl
float depth = texture(depthtex0, texcoord).r;
color = vec4(vec3(depth), 1.0);  // 把深度值当灰度图输出到屏幕
```

这就是着色器程序员的"断点调试"。很原始，但很有效。我们在第 0.3 节讲环境搭建时会详细讲调试技巧。

---

## 本章要点

| 概念 | 一句话解释 |
|------|-----------|
| OpenGL | 一本"如何让 GPU 画东西"的说明书——不是软件 |
| GLSL | OpenGL 的编程语言——像 C，但专为图形计算设计 |
| `#version 120` | 史前版本，你会在老教程里看到——不要学 |
| `#version 150` | 1.17 的原生版本——过渡产品 |
| `#version 330` | **我们的选择**——现代、干净、兼容性广 |
| `compatibility` | 必须加——保留 Minecraft 需要的老功能 |
| `in` / `out` | 代替老式的 `varying` / `gl_FragColor` |
| 没有 `printf` | 用颜色输出调试——这是 GP​​U 编程的日常 |

> **这里的要点是：OpenGL 是你和 GPU 之间的"合同"——它规定了你能说什么、GPU 必须听懂什么。GLSL 就是你说话的语言。而 `#version 330 compatibility` 是我们这门课选择的"方言"。**

---

下一节：[0.3 — 环境搭建：装好你的工具](/00-prep/03-setup/)
