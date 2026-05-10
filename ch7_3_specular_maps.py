from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "public" / "images" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#1a1a2e"
CARD = "#242447"
TEXT = "#f4f7fb"
MUTED = "#b7c0d8"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(13, 8.5), facecolor=BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 13)
ax.set_ylim(0, 8.5)
ax.axis("off")

# Title
ax.text(6.5, 8.1, "LabPBR 1.3 — Specular 贴图通道布局 (_s 纹理)", color=TEXT, ha="center", fontsize=22, weight="bold")
ax.text(6.5, 7.6, "一张 RGBA 纹理 = 四份独立的材质信息", color=MUTED, ha="center", fontsize=13)

# ── 2x2 grid ──
channels = [
    ("R 通道", "光滑度\nSmoothness", "#e74c3c", "1 = 镜面光滑\n0 = 极粗糙\n控制高光扩散"),
    ("G 通道", "金属度\nMetalness", "#2ecc71", "1 = 纯金属\n0 = 绝缘体\n决定镜面反射颜色"),
    ("B 通道", "环境光遮蔽\nAmbient Occlusion", "#3498db", "角落天然更暗\n预烘焙局部阴影\n增加立体感"),
    ("A 通道", "自发光\nEmissive", "#f39c12", "发光的眼睛/岩浆\n独立于光照\n低值 = 不发光"),
]

grid_x = [0.8, 6.9]
grid_y = [4.5, 0.85]
box_w = 5.3
box_h = 2.85

for idx, (chan, name, color, desc) in enumerate(channels):
    gx = grid_x[idx % 2]
    gy = grid_y[idx // 2]

    # Card
    card = FancyBboxPatch((gx, gy), box_w, box_h, boxstyle="round,pad=0.04,rounding_size=0.12",
                          facecolor="#1e1e35", edgecolor=color, linewidth=2.5)
    ax.add_patch(card)

    # Channel name badge
    badge = FancyBboxPatch((gx + 0.3, gy + box_h - 0.7), 1.55, 0.42,
                           boxstyle="round,pad=0.02,rounding_size=0.06", facecolor=color, edgecolor="none")
    ax.add_patch(badge)
    ax.text(gx + 1.075, gy + box_h - 0.49, chan, color="#ffffff", ha="center", va="center", fontsize=13, weight="bold")

    # Name
    ax.text(gx + 2.65, gy + box_h - 0.49, name, color=TEXT, ha="center", va="center", fontsize=15, weight="bold",
            linespacing=1.3)

    # Colored swatch
    size = 80
    grad = np.tile(np.linspace(0.1, 1.0, size).reshape(1, size, 1), (size, 1, 1))
    color_rgb = np.array(plt.matplotlib.colors.to_rgb(color)).reshape(1, 1, 3)
    swatch_img = grad * color_rgb * 0.75 + 0.08

    # Add some noise texture to make it look like a map
    rng = np.random.RandomState(idx * 42)
    noise = rng.uniform(0.85, 1.15, (size, size, 3))
    swatch_img = np.clip(swatch_img * noise, 0, 1)

    # Create inset axes for the swatch
    inset = fig.add_axes([(gx + 0.3) / 13, (gy + 0.5) / 8.5, 2.2 / 13, 1.55 / 8.5])
    inset.imshow(swatch_img, interpolation="bilinear")
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_edgecolor(f"{color}66")
        spine.set_linewidth(1.5)

    # Description text
    ax.text(gx + 3.1, gy + 1.25, desc, color=MUTED, ha="left", va="center", fontsize=11.5, linespacing=1.55)

# Bottom: LabPBR note
note_box = FancyBboxPatch((0.8, 0.08), 11.4, 0.55, boxstyle="round,pad=0.03,rounding_size=0.08",
                          facecolor="#20203b", edgecolor="#ffffff22", linewidth=1.5)
ax.add_patch(note_box)
ax.text(6.5, 0.35, "LabPBR 1.3 约定：_s 纹理的 RGBA = 光滑度·金属度·AO·自发光 — 社区共同遵守的通道布局标准",
        color=TEXT, ha="center", va="center", fontsize=11.5)

fig.savefig(OUTPUT_DIR / "ch7_3_specular_maps.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("ch7_3_specular_maps.png saved")
