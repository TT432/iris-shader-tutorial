from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Wedge
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"
GOOD = "#2ecc71"
BAD = "#e74c3c"
WARN = "#f39c12"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, (ax_correct, ax_wrong) = plt.subplots(1, 2, figsize=(14, 6), facecolor=BG)

for ax_i in [ax_correct, ax_wrong]:
    ax_i.set_facecolor(BG)
    ax_i.set_xlim(-1.35, 1.35)
    ax_i.set_ylim(-1.35, 1.35)
    ax_i.set_aspect("equal")
    ax_i.axis("off")

# ── Left: Correct energy conservation ──
# Outer ring = total incoming light = 100%
outer = Wedge((0, 0), 1.2, 0, 360, facecolor="#ffffff10", edgecolor="#ffffff33", linewidth=2)
ax_correct.add_patch(outer)

# Diffuse 70%
diffuse = Wedge((0, 0), 1.2, 0, 360 * 0.7, facecolor="#4cc9f0", alpha=0.7, edgecolor="none")
ax_correct.add_patch(diffuse)

# Specular 30%
specular = Wedge((0, 0), 1.2, 360 * 0.7, 360, facecolor="#ffd166", alpha=0.7, edgecolor="none")
ax_correct.add_patch(specular)

# Center label
ax_correct.add_patch(FancyBboxPatch((-0.7, -0.42), 1.4, 0.84, boxstyle="round,pad=0.04,rounding_size=0.1",
                                     facecolor="#1a1a2edd", edgecolor=GOOD, linewidth=2))
ax_correct.text(0, 0.12, "输入 = 100%", color=TEXT, ha="center", va="center", fontsize=14, weight="bold")
ax_correct.text(0, -0.22, "输出 ≤ 100%", color=GOOD, ha="center", va="center", fontsize="12")

# Labels
ax_correct.text(0.55, 0.65, "漫反射 70%", color="#4cc9f0", ha="center", fontsize=13, weight="bold")
ax_correct.text(-0.55, -0.55, "镜面反射 30%", color="#ffd166", ha="center", fontsize=13, weight="bold")

# Title
title_l = FancyBboxPatch((-1.15, 0.95), 2.3, 0.35, boxstyle="round,pad=0.03,rounding_size=0.08",
                          facecolor="#1e3a2e", edgecolor=GOOD, linewidth=2)
ax_correct.add_patch(title_l)
ax_correct.text(0, 1.125, "[OK] 正确：能量守恒", color=GOOD, ha="center", va="center", fontsize=15, weight="bold")

# ── Right: WRONG energy conservation ──
outer_w = Wedge((0, 0), 1.2, 0, 360, facecolor="#ffffff10", edgecolor="#ffffff33", linewidth=2)
ax_wrong.add_patch(outer_w)

# Diffuse 80%
diffuse_w = Wedge((0, 0), 1.2, 0, 360 * 0.8, facecolor="#4cc9f0", alpha=0.5, edgecolor="none")
ax_wrong.add_patch(diffuse_w)

# Specular 50% - overlaps!
specular_w = Wedge((0, 0), 1.2, 180, 360 * 0.5 + 180, facecolor="#f72585", alpha=0.5, edgecolor="none")
ax_wrong.add_patch(specular_w)

# Excess indication
excess = Wedge((0, 0), 1.25, 180, 360 * 0.3 + 180, facecolor="none", edgecolor=BAD, linewidth=3, linestyle="--",
               alpha=0.8)
ax_wrong.add_patch(excess)

# Center label
ax_wrong.add_patch(FancyBboxPatch((-0.7, -0.42), 1.4, 0.84, boxstyle="round,pad=0.04,rounding_size=0.1",
                                   facecolor="#1a1a2edd", edgecolor=BAD, linewidth=2))
ax_wrong.text(0, 0.12, "输入 = 100%", color=TEXT, ha="center", va="center", fontsize=14, weight="bold")
ax_wrong.text(0, -0.22, "输出 = 130%!", color=BAD, ha="center", va="center", fontsize=12, weight="bold")

# Labels
ax_wrong.text(0.52, 0.5, "漫反射 80%", color="#4cc9f0", ha="center", fontsize=13, weight="bold")
ax_wrong.text(-0.48, -0.22, "镜面反射 50%", color="#f72585", ha="center", fontsize=13, weight="bold")

# Excess label
ax_wrong.text(0.65, -0.85, "超出 30%！\n违反物理定律", color=BAD, ha="center", fontsize=11, weight="bold",
              linespacing=1.3)

title_w = FancyBboxPatch((-1.2, 0.95), 2.4, 0.35, boxstyle="round,pad=0.03,rounding_size=0.08",
                          facecolor="#3a1e2e", edgecolor=BAD, linewidth=2)
ax_wrong.add_patch(title_w)
ax_wrong.text(0, 1.125, "[X] 错误：能量不守恒", color=BAD, ha="center", va="center", fontsize=15, weight="bold")

# ── Overall layout ──
fig.suptitle("", fontsize=1)  # placeholder

# Bottom notes panel
fig.text(0.5, 0.02, "能量守恒规则：漫反射 + 镜面反射 ≤ 100% · 金属的漫反射 = 0 · PBR 光线追迹保证输出 ≤ 输入",
         ha="center", color=MUTED, fontsize=12, transform=fig.transFigure,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e35", edgecolor="none", alpha=0.7))

# Additional note about metal
fig.text(0.25, 0.08, "金属特例：金属没有漫反射\n光碰到金属只在表面反射\nAlbedo → specular, diffuse = 0",
         ha="center", color=WARN, fontsize=11, transform=fig.transFigure,
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#2a1e00", edgecolor=WARN, linewidth=1.5, alpha=0.8))

fig.savefig(OUTPUT_DIR / "ch7_4_energy_conservation.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("ch7_4_energy_conservation.png saved")
