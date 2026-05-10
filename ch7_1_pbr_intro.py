from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
TRAD = "#ff6b6b"
PBR = "#4cc9f0"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis("off")

# Title
ax.text(7.0, 6.55, "传统渲染 vs PBR 物理渲染", color=TEXT, ha="center", va="center", fontsize=26, weight="bold")
ax.text(7.0, 6.05, "传统只靠一张颜色贴图；PBR 把金属度、粗糙度、法线、AO 分开描述材质", color=MUTED, ha="center", va="center", fontsize=14)

# === Left: Traditional ===
box_l = FancyBboxPatch((0.7, 0.8), 5.7, 4.8, boxstyle="round,pad=0.05,rounding_size=0.18", facecolor="#20203b", edgecolor=TRAD, linewidth=2.5)
ax.add_patch(box_l)
ax.text(3.55, 5.3, "传统：颜色贴图 only", color=TRAD, ha="center", fontsize=18, weight="bold")

# Flat colored block - just one layer
block_l = FancyBboxPatch((1.6, 1.5), 3.9, 2.8, boxstyle="round,pad=0.04,rounding_size=0.12", facecolor="#5a7a5a", edgecolor="#3a5a3a", linewidth=3)
ax.add_patch(block_l)
ax.text(3.55, 2.9, "albedo 贴图", color=TEXT, ha="center", fontsize=16, weight="bold")

# Annotations
ax.text(3.55, 1.8, "只有一张颜色贴图", color=MUTED, ha="center", fontsize=12)
ax.text(3.55, 1.35, "铁块和石头光照完全一样", color=MUTED, ha="center", fontsize=10.5)

# Single layer arrow indicator
arrow_l = np.array([[0.0, 0.0], [0.05, 0.08], [0.12, 0.13], [0.25, 0.16], [0.4, 0.05], [-0.2, 0.02], [0.0, 0.0]])
arrow_l[:, 0] += 3.55
arrow_l[:, 1] += 0.8
ax.fill(arrow_l[:, 0] + 0.15, arrow_l[:, 1], color=TRAD, alpha=0.15)
ax.text(3.55, 1.0, "→ 输入 = 1 张纹理", color=TRAD, ha="center", fontsize=12, alpha=0.9)

# === Right: PBR ===
box_r = FancyBboxPatch((7.6, 0.8), 5.7, 4.8, boxstyle="round,pad=0.05,rounding_size=0.18", facecolor="#20203b", edgecolor=PBR, linewidth=2.5)
ax.add_patch(box_r)
ax.text(10.45, 5.3, "PBR：多层物理贴图", color=PBR, ha="center", fontsize=18, weight="bold")

# 4-layer block representation
layers = [
    ("颜色 Albedo", "#6b8e6b", 0.3),
    ("法线 Normal", "#4a7ab5", 0.28),
    ("粗糙度 Roughness", "#c9953b", 0.26),
    ("金属度 Metalness", "#c06060", 0.24),
]
y_start = 3.85
for label, color, alpha_val in layers:
    rect = FancyBboxPatch((8.5, y_start), 3.9, 0.38, boxstyle="round,pad=0.02,rounding_size=0.06",
                          facecolor=color, edgecolor="none", alpha=alpha_val)
    ax.add_patch(rect)
    ax.text(10.45, y_start + 0.19, label, color="#ffffffcc", ha="center", va="center", fontsize=11.5, weight="bold")
    y_start -= 0.52

ax.text(10.45, 1.8, "四种贴图协同描述材质", color=MUTED, ha="center", fontsize=12)
ax.text(10.45, 1.35, "铁块高反光 · 石头哑光 · 真实区分", color=MUTED, ha="center", fontsize=10.5)

ax.text(10.45, 1.0, "→ 输入 = 4 张纹理", color=PBR, ha="center", fontsize=12, alpha=0.9)

# Bottom note
ax.text(7.0, 0.25, 'PBR = 用物理参数描述材质行为，而不是靠画师在贴图上「画」出光影', color=TEXT, ha="center", fontsize=12.5)

fig.savefig(OUTPUT_DIR / "ch7_1_pbr_intro.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("ch7_1_pbr_intro.png saved")
