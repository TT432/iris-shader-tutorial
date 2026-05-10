import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import rehypeMermaid from 'rehype-mermaid';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: 'https://tt432.github.io',
  base: '/iris-shader-tutorial',

  // Mermaid 图表 + LaTeX 数学公式支持
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [[rehypeKatex, {}], [rehypeMermaid, { strategy: 'img-svg' }]],
  },

  integrations: [
    starlight({
      title: 'Iris Shader 开发教程',
      description: '面向程序员的 Minecraft Iris 光影开发系统教程 — 从零写出你的第一个光影包',

      // 简体中文为唯一语言（使用 root locale，URL 无前缀）
      defaultLocale: 'root',
      locales: {
        root: {
          label: '简体中文',
          lang: 'zh-CN',
        },
      },

      // 代码高亮 — Shiki 原生支持 GLSL
      expressiveCode: {
        themes: ['one-dark-pro', 'github-light'],
        defaultProps: {
          wrap: true,
        },
      },

      // 社交链接
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/TT432/iris-shader-tutorial' },
      ],

      // 搜索: Pagefind (CJK 友好)
      pagefind: true,

      // 编辑链接
      editLink: {
        baseUrl: 'https://github.com/TT432/iris-shader-tutorial/edit/main/',
      },

      // 侧边栏定义 — 只列出已写完的页面
      sidebar: [
        {
          label: '第〇部分 · 站在起跑线上',
          collapsed: true,
          items: [
            { label: '0.1 CPU 与 GPU', link: '/00-prep/01-cpu-vs-gpu/' },
            { label: '0.2 OpenGL 与 GLSL', link: '/00-prep/02-opengl-glsl/' },
            { label: '0.3 环境搭建', link: '/00-prep/03-setup/' },
            { label: '0.4 光影包解剖', link: '/00-prep/04-pack-structure/' },
            { label: '0.5 渲染管线概览', link: '/00-prep/05-pipeline/' },
          ],
        },
        {
          label: '第一部分 · 先让屏幕变个色',
          collapsed: true,
          items: [
            { label: '1.1 你的第一个着色器', link: '/01-composite/01-grayscale/' },
            { label: '1.2 内心独白：灰度公式', link: '/01-composite/02-inner-monologue/' },
            { label: '1.3 uniform 输入参数', link: '/01-composite/03-uniforms/' },
            { label: '1.4 vertex shader 的秘密', link: '/01-composite/04-vertex-shader/' },
            { label: '1.6 shaders.properties 配置', link: '/01-composite/06-shaders-properties/' },
            { label: '1.7 实战：可调灰度滑杆', link: '/01-composite/07-project2/' },
          ],
        },
        {
          label: '第二部分 · 画方块',
          collapsed: false,
          items: [
            { label: '2.1 gbuffers vs composite', link: '/02-gbuffers/01-gbuffers-intro/' },
            { label: '2.2 gbuffers_terrain 解剖', link: '/02-gbuffers/02-terrain/' },
            { label: '2.3 光照是怎么算的', link: '/02-gbuffers/03-lighting/' },
            { label: '2.4 实战：卡通渲染', link: '/02-gbuffers/04-project/' },
            { label: '2.5 为什么需要 G-Buffer', link: '/02-gbuffers/05-gbuffer-intro/' },
            { label: '2.6 RENDERTARGETS 多目标', link: '/02-gbuffers/06-rendertargets/' },
            { label: '2.7 实战：法线可视化', link: '/02-gbuffers/07-project/' },
          ],
        },
        {
          label: '第三部分 · 让光照真实起来',
          collapsed: false,
          items: [
            { label: '3.1 前向 vs 延迟渲染', link: '/03-deferred/01-forward-vs-deferred/' },
            { label: '3.2 从 G-Buffer 重建世界坐标', link: '/03-deferred/02-world-pos-reconstruct/' },
            { label: '3.3 实现 Phong 光照模型', link: '/03-deferred/03-phong-lighting/' },
            { label: '3.4 deferred.fsh 的写法', link: '/03-deferred/04-deferred-pass/' },
            { label: '3.5 实战：基础延迟光照', link: '/03-deferred/05-project/' },
          ],
        },
        {
          label: '第四部分 · 阴影',
          collapsed: false,
          items: [
            { label: '4.1 Shadow Mapping 原理', link: '/04-shadows/01-shadow-intro/' },
            { label: '4.2 shadow.vsh/.fsh 解剖', link: '/04-shadows/02-shadow-pass/' },
            { label: '4.3 阴影采样与比较', link: '/04-shadows/03-shadow-sampling/' },
            { label: '4.4 PCF 软阴影', link: '/04-shadows/04-soft-shadows/' },
            { label: '4.5 实战：初次阴影', link: '/04-shadows/05-project/' },
          ],
        },
        {
          label: '第五部分 · 天空与大气',
          collapsed: false,
          items: [
            { label: '5.1 自定义天空', link: '/05-atmosphere/01-custom-sky/' },
            { label: '5.2 星星渲染', link: '/05-atmosphere/02-stars/' },
            { label: '5.3 体积光 (God Rays)', link: '/05-atmosphere/03-light-shafts/' },
            { label: '5.4 自定义雾效', link: '/05-atmosphere/04-fog/' },
            { label: '5.5 实战：动态天空', link: '/05-atmosphere/05-project/' },
          ],
        },
        {
          label: '第六部分 · 水面与反射',
          collapsed: false,
          items: [
            { label: '6.1 水为什么是特殊的', link: '/06-water/01-water-intro/' },
            { label: '6.2 法线贴图水波', link: '/06-water/02-water-waves/' },
            { label: '6.3 Fresnel 效应', link: '/06-water/03-fresnel/' },
            { label: '6.4 屏幕空间反射 (SSR)', link: '/06-water/04-ssr/' },
            { label: '6.5 实战：镜面水面', link: '/06-water/05-project/' },
          ],
        },
        {
          label: '第七部分 · PBR 材质',
          collapsed: false,
          items: [
            { label: '7.1 为什么原版贴图不够真', link: '/07-pbr/01-pbr-intro/' },
            { label: '7.2 GGX 微表面模型', link: '/07-pbr/02-ggx/' },
            { label: '7.3 specular 与法线贴图', link: '/07-pbr/03-specular-normal/' },
            { label: '7.4 能量守恒', link: '/07-pbr/04-energy/' },
            { label: '7.5 实战：金属方块', link: '/07-pbr/05-project/' },
          ],
        },
        {
          label: '第八部分 · 后处理与最终画面',
          collapsed: false,
          items: [
            { label: '8.1 Bloom 泛光', link: '/08-post/01-bloom/' },
            { label: '8.2 色调映射', link: '/08-post/02-tonemap/' },
            { label: '8.3 色彩分级', link: '/08-post/03-color-grade/' },
            { label: '8.4 FXAA 快速抗锯齿', link: '/08-post/04-fxaa/' },
            { label: '8.5 实战：电影感调色', link: '/08-post/05-project/' },
          ],
        },
        {
          label: '第九部分 · 进阶特效',
          collapsed: true,
          items: [
            { label: '9.1 体积云', link: '/09-advanced/01-volumetric-clouds/' },
            { label: '9.2 视差贴图与曲面细分', link: '/09-advanced/02-parallax/' },
            { label: '9.3 其他 gbuffers Pass', link: '/09-advanced/03-other-gbuffers/' },
            { label: '9.4 实战：体积云天空', link: '/09-advanced/04-project/' },
          ],
        },
        {
          label: '第十部分 · 工程化与发布',
          collapsed: true,
          items: [
            { label: '10.1 维度分离', link: '/10-ship/01-dimensions/' },
            { label: '10.2 配置界面设计', link: '/10-ship/02-config-ui/' },
            { label: '10.3 兼容性处理', link: '/10-ship/03-compat/' },
            { label: '10.4 BSL 源码导读', link: '/10-ship/04-bsl-guide/' },
            { label: '10.5 你的下一步', link: '/10-ship/05-next-steps/' },
          ],
        },
        {
          label: '附录',
          collapsed: false,
          items: [
            { label: 'A. GLSL 速查表', link: '/appendix/a-glsl-cheatsheet/' },
          ],
        },
      ],

      // 自定义 CSS（KaTeX 数学公式样式）
      customCss: ['katex/dist/katex.min.css'],
    }),
  ],
});
