---
title: 1.7 — 实战：可调灰度滑杆
description: 把第 1 章学到的所有知识整合成一个完整的、用户可配置的光影效果
---

这一节我们会讲解：

- 整合 composite、uniform、时间动画、条件编译、滑杆配置——做一个完整的光影功能
- 从"想法"到"可发布效果"的完整开发流程
- 一个自测清单——确保你第 1 章的每个知识点都掌握了

---

## 项目目标

做一个**可由用户调节的"呼吸式灰度"效果**：

- 画面整体偏黑白
- 灰度强度以正弦波形式在用户设定的范围内来回振荡
- 用户可以调节**振荡速度**（滑杆）
- 用户可以调节**灰度强度上限**（滑杆）
- 用户可以用**复选框**完全关闭这个效果

---

## 第一步：确定需要的变量

在写代码之前，先想清楚我们需要什么：

| 变量 | 类型 | 用途 |
|------|------|------|
| 效果开关 | 复选框 | `BREATHING_GRAYSCALE` |
| 振荡速度 | 滑杆 (0.1~3.0, 默认 1.0) | `BREATHING_SPEED` |
| 强度上限 | 滑杆 (0.0~1.0, 默认 0.8) | `BREATHING_STRENGTH` |

---

## 第二步：写 `shaders.properties`

```properties
# ===== 屏幕布局 =====
screen=<empty> <empty> [EFFECTS] <empty> <empty> <profile>

screen.EFFECTS=<empty> <empty> BREATHING_GRAYSCALE BREATHING_SPEED BREATHING_STRENGTH <empty>

# ===== 滑杆定义 =====
sliders=BREATHING_SPEED (0.1, 3.0, 1.0)
sliders=BREATHING_STRENGTH (0.0, 1.0, 0.8)

# ===== 默认值 =====
BREATHING_GRAYSCALE=true
```

---

## 第三步：写着色器代码

```glsl
#version 330 compatibility

// 这些 #define 是 Iris 发现选项的"锚点"——必须存在，
// Iris 会根据 shaders.properties 的值自动替换它们
#define BREATHING_GRAYSCALE 1
#define BREATHING_SPEED 1.0
#define BREATHING_STRENGTH 0.8

uniform sampler2D colortex0;
uniform float frameTimeCounter;

in vec2 texcoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 color;

void main() {
    color = texture(colortex0, texcoord);

    #ifdef BREATHING_GRAYSCALE
        // 计算灰度
        float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));

        // 正弦波：在 0~STRENGTH 之间振荡
        // sin(t) 输出 [-1,1] → *0.5+0.5 变成 [0,1] → *STRENGTH 变成 [0, STRENGTH]
        float wave = (sin(frameTimeCounter * BREATHING_SPEED) * 0.5 + 0.5) * BREATHING_STRENGTH;

        // 混合
        color.rgb = mix(color.rgb, vec3(gray), wave);
    #endif
}
```

---

## 第四步：测试

保存两个文件，F3+R。进入光影包设置界面，你应该看到：

- `BREATHING_GRAYSCALE` 复选框 
- `BREATHING_SPEED` 滑杆（0.1 ~ 3.0）
- `BREATHING_STRENGTH` 滑杆（0.0 ~ 1.0）

试着把速度调到 0.1（极慢），观察画面极其缓慢地在彩色和灰度之间漂移。调到 3.0（快），画面快速颤动。

把强度上限调到 0.3——画面不会完全变灰，只有轻微的"褪色感"。调到 1.0——在振荡高峰时画面完全变灰。

**默认参数下的动态效果**（`SPEED=1.0`, `STRENGTH=0.8`）：

![呼吸灰度动态效果](/images/screenshots/ch1_7_breathing.gif)

**低速 + 低强度**（`SPEED=0.3`, `STRENGTH=0.3`）：几乎察觉不到变化，画面只有微弱的褪色感。

![低速低强度——画面几乎保持原色，灰度呼吸微不可察](/images/screenshots/ch1_7_low.gif)

**高速 + 高强度**（`SPEED=2.0`, `STRENGTH=1.0`）：画面快速在彩色和完全灰度之间振荡。

![高速高强度——画面在彩色和灰度间快速振荡，效果明显](/images/screenshots/ch1_7_high.gif)

**关闭效果**（取消勾选 `BREATHING_GRAYSCALE`）：画面恢复原版色彩，效果完全消失。

![关闭效果——画面恢复原版，效果完全消失](/images/screenshots/ch1_7_off.png)

---

## 内心独白：从零到完整功能

想想我们走了多远。

在 1.1 节，你连 `uniform` 是什么都不确定。现在你：
- 用 `texture()` 从缓冲区采样
- 用 `dot()` 做数学运算
- 用 `sin()` 和 `frameTimeCounter` 产生动画
- 用 `mix()` 在两个状态之间过渡
- 用 `#ifdef` 做条件编译
- 用 `shaders.properties` 构建用户界面

而所有这些——采样、数学、动画、混合、开关——只需要 3 行真正做事的代码：

```glsl
float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
float wave = (sin(frameTimeCounter * BREATHING_SPEED) * 0.5 + 0.5) * BREATHING_STRENGTH;
color.rgb = mix(color.rgb, vec3(gray), wave);
```

这就是着色器编程的美妙之处：**代码很少，但每行都在做大量的事情**——因为每一行都被 GPU 并行执行了 200 万次。

---

## 第 1 章自测清单

在进入第 2 章（gbuffers——3D 世界的渲染）之前，确保你能做到以下事情：

- [ ] 用 `texture(colortex0, texcoord)` 采集画面
- [ ] 理解 `uniform`（全局常量）和 `in`（逐像素变量）的区别
- [ ] 熟练使用 `dot()`、`mix()`、`sin()` 做基本数学运算
- [ ] 用 `frameTimeCounter` 产生时间驱动的动画
- [ ] 在 `shaders.properties` 里定义复选框和滑杆
- [ ] 用 `#ifdef` 让功能可以通过复选框开关
- [ ] 用滑杆的值（即 `#define` 的数值宏）控制效果强度
- [ ] F3+R 快速重载光影以测试修改

如果你对上面任何一条不确定——回到对应章节再读一遍，改一改代码，看到效果有了直觉再继续。着色器编程**不是靠"理解"推进的——是靠"看到效果"推进的。**

>  **第 1 章完成。** 你已经掌握了 composite pass 的全部基础操作。下一章我们将进入真正的 3D 世界——学习 `gbuffers_terrain`，在那里你会和法线、光照、纹理图集正面交锋。

---

[下一章：第 2 章 — gbuffers：画方块](/02-gbuffers/01-gbuffers-intro/)
