---
title: A. GLSL 速查表
description: 常用 GLSL 数据类型、内置函数、Iris 特殊宏
---

## 基本数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `float` | 单精度浮点数 | `float x = 3.14;` |
| `int` | 整数 | `int i = 42;` |
| `bool` | 布尔值 | `bool b = true;` |
| `vec2` | 二维浮点向量 | `vec2 uv = vec2(0.5, 0.5);` |
| `vec3` | 三维浮点向量 (RGB/XYZ) | `vec3 color = vec3(1.0, 0.0, 0.0);` |
| `vec4` | 四维浮点向量 (RGBA/XYZW) | `vec4 col = vec4(1.0, 0.0, 0.0, 1.0);` |
| `ivec2/3/4` | 整数向量 | `ivec2 res = ivec2(1920, 1080);` |
| `mat2/3/4` | 2×2 / 3×3 / 4×4 矩阵 | `mat4 mvp = gl_ModelViewProjectionMatrix;` |
| `sampler2D` | 2D 纹理采样器 | `uniform sampler2D colortex0;` |

## 向量分量访问 (Swizzling)

```glsl
vec4 v = vec4(1.0, 2.0, 3.0, 4.0);
v.rgba  // = vec4(1.0, 2.0, 3.0, 4.0)  颜色语义
v.xyzw  // = vec4(1.0, 2.0, 3.0, 4.0)  空间语义
v.rgb   // = vec3(1.0, 2.0, 3.0)        取前三个
v.xxx   // = vec3(1.0, 1.0, 1.0)        重复
v.bgr   // = vec3(3.0, 2.0, 1.0)        重排
```

## 常用内置函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `dot(a, b)` | 向量点积 | `float d = dot(N, L);` |
| `cross(a, b)` | 向量叉积 | `vec3 c = cross(a, b);` |
| `normalize(v)` | 归一化（长度变1） | `vec3 n = normalize(N);` |
| `length(v)` | 向量长度 | `float l = length(pos);` |
| `distance(a, b)` | 两点距离 | `float d = distance(p1, p2);` |
| `reflect(I, N)` | 反射向量 | `vec3 R = reflect(V, N);` |
| `refract(I, N, eta)` | 折射向量 | `vec3 T = refract(V, N, 1.33);` |
| `mix(a, b, t)` | 线性插值 `a*(1-t) + b*t` | `vec3 c = mix(c1, c2, 0.5);` |
| `clamp(x, lo, hi)` | 钳制到 [lo, hi] | `float f = clamp(v, 0.0, 1.0);` |
| `smoothstep(e0, e1, x)` | 平滑阶跃 | `float s = smoothstep(0.0, 1.0, t);` |
| `pow(x, y)` | x^y | `float p = pow(v, 2.2);` |
| `exp(x)` | e^x | `float e = exp(-d * density);` |
| `sin/cos/tan(x)` | 三角函数 | `float s = sin(time);` |
| `floor/ceil(x)` | 向下/上取整 | `int i = int(floor(v));` |
| `fract(x)` | 取小数部分 | `float f = fract(uv);` |
| `abs(x)` | 绝对值 | `float a = abs(v);` |
| `max/min(a, b)` | 较大/较小值 | `float m = max(v, 0.0);` |
| `step(edge, x)` | x >= edge ? 1 : 0 | `float s = step(0.5, v);` |
| `texture(sampler, uv)` | 纹理采样 | `vec4 c = texture(colortex0, uv);` |

## Iris 特殊宏与 Uniform

### 条件编译宏

```glsl
IS_IRIS            // 当前在 Iris 上运行
IRIS_VERSION       // Iris 版本号
MC_VERSION         // Minecraft 版本号
MC_GL_VERSION      // OpenGL 版本号
MC_GLSL_VERSION    // GLSL 版本号
```

### 颜色缓冲区 (colortex)

| 名称 | 说明 |
|------|------|
| `colortex0` | 主场景颜色 |
| `colortex1` ~ `colortex7` | 自定义缓冲区（G-Buffer） |

### 深度缓冲区

| 名称 | 说明 |
|------|------|
| `depthtex0` | 场景深度（含所有几何体，包括透明物体） |
| `depthtex1` | 场景深度（不含透明物体） |
| `depthtex2` | 场景深度（不含手部渲染） |

### 阴影缓冲区

| 名称 | 说明 |
|------|------|
| `shadowtex0` | 阴影深度贴图（含透明物体） |
| `shadowtex1` | 阴影深度贴图（不含透明物体） |
| `shadowtex0HW` / `shadowtex1HW` | 硬件滤波版本（Iris 可选） |
| `shadowcolor` / `shadowcolor0`~`N` | 阴影颜色缓冲区 |
| `watershadow` | `shadowtex0` 的旧版别名 |

### 关键 Uniform（常用）

```glsl
uniform float frameTimeCounter;      // 帧时间（秒，持续递增）
uniform int   frameCounter;          // 帧计数器
uniform float viewWidth, viewHeight; // 窗口分辨率
uniform float aspectRatio;           // 宽高比
uniform vec3  cameraPosition;        // 相机世界坐标
uniform vec3  sunPosition;           // 太阳方向
uniform vec3  shadowLightPosition;   // 阴影光源方向
uniform float rainStrength;          // 雨强度 (0~1)
uniform int   worldTime;             // 世界时间 (0~24000)
uniform float near, far;             // 近/远裁剪面
uniform mat4  gbufferModelView;      // 模型视图矩阵
uniform mat4  gbufferProjection;     // 投影矩阵
uniform mat4  gbufferModelViewInverse;      // 模型视图矩阵的逆
uniform mat4  gbufferProjectionInverse;     // 投影矩阵的逆
```

> ⚠️ 补充说明：`timeAngle` 与 `timeBrightness` 并非标准 Iris uniform，它们只出现在 BSL/Complementary 的兼容层（`HardcodedCustomUniforms.java`）里，不能当作所有光影包都可用的通用输入。

## 预处理器指令

```glsl
#define SHADOW 1            // 定义宏
#undef SHADOW               // 取消定义
#ifdef SHADOW               // 如果定义了...
#ifndef SHADOW              // 如果没定义...
#else / #elif / #endif       // 条件分支
#include "/lib/common.glsl" // 包含文件
#version 330 compatibility // 声明 GLSL 版本
```
