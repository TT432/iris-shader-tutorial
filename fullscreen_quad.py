from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
ACCENT = "#4cc9f0"
PINK = "#f72585"
GREEN = "#80ffdb"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis("off")

ax.text(7, 7.55, "全屏四边形技巧：只给 4 个顶点，铺满整张屏幕", color=TEXT, ha="center", fontsize=24, weight="bold")
ax.text(7, 7.12, "顶点着色器很少，片元着色器会被光栅化成约 200 万个像素任务", color=MUTED, ha="center", fontsize=14)

left = FancyBboxPatch((0.65, 0.85), 5.8, 5.85, boxstyle="round,pad=0.05,rounding_size=0.16", facecolor="#242447", edgecolor=ACCENT, linewidth=2.3)
right = FancyBboxPatch((7.55, 0.85), 5.8, 5.85, boxstyle="round,pad=0.05,rounding_size=0.16", facecolor="#242447", edgecolor=PINK, linewidth=2.3)
ax.add_patch(left)
ax.add_patch(right)

quad = np.array([[1.55, 1.75], [5.55, 1.75], [5.55, 5.75], [1.55, 5.75]])
ax.add_patch(Polygon(quad, closed=True, facecolor="#4cc9f022", edgecolor=ACCENT, linewidth=3))
ax.plot([1.55, 5.55], [1.75, 5.75], color=ACCENT, lw=1.4, alpha=0.55)
ax.plot([1.55, 5.55], [5.75, 1.75], color=ACCENT, lw=1.4, alpha=0.35)

corner_labels = ["(-1, -1)", "(1, -1)", "(1, 1)", "(-1, 1)"]
offsets = [(-0.28, -0.35), (0.28, -0.35), (0.28, 0.35), (-0.28, 0.35)]
for point, label, offset in zip(quad, corner_labels, offsets):
    ax.scatter([point[0]], [point[1]], s=95, color=GREEN, zorder=4)
    ax.text(point[0] + offset[0], point[1] + offset[1], label, color=TEXT, ha="center", va="center", fontsize=12)
ax.text(3.55, 6.25, "裁剪空间四个角", color=ACCENT, ha="center", fontsize=17, weight="bold")
ax.text(3.55, 1.22, "几何很简单：覆盖整块屏幕", color=MUTED, ha="center", fontsize=13)

screen_x, screen_y = 8.35, 1.55
screen_w, screen_h = 4.25, 4.5
ax.add_patch(Rectangle((screen_x, screen_y), screen_w, screen_h, facecolor="#0f172acc", edgecolor=PINK, linewidth=2.5))

cols, rows = 28, 18
for col in range(cols):
    for row in range(rows):
        px = screen_x + (col + 0.5) * screen_w / cols
        py = screen_y + (row + 0.5) * screen_h / rows
        alpha = 0.22 + 0.45 * (col + row) / (cols + rows)
        ax.scatter([px], [py], s=6, color=PINK, alpha=alpha, linewidths=0)

for col in range(1, cols):
    x = screen_x + col * screen_w / cols
    ax.plot([x, x], [screen_y, screen_y + screen_h], color="#ffffff12", lw=0.45)
for row in range(1, rows):
    y = screen_y + row * screen_h / rows
    ax.plot([screen_x, screen_x + screen_w], [y, y], color="#ffffff12", lw=0.45)

ax.text(10.48, 6.25, "光栅化后的像素网格", color=PINK, ha="center", fontsize=17, weight="bold")
ax.text(10.48, 1.05, "示意：1920 × 1080 ≈ 207 万个片元", color=TEXT, ha="center", fontsize=13)

ax.add_patch(FancyArrowPatch((6.58, 3.8), (7.42, 3.8), arrowstyle="-|>", mutation_scale=28, color="#ffffffcc", lw=2.4))
ax.text(7, 4.25, "光栅化", color=TEXT, ha="center", fontsize=14, weight="bold")
ax.text(7, 0.42, "所以 composite/final 常用它：不用画模型，只让每个屏幕像素运行一次着色器。", color=MUTED, ha="center", fontsize=13)

fig.savefig(OUTPUT_DIR / "fullscreen_quad.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
