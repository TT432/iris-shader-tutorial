---
title: 10.3 — 兼容性处理
description: 让光影在 Iris、OptiFine、三个显卡厂商、不同 MC 版本上都能活下来——兼容不是一句"我们尽力了"，而是一套有方法论的工程实践
---

这一节我们会讲解：

- `IS_IRIS` 和 `MC_VERSION` 宏——光影如何知道自己跑在哪
- Intel、AMD、NVIDIA 三家的驱动差异，以及怎样写"三套分支"
- `#ifdef` 条件编译做降级——显卡做不到的事，优雅地不做
- Fallback 路径：Tessellation 失败 → POM，SSR 太贵 → 简化反射
- 发布前兼容性测试的最低清单

你已经花了大量时间做效果。但现在有一个更现实的问题：你的光影不是只在自己的电脑上跑。朋友用 Intel 核显，网友用 AMD 老卡，还有人在国外用 OptiFine 而不是 Iris。你的 shader 可能编译通过了自己的 GTX 4090，但换个机器就报 `ERROR: 0:12: 'xxx' : is not supported in this version`。

> 写光影像是在给整个城市送外卖。你不能只做一份菜，你得确保每家每户的灶都能热你的菜。

![兼容性处理：同一光影在 Intel/AMD/NVIDIA 不同显卡和 Iris/OptiFine 加载器上正常运行](/images/screenshots/ch10_3_compat.png)

好吧，我们开始吧。

---

## 你在哪？IS_IRIS 和 MC_VERSION

光影包最基础的自省是回答两个问题："我跑在哪个加载器上？"和"我在哪个 MC 版本上？"

Iris 提供了一个宏 `IS_IRIS`。当光影在 Iris 下加载时，这个宏是定义的；如果在 OptiFine 下，它未定义。

```glsl
#ifdef IS_IRIS
    // Iris 特有的写法：比如 uniform 绑定方式、特定的 pass 支持
    uniform sampler2D colortex3;
#else
    // OptiFine 兼容写法
    uniform sampler2D colortex3;
#endif
```

实际上，大部分 uniform 在 Iris 和 OptiFine 之间是一致或兼容的，但 pass 列表存在差异。比如 Iris 有 `setup` pass（一个 compute-only 的初始化步骤），OptiFine 没有。如果你用了 Iris 独有的特性，你得在 OptiFine 分支里提供替代逻辑。

`MC_VERSION` 是版本检测宏。对 Iris 来说它通常是数值形式，例如 `11800` 代表 1.18。

```glsl
#if MC_VERSION >= 11800
    // 1.18 之后的世界高度扩展了，云层计算需要重新拨高
    #define CLOUD_BASE 600.0
#else
    #define CLOUD_BASE 400.0
#endif
```

内心独白：`MC_VERSION` 不应该被滥用。只有当某个功能严重依赖特定版本的数据格式时才用它。你不能为每个小版本都写独立的 shader——那样你的维护成本会成指数增长。

> IS_IRIS 是加载器检测，MC_VERSION 是环境检测。前者决定你能用什么，后者决定你应该调什么。

---

## 三家的 GPU：三大门派

你用 `glGetString(GL_RENDERER)` 或者看 Iris 日志能知道自己用的什么显卡。但用户在光影菜单里通常看不到这些。你的 shader 需要自己猜测——或者让用户手动切换。

一种常见做法是在 `shaders.properties` 里放一个显卡预设选择器：

```properties
define.GPU_VENDOR = 显卡厂商
GPU_VENDOR = AUTO
```

然后在 shader 里：如果用户选了 `NVIDIA`，就启用一些更高优化的路径；如果选了 `INTEL`，就砍掉所有 tessellation 和 heavy compute shader 的部分。

更自动化的方式是利用驱动行为和已知 bug：

**NVIDIA** 驱动通常对 GLSL 扩展支持最全，tessellation 和 compute shader 都能用。但老卡（GT 710 之类）显存可能不够跑高分辨率 shadow map 和高步数的 Ray Marching。

**AMD** 在 Windows 上的 OpenGL 驱动历史上有不少坑——比如特定的 `discard` 语句触发编译错误，或者纹理格式兼容性问题。常见对策是在 `#ifdef AMD` 分支里用 `clip` 替代 `discard`，避免某些有问题的 GLSL 优化路径。

**Intel 核显** 是兼容性最敏感的。有的 Intel 驱动完全不支持 tessellation；有的不支持 `textureGather`；有的 shadow map 格式在 Intel 上有偏移错误。Intel 分支的原则是：性能最低、效果最保守、永远有 fallback。

```glsl
#ifdef GPU_INTEL
    #define SHADOW_FILTER_SAMPLES 4   // Intel 采样少一些
    #define MAX_RAY_STEPS 32           // 步数砍掉一半
    #define DISABLE_TESSELLATION
#else
    #define SHADOW_FILTER_SAMPLES 16
    #define MAX_RAY_STEPS 64
#endif
```

顺便说一下，这些宏通常不是你手写判断的——你可以把它们做进 `shaders.properties` 里当预设，让用户在光影菜单里选择一个预设档，档位里自动写好了宏组合。这也是 BSL 的做法：提供了几个预设，快速切换画质。

---

## Fallback 路径：优雅降级

这是兼容性里最重要的一课：**如果一个效果不能跑，不要崩溃，要有替代方案**。

比如 Tessellation 如果驱动不支持，`#ifndef DISABLE_TESSELLATION` 整个绕过 `.tcs` / `.tes`，退回到 POM 或普通法线贴图。SSR 如果采样数太高导致帧率崩盘，退回到只对水面做屏幕空间反射，或者关闭 SSR。体积云如果帧率太低，切换到 2D 平面云。

```glsl
#ifdef HIGH_PERFORMANCE_MODE
    // 降级策略：2D 静态云
    float cloud = sample2DCloud(texcoord);
#else
    // 全量体积云 Ray Marching
    vec4 cloud = marchClouds(rayOrigin, rayDir, sunDir, sunColor);
#endif
```

每一条 fallback 路径你都需要有意识地设计。不是在所有效果都出 bug 之后再去补救——而是在你加入一个新效果的时候就要想："如果它跑不动，用户看到什么？"这个问题的答案不应该是一行 GLSL 编译错误。

> Fallback 不是认输——是让用户在低配机器上至少看到"有意为之的简化画面"，而不是一片全黑或全紫的崩溃。

---

## 发布前的兼容性测试清单

你不能要求自己有三台不同显卡的电脑，但你可以做以下事情：

- [ ] 在 Iris 最新版上跑过，检查日志里是否有任何 `WARN` 或 `ERROR`。
- [ ] 用 `Ctrl+D` 开启 Iris 调试模式，确认所有 pass 都正常编译。
- [ ] 在 `shaders.properties` 里提供至少一个低配预设（关掉 tessellation、降采样 shadow、减少 Ray Marching 步数）。
- [ ] 把 `shaders.properties` 里的所有宏在源码里都有一个对应的 `#define` 锚点行——不然 Iris 根本看不到它们。
- [ ] 找至少一位用不同显卡的测试者，让他跑一遍你的光影并截图。
- [ ] 把光影包 zip 发给一个完全不懂 shader 的朋友，让他只做"丢进 shaderpacks 文件夹 + 选择光影"的操作，看他能不能不出错。

---

## 本章要点

- `IS_IRIS` 宏区分 Iris 和 OptiFine 环境；`MC_VERSION` 宏区分游戏版本。
- NVIDIA 兼容性最好；AMD 在 OpenGL 下可能有 `discard`、纹理格式等坑；Intel 核显需要最保守的策略。
- 每个需要可配制的宏必须在 shader 源码中有 `#define 宏名` 锚点行。
- 为每一种重效果准备 fallback 路径：tessellation → POM，SSR → 简化反射，体积云 → 2D 云。
- 发布前至少验证 Iris 日志无报错、调试模式编译通过、提供一个低配预设。

这里的要点是：兼容性是提前设计出来的，不是最后花一个下午修的。你在加效果的时候就在想 fallback，你的光影就能在更多人的电脑上跑起来。

下一节：[10.4 — BSL 源码导读](/10-ship/04-bsl-guide/)
