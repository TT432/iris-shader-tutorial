from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
PANEL = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
CPU = "#ffb703"
GPU = "#4cc9f0"
ACCENT = "#f72585"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def add_box(ax, xy, width, height, color, label, fontsize=16):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.03,rounding_size=0.08",
        linewidth=2,
        edgecolor=color,
        facecolor=PANEL,
    )
    ax.add_patch(box)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, label, color=TEXT, ha="center", va="center", fontsize=fontsize, weight="bold")


def draw_professor(ax, x, y, color):
    ax.add_patch(Circle((x, y + 0.55), 0.16, facecolor=color, edgecolor="none"))
    ax.plot([x, x], [y + 0.08, y + 0.42], color=color, lw=6, solid_capstyle="round")
    ax.plot([x - 0.3, x + 0.3], [y + 0.25, y + 0.32], color=color, lw=5, solid_capstyle="round")
    ax.plot([x, x - 0.22], [y + 0.08, y - 0.24], color=color, lw=5, solid_capstyle="round")
    ax.plot([x, x + 0.22], [y + 0.08, y - 0.24], color=color, lw=5, solid_capstyle="round")
    ax.add_patch(Rectangle((x + 0.25, y + 0.05), 0.28, 0.18, facecolor="none", edgecolor=color, lw=3))


def draw_many_arms(ax, cx, cy, radius, color):
    angles = np.linspace(-140, 140, 17) * np.pi / 180
    for angle in angles:
        x2 = cx + radius * np.cos(angle)
        y2 = cy + radius * np.sin(angle)
        ax.plot([cx, x2], [cy, y2], color=color, lw=3, alpha=0.85, solid_capstyle="round")
        ax.add_patch(Circle((x2, y2), 0.035, facecolor=color, edgecolor="none", alpha=0.95))
    ax.add_patch(Circle((cx, cy), 0.2, facecolor=color, edgecolor="none"))
    ax.add_patch(Circle((cx, cy + 0.28), 0.13, facecolor=color, edgecolor="none"))


fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis("off")

ax.text(7, 7.55, "CPU 串行思考 vs GPU 并行洪流", color=TEXT, ha="center", va="center", fontsize=28, weight="bold")
ax.text(7, 7.12, "同一批任务，处理模型完全不同", color=MUTED, ha="center", va="center", fontsize=15)

left = FancyBboxPatch((0.6, 0.7), 5.9, 6.0, boxstyle="round,pad=0.05,rounding_size=0.18", facecolor="#20203b", edgecolor=CPU, linewidth=2.5)
right = FancyBboxPatch((7.5, 0.7), 5.9, 6.0, boxstyle="round,pad=0.05,rounding_size=0.18", facecolor="#20203b", edgecolor=GPU, linewidth=2.5)
ax.add_patch(left)
ax.add_patch(right)

ax.text(3.55, 6.35, "CPU：一位教授，逐题批改", color=CPU, ha="center", fontsize=20, weight="bold")
draw_professor(ax, 1.6, 4.4, CPU)

xs = [2.7, 3.6, 4.5, 5.4]
for number, x in enumerate(xs, start=1):
    add_box(ax, (x - 0.26, 4.05), 0.52, 0.52, CPU, str(number), fontsize=18)
for x1, x2 in zip(xs, xs[1:]):
    ax.add_patch(FancyArrowPatch((x1 + 0.32, 4.31), (x2 - 0.32, 4.31), arrowstyle="-|>", mutation_scale=18, color=CPU, lw=2))
ax.text(3.9, 3.2, "一个核心按顺序执行：\n先做 1，再做 2，再做 3……", color=TEXT, ha="center", va="center", fontsize=16)
ax.text(3.55, 1.45, "优点：复杂逻辑强\n瓶颈：大量像素会排队", color=MUTED, ha="center", va="center", fontsize=15)

ax.text(10.45, 6.35, "GPU：千手观音，同时开工", color=GPU, ha="center", fontsize=20, weight="bold")
draw_many_arms(ax, 10.45, 4.35, 1.55, GPU)

grid_x = np.linspace(8.5, 12.4, 7)
grid_y = np.linspace(2.35, 5.55, 5)
colors = ["#4cc9f0", "#80ffdb", "#f72585", "#b5179e", "#ffd166"]
for row, y in enumerate(grid_y):
    for col, x in enumerate(grid_x):
        ax.add_patch(Rectangle((x - 0.12, y - 0.12), 0.24, 0.24, facecolor=colors[(row + col) % len(colors)], edgecolor="none", alpha=0.9))

ax.text(10.45, 1.45, "成千上万个小核心\n同时处理像素、顶点、采样", color=MUTED, ha="center", va="center", fontsize=15)
ax.text(10.45, 0.95, "着色器的核心思想：把同一段程序发给很多数据", color=TEXT, ha="center", va="center", fontsize=14)

fig.savefig(OUTPUT_DIR / "cpu_vs_gpu.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
