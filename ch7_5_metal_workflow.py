from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
ACCENT = "#f72585"
METAL = "#ffd166"
DIEL = "#4cc9f0"
EDGE_METAL = "#f0a500"
EDGE_DIEL = "#0097e6"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(15, 7.5), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 15)
ax.set_ylim(0, 7.5)
ax.axis("off")

# Title
ax.text(7.5, 7.15, "PBR Metalness 工作流 — 金属与绝缘体的分岔路口", color=TEXT, ha="center", fontsize=23, weight="bold")
ax.text(7.5, 6.7, "一张 metalness 贴图决定每条光线走哪条分支", color=MUTED, ha="center", fontsize=13)

# ── Helper: draw arrow ──
def draw_arrow(x1, y1, x2, y2, color="#ffffffaa", lw=2.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, mutation_scale=18))

def draw_box(x, y, w, h, color, title, desc, face=None):
    if face is None:
        face = "#1e1e35"
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                         facecolor=face, edgecolor=color, linewidth=2.5)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.4, title, color=TEXT, ha="center", va="center", fontsize=13.5, weight="bold")
    if desc:
        ax.text(x + w / 2, y + 0.3, desc, color=MUTED, ha="center", va="center", fontsize=9.5, linespacing=1.35)

# ── Step 1: Albedo (top center) ──
cx = 7.5
draw_box(cx - 1.3, 5.55, 2.6, 0.85, "#9b5de5", "① Albedo 贴图", "颜色纹理 → 基础色")
draw_arrow(cx, 5.55, cx, 4.95, "#9b5de5")

# ── Step 2: Metalness check ──
draw_box(cx - 1.6, 4.1, 3.2, 0.85, ACCENT, "② 读取 Metalness", "采样 _s 贴图 G 通道")
ax.text(cx, 3.85, "metalness ≥ 0.5 ?", color=TEXT, ha="center", fontsize=12, weight="bold")

# Branch arrows
draw_arrow(cx - 1.2, 4.1, 3.5, 3.2, EDGE_METAL)  # left branch
draw_arrow(cx + 1.2, 4.1, 11.5, 3.2, EDGE_DIEL)  # right branch

# ── Left: Metal branch ──
draw_box(1.2, 2.35, 4.6, 0.85, METAL, "③ 金属路径 (Metal)", "specular = albedo\n漫反射 diffuse = 0")

metal_box = FancyBboxPatch((1.2, 0.85), 4.6, 1.15, boxstyle="round,pad=0.04,rounding_size=0.12",
                            facecolor="#2a1e00", edgecolor=METAL, linewidth=2.5)
ax.add_patch(metal_box)
ax.text(3.5, 1.72, "金属材质结果", color=METAL, ha="center", fontsize=14, weight="bold")
ax.text(3.5, 1.2, "镜面反射 90%+ · 无漫反射\n铁、金、铜 → 高光带有材质颜色", color=TEXT, ha="center", fontsize=10.5, linespacing=1.4)

draw_arrow(3.5, 2.35, 3.5, 2.0, METAL)

# ── Right: Dielectric branch ──
draw_box(9.2, 2.35, 4.6, 0.85, DIEL, "③ 绝缘体路径 (Dielectric)", "specular = 0.04 (F0)\ndiffuse = albedo")

diel_box = FancyBboxPatch((9.2, 0.85), 4.6, 1.15, boxstyle="round,pad=0.04,rounding_size=0.12",
                           facecolor="#00202a", edgecolor=DIEL, linewidth=2.5)
ax.add_patch(diel_box)
ax.text(11.5, 1.72, "绝缘体材质结果", color=DIEL, ha="center", fontsize=14, weight="bold")
ax.text(11.5, 1.2, "漫反射为主 · 镜面 ~4%\n塑料、石头、木头 → 灰白色高光", color=TEXT, ha="center", fontsize=10.5, linespacing=1.4)

draw_arrow(11.5, 2.35, 11.5, 2.0, DIEL)

# ── Bottom explanation ──
note_y = 0.28
ax.text(7.5, note_y, "PBR Metalness 工作流的核心：用一张 metalness 贴图（0~1 连续值）在金属和绝缘体之间做混合，而不是二选一。",
        color=TEXT, ha="center", fontsize=11.5,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e1e35", edgecolor="#ffffff22", linewidth=1))

fig.savefig(OUTPUT_DIR / "ch7_5_metal_workflow.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("ch7_5_metal_workflow.png saved")
