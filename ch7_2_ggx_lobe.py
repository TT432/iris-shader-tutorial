from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
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


def ggx_ndf(NdotH, roughness):
    """GGX / Trowbridge-Reitz NDF"""
    a = roughness * roughness
    a2 = a * a
    denom = NdotH * NdotH * (a2 - 1.0) + 1.0
    denom = np.maximum(denom, 1e-8)
    return a2 / (np.pi * denom * denom)


roughness_values = [0.1, 0.3, 0.5, 0.8]
colors = ["#4cc9f0", "#80ffdb", "#ffd166", "#f72585"]

fig, (ax_polar, ax_curve) = plt.subplots(1, 2, figsize=(15, 6.5), facecolor=BG)

# ── Left: Polar lobe shape ──
ax_polar.set_facecolor(BG)
theta = np.linspace(-np.pi / 2, np.pi / 2, 360)
theta_deg = np.degrees(theta)

for roughness, color in zip(roughness_values, colors):
    # NdotH = cos(theta)
    cos_th = np.cos(theta)
    cos_th = np.maximum(cos_th, 0.001)
    ndf = ggx_ndf(cos_th, roughness)
    ndf_max = ggx_ndf(1.0, roughness)
    ndf_norm = ndf / ndf_max
    r = ndf_norm
    x = r * np.sin(theta)
    y = r * np.cos(theta)
    ax_polar.fill_betweenx(y, -x, x, alpha=0.25, color=color)
    ax_polar.plot(x, y, color=color, lw=2.5, label=f"粗糙度 = {roughness}")
    ax_polar.plot(-x, y, color=color, lw=2.5)

# Reflection direction indicator
ax_polar.annotate("", xy=(0, 1.05), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="#ffffff88", lw=2))
ax_polar.text(0.35, 1.06, "完美镜面反射方向", color=MUTED, ha="left", va="center", fontsize=10)

# Surface indicator
ax_polar.plot([-1.3, 1.3], [0, 0], color="#ffffff44", lw=1.5, linestyle="--")
ax_polar.text(1.32, 0.0, "微表面", color=MUTED, ha="left", va="center", fontsize=9)

ax_polar.set_xlim(-1.35, 1.35)
ax_polar.set_ylim(-0.15, 1.15)
ax_polar.set_aspect("equal")
ax_polar.axis("off")

# Legend on polar
leg = ax_polar.legend(loc="lower left", fontsize=11, facecolor=CARD, edgecolor="#ffffff22", labelcolor=TEXT,
                      bbox_to_anchor=(0.0, -0.08))
leg.set_zorder(100)

# ── Right: Cross-section curve ──
ax_curve.set_facecolor(BG)
angle = np.linspace(-80, 80, 500)
cos_a = np.cos(np.radians(angle))
cos_a = np.maximum(cos_a, 0.001)

for roughness, color in zip(roughness_values, colors):
    ndf = ggx_ndf(cos_a, roughness)
    label_cn = f"粗糙度 {roughness}"
    ax_curve.plot(angle, ndf, color=color, lw=2.2, label=label_cn)

ax_curve.set_xlabel("偏离反射方向的角度 (°)", color=MUTED, fontsize=12)
ax_curve.set_ylabel("NDF 值", color=MUTED, fontsize=12)
ax_curve.set_title("GGX 法线分布函数（NDF）", color=TEXT, fontsize=15, weight="bold", pad=12)
ax_curve.tick_params(colors=MUTED, labelsize=10)
ax_curve.set_facecolor("#1e1e35")
for spine in ax_curve.spines.values():
    spine.set_edgecolor("#ffffff22")

ax_curve.grid(True, alpha=0.12, color="#ffffff")
ax_curve.legend(fontsize=10, facecolor=CARD, edgecolor="#ffffff22", labelcolor=TEXT)

# Highlight annotations
ax_curve.annotate("光滑表面\n高光集中", xy=(0, ggx_ndf(1.0, 0.1)), xytext=(18, ggx_ndf(1.0, 0.1) * 0.6),
                   color=TEXT, fontsize=9.5,
                   arrowprops=dict(arrowstyle="->", color="#4cc9f0", lw=1.5),
                   ha="center")

ax_curve.annotate("粗糙表面\n高光发散", xy=(35, ggx_ndf(np.cos(np.radians(35)), 0.8)),
                   xytext=(58, ggx_ndf(np.cos(np.radians(20)), 0.3)),
                   color=TEXT, fontsize=9.5,
                   arrowprops=dict(arrowstyle="->", color="#f72585", lw=1.5),
                   ha="center")

# Overall title
fig.suptitle("GGX 微表面模型 — 不同粗糙度下的高光波瓣", color=TEXT, fontsize=20, weight="bold", y=0.98)

fig.savefig(OUTPUT_DIR / "ch7_2_ggx_lobe.png", dpi=180, facecolor=BG, bbox_inches="tight")
plt.close(fig)
print("ch7_2_ggx_lobe.png saved")
