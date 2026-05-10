---
title: 0.4 — 光影包解剖：这些文件都是干什么的
description: 逐层拆解一个光影包的目录结构——理解 .vsh、.fsh、shaders.properties、lib/ 等每个组件的角色
---

这一节我们会讲解：

- 一个光影包到底长什么样——从 .zip 到目录结构的全景图
- `.vsh`、`.fsh`、`.csh`——三种着色器文件各自干什么
- `shaders.properties`——配置文件为什么是"大脑"
- `lib/`——专业光影的模块化武器
- 维度文件夹 `world0/world-1/world1`——同一个代码库，三个世界

如果你刚才在 0.3 节下载了 Base-330 模板，打开它的 `shaders/` 文件夹——你可能被里面几十个文件吓到了。别慌。我们一个一个来，你会发现它们**不是一盘散沙，而是一条流水线**。

---

## 全景图：打开你的光影包

一个能用的光影包本质上就是一个改名为 `.zip` 的文件夹。打开 Base-330，你会看到：

```
Base-330.zip
 shaders/                    ← 所有魔法发生的地方
     shaders.properties      ← 配置文件（大脑）
     gbuffers_terrain.vsh    ← 地形方块的顶点着色器
     gbuffers_terrain.fsh    ← 地形方块的片元着色器
     gbuffers_water.vsh
     gbuffers_water.fsh
     gbuffers_entities.vsh
     gbuffers_entities.fsh
     ...（还有几十个）
     composite.vsh
     composite.fsh
     deferred.vsh
     deferred.fsh
     final.vsh
     final.fsh
     shadow.vsh / shadow.fsh  ← Base-330 模板不包含 shadow pass 文件，这些文件仅在你启用阴影功能时才需要添加
```

如果你去看 BSL（一个工业级光影）的 `shaders/` 目录，还要复杂得多：

```
BSL_v10/
 shaders/
     shaders.properties      ← 280+ 行的控制中心
     block.properties        ← 方块 ID 映射表
     item.properties	        ← 物品 ID 映射表
     entity.properties       ← 实体 ID 映射表
     dimension.properties    ← 维度特性配置
     lang/                   ← 多语言翻译
        en_US.lang
     tex/                    ← 嵌入的自定义纹理
        noise.png
        dirt.png
     lib/                    ← 模块化代码库（灵魂所在！）
        settings.glsl
        atmospherics/       ← 云、雾、天空
        color/              ← 色彩管理
        lighting/           ← 光照、AO、阴影
        surface/            ← PBR 材质
        reflections/        ← 反射
        post/               ← 后期特效
        util/               ← 工具函数
     program/                ← 着色器逻辑模板
        composite.glsl
        gbuffers_terrain.glsl
        ...
     world0/                 ← 主世界（Overworld）
        gbuffers_terrain.vsh/.fsh
        composite.vsh/.fsh
        ...（所有 pass）
     world-1/                ← 下界（Nether）
        ...（每个 pass 的维度变体）
     world1/                 ← 末地（The End）
         ...
```

别被吓到。BSL 是经过多年迭代的工业产品。我们今天只看 Base-330——但它已经包含了所有必要的基因。

---

## 三种文件后缀

打开 `shaders/` 之后，你会看到文件后缀只有几种：

| 后缀 | 全称 | 用途 | 类比 |
|------|------|------|------|
| `.vsh` | Vertex Shader | 顶点着色器——处理每个顶点 | 建筑工人：把骨架搭好 |
| `.fsh` | Fragment Shader | 片元着色器——处理每个像素 | 油漆工：给骨架上色 |
| `.csh` | Compute Shader | 计算着色器——通用 GPU 计算 | 后勤：预处理数据（Iris 独有） |
| `.gsh` | Geometry Shader | 几何着色器——修改图元 | （不常用，略过） |
| `.tcs` / `.tes` | Tessellation Shader | 曲面细分——动态增加顶点 | （进阶话题） |

在 Base-330 模板里你会看到大量的 `.vsh` 和 `.fsh` 文件成对出现——比如 `gbuffers_terrain.vsh` 和 `gbuffers_terrain.fsh`。这是因为**每一个渲染步骤（pass）都需要顶点着色器 + 片元着色器**。你在第 1.1 节只改了 `composite.fsh`——`composite.vsh` 其实也在那里，只是你不需要动它。它在后台默默画着一个全屏矩形。我们会在第 1.4 节打开它看看。

---

## `shaders.properties`：光影包的大脑

这是一个纯文本文件，但你把它看作是一个 JSON 配置文件。它控制三件事：

1. **哪些 pass 启用/禁用**——你的光影要不要阴影？要不要体积光？
2. **光影选项 UI**——用户在"光影设置"界面看到什么？
3. **内部管线参数**——shadow map 分辨率、AO 采样数……

举个简单的例子：

```properties
# 开启阴影 pass
program.world0/shadow.enabled=SHADOW

# 设置界面布局
screen=<empty> <empty> LIGHTING MATERIAL ENVIRONMENT

# 把 SHADOW 绑定到一个复选框
screen.LIGHTING=<empty> SHADOW shadowMapResolution shadowDistance
```

Base-330 的 `shaders.properties` 很简洁——可能只有几十行。BSL 的有 280+ 行——但那是因为 BSL 有几十个可调选项。

现在我们不需要深入理解它的语法。你只需要知道：**`shaders.properties` 是你接线的"配电箱"。** 着色器代码是灯泡，properties 是开关——你不开开关，灯泡就不会亮。

---

## 为什么会有 `gbuffers_terrain`、`gbuffers_water`、`gbuffers_entities`……？

你打开 Base-330 看到几十个 `gbuffers_xxx.vsh/.fsh` 文件时，可能会想："为什么不能把所有东西放在一个文件里？"

好问题。答案在于：**Minecraft 里的不同东西需要不同的渲染处理。**

- **`gbuffers_terrain`**：固体方块（草、石头、木板……）。这是最重要的 pass——你视野里 90% 的东西都是它画的。
- **`gbuffers_water`**：水、染色玻璃、任何半透明方块。它需要特殊处理——因为水会反射、折射。
- **`gbuffers_entities`**：生物、掉落物、画。实体和方块的光照模型不同。
- **`gbuffers_skybasic`**：天空底色（没有太阳月亮纹理的天空部分）。
- **`gbuffers_skytextured`**：太阳和月亮。
- **`gbuffers_clouds`**：云。
- **`gbuffers_hand`**：你手上拿的东西。
- **`gbuffers_weather`**：雨和雪。

每一个 gbuffers pass 处理**一类特定的东西**。Iris 会根据当前正在渲染的内容自动选择对应的 pass。如果你不为某个 pass 提供文件——比如觉得原版信标光束就挺好——Iris 会自动使用回退链（fallback chain）：缺了 `gbuffers_beaconbeam.fsh`，就退而用 `gbuffers_textured.fsh`；缺了 `gbuffers_damagedblock.fsh`，就退而用 `gbuffers_terrain.fsh`。

> "那如果我的光影不需要修改其中某个 pass 呢？比如——我觉得原版的信标光束就挺好，不想动它？"

在 Base-330 里，所有这些 gbuffers 文件都写了"什么都不改"的默认代码。这意味着**你的光影可以工作，但画面和原版一模一样**——直到你开始修改其中的某个文件。

---

## `lib/`：专业光影的模块化秘密

在 Base-330 里你找不到 `lib/` 目录——它是空的模板，所有代码都平铺在各个 pass 文件里。

但任何一个工业级光影（BSL、Complementary、AstraLex……）都有 `lib/`。它的作用是什么？

**避免重复代码。**

假设你的光影有 30 个 pass 文件，每个都需要算"这个像素的亮度"。如果你把亮度计算写在每个文件里——你就需要维护 30 份相同的代码。改一次公式→改 30 个文件。

而如果有 `lib/`：

```glsl
// lib/lighting/brightness.glsl
float getBrightness(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}
```

然后在每个需要它的 pass 里：

```glsl
#include "/lib/lighting/brightness.glsl"

void main() {
    float brightness = getBrightness(color.rgb);
    // ...
}
```

一份代码，到处引用。这是所有大型光影包的架构基础。

>  **你现在不需要建 `lib/`。** 前几章的练习都很简单，所有代码写在一个 `.fsh` 文件里就够了。但当你的光影包开始有几百行代码时——你会自然地开始拆模块。BSL 的 `lib/` 是你未来的路标。

---

## `world0/`、`world-1/`、`world1/`：同一个光影，三个世界

这是 OptiFine/Iris 的一个强大特性——你可以**按维度提供不同的着色器代码**。

- `world0/` = 主世界（Overworld）
- `world-1/` = 下界（Nether）
- `world1/` = 末地（The End）

为什么需要这个？因为三个世界的**光照条件完全不同**：

- 主世界：有太阳、月亮、天空光、昼夜循环
- 下界：没有天空光、昏暗的红色基调、岩浆是主要光源
- 末地：永远是夜晚、紫色虚空、末影龙战斗的特殊光照

如果你的光影把主世界的"蓝天"写死了——那进入下界后天空会完全不对劲。维度分离让你可以对三个世界写三套不同的天空代码。

Base-330 **没有**维度文件夹——所有代码放在 `shaders/` 根目录。这也是一种合法做法——你的代码对所有维度一视同仁。只有当你需要差异化时，才需要考虑维度分离。

---

## 内心独白：从"一头雾水"到"这其实很有道理"

我知道你现在脑子里可能是一片乱麻——几十个文件、各种后缀、配置文件、维度分离……"我只是想写个光影，为什么要面对这些？"

让我给你一个不同的视角。

想象一下：你刚拿到一套乐高积木。打开盒子，几千个零件——方的、长的、带孔的、带轮子的——铺了一地。如果你试图"理解每一个零件的用途"，你会疯掉。

但如果你先拿起说明书，翻到第一页——"第一步：拼出底座"——你只需要其中的 8 个零件。其他的暂时和你无关。

Base-330 就是你的乐高套装。**今天你只需要两个零件：`composite.fsh` 和 `composite.vsh`。** 其他所有文件，摆在那里就好——它们是给后面章节准备的。

等你学到了第 2 章（gbuffers），`gbuffers_terrain.fsh` 会变成你的主角。等你学到了第 4 章（阴影），`shadow.fsh` 会登场。每一个文件都在等属于它的那一章。

> **你不需要一次理解所有。你只需要理解你现在在用的。**

---

## 本章要点

1.  **`.vsh`** = 顶点着色器（搭骨架），**`.fsh`** = 片元着色器（上色）
2.  **`shaders.properties`** = 配置文件——控制哪个 pass 启用、用户看到什么 UI
3.  **gbuffers_xxx** 系列 = 场景中不同"类型"的东西各走各的 pass——方块、水、实体、天空各有专属
4.  **`lib/`** = 模块化代码库——避免重复，专业光影标配（但新手不需要立刻用）
5.  **`world0/world-1/world1`** = 维度分离——同一个光影，三个世界可以有不同的代码
6.  **乐高心态**：你现在只需要 `composite.fsh`。其他零件放着别动——它们后面会登场。

> **这里的要点是：光影包的几十个文件不是"复杂"，是"分工"。每一个文件有一个明确的职责。你不需要一次理解全部——你只需要理解你现在在用的那个。**

---

下一节：[0.5 — 渲染管线概览：代码的执行顺序](/00-prep/05-pipeline/)
