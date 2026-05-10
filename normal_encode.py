from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
RED = "#ff595e"
GREEN = "#8ac926"
BLUE = "#4cc9f0"
YELLOW = "#ffd166"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def rounded(ax, x, y, w, h, edge, title, body):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.16", facecolor=CARD, edgecolor=edge, linewidth=2.4))
    ax.text(x + w / 2, y + h - 0.45, title, color=edge, ha="center", va="center", fontsize=18, weight="bold")
    ax.text(x + w / 2, y + 0.78, body, color=TEXT, ha="center", va="center", fontsize=14, linespacing=1.5)


fig, ax = plt.subplots(figsize=(15, 7), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 15)
ax.set_ylim(0, 7)
ax.axis("off")

ax.text(7.5, 6.55, "法线编码：把 [-1, 1] 的方向塞进 [0, 1] 的颜色", color=TEXT, ha="center", fontsize=24, weight="bold")
ax.text(7.5, 6.12, "纹理颜色不能直接存负数，所以先打包，读取时再解包", color=MUTED, ha="center", fontsize=14)

rounded(ax, 0.75, 3.05, 3.45, 2.3, RED, "原始法线", "X、Y、Z 都在 [-1, 1]\n例如 n = (-0.4, 0.7, 0.6)")
rounded(ax, 5.75, 3.05, 3.45, 2.3, YELLOW, "打包到颜色", "encoded = n × 0.5 + 0.5\n范围变成 [0, 1]")
rounded(ax, 10.75, 3.05, 3.45, 2.3, BLUE, "解包回方向", "normal = encoded × 2.0 - 1.0\n重新得到可计算的法线")

for x1, x2 in [(4.28, 5.68), (9.28, 10.68)]:
    ax.add_patch(FancyArrowPatch((x1, 4.2), (x2, 4.2), arrowstyle="-|>", mutation_scale=26, color="#ffffffcc", lw=2.5))

channels = [(RED, "R = X"), (GREEN, "G = Y"), (BLUE, "B = Z")]
for i, (color, label) in enumerate(channels):
    y = 2.2 - i * 0.52
    ax.add_patch(Rectangle((1.15, y), 2.65, 0.22, facecolor="#ffffff18", edgecolor="none"))
    ax.add_patch(Rectangle((1.15, y), 1.32, 0.22, facecolor=color, edgecolor="none", alpha=0.9))
    ax.text(0.75, y + 0.11, "-1", color=MUTED, ha="right", va="center", fontsize=11)
    ax.text(3.95, y + 0.11, "1", color=MUTED, ha="left", va="center", fontsize=11)
    ax.text(2.47, y + 0.35, label, color=color, ha="center", va="center", fontsize=12, weight="bold")

encoded_color = np.array([( -0.4 + 1) / 2, (0.7 + 1) / 2, (0.6 + 1) / 2])
ax.add_patch(Rectangle((6.45, 1.15), 2.0, 1.25, facecolor=encoded_color, edgecolor="#ffffffaa", linewidth=2))
ax.text(7.45, 0.83, "示例颜色 ≈ (0.30, 0.85, 0.80)", color=MUTED, ha="center", fontsize=12)

center = np.array([12.45, 1.65])
ax.scatter([center[0]], [center[1]], s=80, color="#ffffff", zorder=4)
vectors = [((-0.75, 0.25), RED, "X"), ((0.35, 0.88), GREEN, "Y"), ((0.8, 0.52), BLUE, "Z")]
for direction, color, label in vectors:
    end = center + np.array(direction)
    ax.add_patch(FancyArrowPatch(tuple(center), tuple(end), arrowstyle="-|>", mutation_scale=18, color=color, lw=2.3))
    ax.text(end[0] + 0.1, end[1] + 0.03, label, color=color, fontsize=12, weight="bold")

ax.text(12.45, 0.83, "读取后再参与 dot、光照、反射计算", color=MUTED, ha="center", fontsize=12)
ax.text(7.5, 0.25, "记忆公式：存进去时 +1 再除以 2；取出来时乘 2 再 -1。", color=TEXT, ha="center", fontsize=13)

fig.savefig(OUTPUT_DIR / "normal_encode.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
