from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def add_card(ax, x, y, w, h, edge, title, subtitle):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", facecolor=CARD, edgecolor=edge, linewidth=2.5)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.45, title, ha="center", va="center", color=edge, fontsize=18, weight="bold")
    ax.text(x + w / 2, y + h - 0.85, subtitle, ha="center", va="center", color=TEXT, fontsize=14)
    return (x + 0.22, y + 0.45, w - 0.44, h - 1.55)


def inset_image(fig, box, image):
    ax_img = fig.add_axes(box)
    ax_img.imshow(image, interpolation="nearest")
    ax_img.set_xticks([])
    ax_img.set_yticks([])
    for spine in ax_img.spines.values():
        spine.set_edgecolor("#ffffff33")
        spine.set_linewidth(1.2)


size = 96
x = np.linspace(0, 1, size)
y = np.linspace(0, 1, size)
xx, yy = np.meshgrid(x, y)

albedo = np.zeros((size, size, 3))
albedo[..., 0] = 0.15 + 0.75 * xx
albedo[..., 1] = 0.25 + 0.55 * yy
albedo[..., 2] = 0.35 + 0.35 * (1 - xx)

nx = xx * 2 - 1
ny = yy * 2 - 1
nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
normal = np.dstack(((nx + 1) / 2, (ny + 1) / 2, (nz + 1) / 2))

material = np.zeros((size, size, 3))
checker = ((np.floor(xx * 8) + np.floor(yy * 8)) % 2) * 0.35 + 0.35
material[..., 0] = checker
material[..., 1] = 0.25 + 0.7 * xx
material[..., 2] = 0.2 + 0.6 * (1 - yy)

depth = np.dstack([yy, yy, yy])

fig, ax = plt.subplots(figsize=(15, 6), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 15)
ax.set_ylim(0, 6)
ax.axis("off")

ax.text(7.5, 5.55, "G-Buffer：把一个像素拆成多张“资料卡”", color=TEXT, ha="center", fontsize=25, weight="bold")
ax.text(7.5, 5.12, "后续光照阶段不再猜测，而是读取这些纹理", color=MUTED, ha="center", fontsize=14)

cards = [
    (0.7, "#ff6b6b", "colortex0", "颜色 / Albedo", albedo, "这个像素原本是什么颜色"),
    (4.25, "#4cc9f0", "colortex1", "法线 / Normal", normal, "表面朝向，用 RGB 存 XYZ"),
    (7.8, "#ffd166", "colortex2", "材质 / Material", material, "粗糙度、金属度、遮罩等"),
    (11.35, "#80ffdb", "depthtex0", "深度 / Depth", depth, "离相机远近，近亮远暗"),
]

for x0, edge, title, subtitle, image, note in cards:
    image_box = add_card(ax, x0, 1.0, 2.95, 3.85, edge, title, subtitle)
    inset_image(fig, image_box, image)
    ax.text(x0 + 1.475, 0.55, note, ha="center", va="center", color=MUTED, fontsize=12)

ax.text(7.5, 0.12, "一句话：G-Buffer 先记录“事实”，Deferred 再统一计算光照。", color=TEXT, ha="center", fontsize=13)

fig.savefig(OUTPUT_DIR / "gbuffer_layout.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
