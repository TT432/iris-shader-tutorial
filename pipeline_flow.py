from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
CARD = "#242447"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


fig, ax = plt.subplots(figsize=(15, 5.5), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 15)
ax.set_ylim(0, 5.5)
ax.axis("off")

ax.text(7.5, 5.05, "Iris 渲染管线：一帧图像的接力赛", color=TEXT, ha="center", fontsize=25, weight="bold")
ax.text(7.5, 4.62, "每个 pass 接收上一站的结果，再写出下一站需要的纹理", color=MUTED, ha="center", fontsize=14)

stages = [
    ("shadow", "阴影贴图", "先从光源视角\n记录遮挡关系", "#9b5de5"),
    ("gbuffers", "几何缓冲", "写入颜色、法线\n材质和深度", "#4cc9f0"),
    ("deferred", "延迟光照", "读取 G-Buffer\n计算主要光照", "#ffd166"),
    ("composite", "后期合成", "泛光、雾、调色\n逐步叠加效果", "#f72585"),
    ("final", "最终输出", "送到屏幕\n成为玩家看到的画面", "#80ffdb"),
]

box_w = 2.35
box_h = 2.35
y = 1.55
xs = [0.65, 3.55, 6.45, 9.35, 12.25]

for (name, title, desc, color), x in zip(stages, xs):
    patch = FancyBboxPatch((x, y), box_w, box_h, boxstyle="round,pad=0.05,rounding_size=0.16", facecolor=CARD, edgecolor=color, linewidth=2.5)
    ax.add_patch(patch)
    ax.text(x + box_w / 2, y + 1.78, name, ha="center", va="center", color=color, fontsize=17, weight="bold")
    ax.text(x + box_w / 2, y + 1.28, title, ha="center", va="center", color=TEXT, fontsize=16, weight="bold")
    ax.text(x + box_w / 2, y + 0.62, desc, ha="center", va="center", color=MUTED, fontsize=12, linespacing=1.45)

for start, end in zip(xs, xs[1:]):
    ax.add_patch(FancyArrowPatch((start + box_w + 0.08, y + box_h / 2), (end - 0.08, y + box_h / 2), arrowstyle="-|>", mutation_scale=22, color="#ffffffaa", lw=2.2))

ax.text(7.5, 0.58, "理解顺序很关键：你在某个 pass 里，只能可靠使用它之前已经写好的结果。", color=TEXT, ha="center", fontsize=13)

fig.savefig(OUTPUT_DIR / "pipeline_flow.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
