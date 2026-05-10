---
title: 1.6 — shaders.properties：配置文件与功能开关
description: 学会用 shaders.properties 控制 pass 的启用/禁用，定义用户可见的设置界面
---

这一节我们会讲解：

- `shaders.properties` 的核心语法——两件事：控制管线 + 定义 UI
- `#define` 条件编译——如果 SHADOW 没开启，阴影代码根本不会被编译
- `screen=` 和 `sliders=`——构建用户设置界面
- `profile.*`——给用户预设的配置方案

到目前为止，你的光影都是"硬编码"的——灰度滤镜永远开着，颜色永远按那个频率振荡。但真正的光影包是**可配置的**——用户拖动滑杆调节强度、勾选复选框开关功能。

---

## 第一部分：控制管线

打开 Base-330 的 `shaders/shaders.properties`。先看一个最简单的例子：

```properties
# 如果 SHADOW 宏被定义了，就启用 shadow pass
program.world0/shadow.enabled=SHADOW

# 如果 AO 宏被定义了，就启用 deferred pass
program.world0/deferred.enabled=AO
```

语法是：`program.<维度>/<pass名称>.enabled=<条件>`

- `<维度>`：`world0`（主世界）、`world-1`（下界）、`world1`（末地）
- `<pass名称>`：`shadow`、`deferred`、`composite1`、`composite2`……
- `<条件>`：一个 `#define` 宏的名字——如果这个宏被定义了，pass 就启用

这个条件也可以有逻辑运算：

```properties
# 只有 FXAA 开启 且 不是复古滤镜模式 时才启用
program.world0/composite6.enabled=FXAA && !RETRO_FILTER

# SHADOW 或 SHADOW_COLOR 任一开启
program.world0/shadowcomp.enabled=SHADOW || SHADOW_COLOR
```

---

## 第二部分：`#define` 与条件编译

上面的 `SHADOW`、`AO`、`FXAA` 这些宏是从哪来的？它们有两个来源：

### 来源一：`lib/settings.glsl`（你在代码里手动定义）

```glsl
// lib/settings.glsl
#define SHADOW 1            // 开启阴影
#define AO 1                // 开启环境光遮蔽
//#define MOTION_BLUR 1     // 注释掉 = 关闭运动模糊
```

### 来源二：用户通过 UI 打开的选项（你在 properties 里定义）

当你用 `screen=` 定义了一个复选框，用户勾选它时，Iris 会自动定义一个对应的宏。

> ⚠️ **关键前提**：Iris 通过扫描 shader 源码中的 `#define NAME` 行来**发现**可配置选项（`OptionAnnotatedSource.java`）。如果你只在代码里写 `#ifdef GRAYSCALE` 但从未写 `#define GRAYSCALE`，Iris 就找不到这个选项，`shaders.properties` 里的配置也不会生效。**选项名必须在源码中至少有一个 `#define` 声明作为"锚点"。**

不管宏从哪来，一旦它被定义了，你就可以在着色器代码里用它做条件编译：

```glsl
#ifdef SHADOW
    // 这段代码只有在 SHADOW 被定义时才编译
    float shadow = calculateShadow(coord);
#else
    // 这段代码在 SHADOW 未定义时编译
    float shadow = 1.0;
#endif
```

>  **条件编译不是运行时 `if`。** `#ifdef` 在编译阶段决定代码的去留——未定义的代码块根本不会进入着色器程序，GPU 甚至不知道它存在过。关闭的功能零性能开销。

---

## 第三部分：构建用户界面

现在，让我们给你的灰度滤镜加一个**开关**——一个复选框，用户可以勾选"黑白模式"。

### 第一步：在 `shaders.properties` 里定义选项

```properties
# 定义一个叫 GRAYSCALE 的选项
# 它在"通用"页面下，显示为复选框
screen=GRAYSCALE [GENERAL]

# 把它放在 GENERAL 子页面里
screen.GENERAL=<empty> <empty> GRAYSCALE <empty>

# 设置它的默认值（开启）
GRAYSCALE=true
```

### 第二步：在着色器代码里使用它

```glsl
void main() {
    color = texture(colortex0, texcoord);

    #ifdef GRAYSCALE
    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    color.rgb = vec3(gray);
    #endif
}
```

保存 `shaders.properties` 和 `composite.fsh`，F3+R 重载。

现在进入 **选项 → 视频设置 → 光影 → 光影包设置**——你应该能看到一个"黑白模式"的复选框。勾选/取消勾选它，画面应该在彩色和灰度之间切换。

---

## 第四部分：滑杆——不只是开关

复选框很好，但有时候你需要**连续的强度控制**——比如"灰度强度 0%~100%"。

### 定义滑杆

```properties
# 定义一个叫 GRAYSCALE_STRENGTH 的滑杆选项
# 范围：0.0 ~ 1.0，默认值：0.5
screen=GRAYSCALE_STRENGTH [GENERAL]
screen.GENERAL=<empty> <empty> GRAYSCALE GRAYSCALE_STRENGTH <empty>
sliders=GRAYSCALE_STRENGTH (0.0, 1.0, 0.5)
```

### 在着色器中使用滑杆值

Iris 会自动把滑杆的值注入为一个 `#define` 宏。和复选框一样，**源码中需要有一个 `#define GRAYSCALE_STRENGTH 0.5` 作为锚点**——Iris 会找到这一行，把值替换为用户设定的数值。如果源码中完全没有这个 `#define` 声明，滑杆的值就无法注入。

```glsl
// 这一行是 Iris 的"锚点"——Iris 会找到它并替换值
#define GRAYSCALE_STRENGTH 0.5

void main() {
    color = texture(colortex0, texcoord);

    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    // GRAYSCALE_STRENGTH 是用户在滑杆上设定的值（0.0 ~ 1.0）
    color.rgb = mix(color.rgb, vec3(gray), GRAYSCALE_STRENGTH);
}
```

注意这里**不需要 `#ifdef`**——因为滑杆的值始终存在（要么是用户设定的，要么是默认值）。它不像复选框那样"存在/不存在"。

---

## 第五部分：预设配置（Profile）

如果你的光影有很多选项，让用户一个一个调会很烦。你可以提供**预设**——"一键切换到低配/中配/高配/极致模式"。

```properties
profile.MINIMUM=!SHADOW !AO shadowMapResolution=512
profile.LOW=profile.MINIMUM SHADOW shadowMapResolution=1024
profile.MEDIUM=profile.LOW AO shadowMapResolution=1536
profile.HIGH=profile.MEDIUM shadowMapResolution=2048
profile.ULTRA=profile.HIGH shadowMapResolution=3072
```

`profile.LOW=profile.MINIMUM SHADOW shadowMapResolution=1024` 的意思是：LOW 预设 继承 MINIMUM 预设的所有设置，再加上 SHADOW 开启，阴影分辨率设为 1024。

`!SHADOW` 的意思是：**强制关闭** SHADOW——即使用户之前手动开启了它。

---

## 完整的 `shaders.properties` 示例

把这一节所有的东西拼在一起，你的 `shaders.properties` 大概长这样：

```properties
# ===== 预设配置 =====
profile.LOW=GRAYSCALE GRAYSCALE_STRENGTH(0.0)
profile.HIGH=GRAYSCALE GRAYSCALE_STRENGTH(1.0)

# ===== 屏幕布局 =====
screen=<empty> <empty> [GENERAL] <empty> <empty> <profile>

screen.GENERAL=<empty> <empty> GRAYSCALE GRAYSCALE_STRENGTH <empty>

# ===== 默认值 =====
GRAYSCALE=true
sliders=GRAYSCALE_STRENGTH (0.0, 1.0, 0.5)
```

注意 `[GENERAL]` 带方括号——表示这是一个**可折叠的子页面**。不带方括号的 `GENERAL` 是子页面里的内容。

---

## 内心独白：配置文件看起来好啰嗦

是的。`shaders.properties` 的语法确实有点 hacky——用等号、括号、尖括号来定义 UI 布局，感觉不像是在写配置，更像是在用一种 20 年前的 DSL。

这是 Minecraft 光影生态的历史包袱。OptiFine 时代的规范就这样，Iris 选择兼容它。

但好消息是——**你不需要从零手写。** 开源一份 BSL 或 Complementary 的 `shaders.properties`，把里面的 `screen=` 布局抄过来，改成你自己的选项名就行。等你需要更复杂的 UI（颜色选择器、子页面嵌套、选项联动），查 Iris 文档就行。大部分情况下，复选框加滑杆已经够用了。

---

## 本章要点

1.  **`program.xxx.enabled=MACRO`** = 用宏控制 pass 的开关
2.  **`#ifdef`** = 条件编译——关掉的功能完全不影响性能
3.  **`screen=OPTION_NAME`** = 定义用户可见的设置项
4.  **`sliders=OPTION (min, max, default)`** = 定义滑杆
5.  **`profile.XXX=`** = 预设配置——继承 + 覆盖
6.  **复选框 = `#ifdef`**，**滑杆 = 直接用值**

> **这里的要点是：`shaders.properties` 和 `#define` 是你控制光影行为的两个面板——properties 是面向用户的 UI，`#define` 是面向代码的开关。它们通过宏名连接在一起。**

---

下一节：[1.7 — 实战：可调灰度滑杆](/01-composite/07-project2/)
