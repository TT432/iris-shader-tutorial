#!/usr/bin/env python3
"""
Generate all Chapter 9 and Chapter 10 diagrams for the Iris Shader tutorial.
Dark theme (#1a1a2e), Chinese labels, professional matplotlib diagrams.
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc, Polygon, Circle, Rectangle, Wedge, FancyArrow
from matplotlib.patches import ConnectionPatch
import matplotlib.patches as mpatches
from matplotlib.path import Path
import matplotlib.patheffects as pe

# ─── Global config ────────────────────────────────────────────────
OUTDIR = os.path.dirname(os.path.abspath(__file__))
BG = '#1a1a2e'
FG = '#e0e0e0'
ACCENT = '#00d4ff'
ACCENT2 = '#ff6b6b'
ACCENT3 = '#ffd93d'
ACCENT4 = '#6bcb77'
ACCENT5 = '#a855f7'
ACCENT6 = '#f59e0b'
GRID_COLOR = '#2a2a4a'
DPI = 150
FIGSIZE_STD = (10, 6)

# Chinese font
plt.rcParams['font.family'] = 'Microsoft YaHei'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def save(fig, name):
    path = os.path.join(OUTDIR, name)
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(fig)
    print(f"  ✓ {name}")


# ═══════════════════════════════════════════════════════════════════
# Chapter 9
# ═══════════════════════════════════════════════════════════════════

def ch9_1_volumetric_clouds():
    """体积云光线步进 — camera rays marching through cloud volume."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Camera body (trapezoid on left)
    cam_x = 1.2
    cam = Polygon([
        (cam_x - 0.4, 3 - 0.3), (cam_x + 0.4, 3 - 0.5),
        (cam_x + 0.4, 3 + 0.5), (cam_x - 0.4, 3 + 0.3)
    ], facecolor='#333355', edgecolor=ACCENT, linewidth=1.5, zorder=5)
    ax.add_patch(cam)
    # Lens
    lens = Circle((cam_x + 0.35, 3), 0.15, facecolor=ACCENT, edgecolor='white', linewidth=0.8, zorder=6)
    ax.add_patch(lens)
    ax.text(cam_x - 0.6, 1.5, '相机', color=FG, fontsize=11, ha='center', fontweight='bold')

    # Cloud volume (rounded rect)
    cloud_bg = FancyBboxPatch((5, 1.5), 6.5, 3, boxstyle="round,pad=0.3",
                               facecolor='#1e2a4a', edgecolor='#3a5a8a', linewidth=1.5, zorder=1)
    ax.add_patch(cloud_bg)

    # Cloud density gradient (vertical gradient approximated with horizontal bands)
    for i in range(20):
        alpha = 0.03 + 0.04 * (1 - abs(i - 10) / 10)  # denser in middle
        y0 = 1.5 + i * 3 / 20
        rect = Rectangle((5.2, y0), 6.1, 3 / 20, facecolor='white', alpha=alpha, zorder=2)
        ax.add_patch(rect)

    # Internal cloud blobs
    rng = np.random.default_rng(42)
    for _ in range(25):
        cx = rng.uniform(5.5, 10.5)
        cy = rng.uniform(2.0, 4.2)
        r = rng.uniform(0.3, 0.8)
        alpha = rng.uniform(0.08, 0.25)
        blob = Circle((cx, cy), r, facecolor='white', alpha=alpha, edgecolor='none', zorder=3)
        ax.add_patch(blob)

    ax.text(8.25, 5.0, '体积云', color='white', fontsize=14, ha='center', fontweight='bold', zorder=5)
    ax.text(8.25, 4.5, '云密度梯度', color='#88aacc', fontsize=9, ha='center', zorder=5)

    # Ray 1 (top)
    ray_y = 3.9
    ax.plot([cam_x + 0.35, 5], [ray_y, ray_y], color=ACCENT3, linewidth=1.2, alpha=0.6, zorder=4)
    steps1 = [(5.8, ray_y), (7.5, ray_y), (9.2, ray_y), (10.5, ray_y)]
    for i, (sx, sy) in enumerate(steps1):
        c = Circle((sx, sy), 0.12, facecolor=ACCENT3, edgecolor='white', linewidth=0.8, zorder=7)
        ax.add_patch(c)
        if i > 0:
            ax.annotate(f'步{i}', (sx, sy + 0.3), color=ACCENT3, fontsize=8, ha='center')

    # Ray 2 (middle)
    ray_y = 3.0
    ax.plot([cam_x + 0.35, 5], [ray_y, ray_y], color=ACCENT, linewidth=1.2, alpha=0.6, zorder=4)
    steps2 = [(5.6, ray_y), (7.0, ray_y), (8.5, ray_y), (9.8, ray_y)]
    for i, (sx, sy) in enumerate(steps2):
        c = Circle((sx, sy), 0.12, facecolor=ACCENT, edgecolor='white', linewidth=0.8, zorder=7)
        ax.add_patch(c)

    # Ray 3 (bottom)
    ray_y = 2.1
    ax.plot([cam_x + 0.35, 5], [ray_y, ray_y], color=ACCENT4, linewidth=1.2, alpha=0.6, zorder=4)
    steps3 = [(5.8, ray_y), (7.3, ray_y), (9.0, ray_y)]
    for i, (sx, sy) in enumerate(steps3):
        c = Circle((sx, sy), 0.12, facecolor=ACCENT4, edgecolor='white', linewidth=0.8, zorder=7)
        ax.add_patch(c)

    # Distance annotation
    ax.annotate('', xy=(9.2, 4.3), xytext=(7.5, 4.3),
                arrowprops=dict(arrowstyle='<->', color=ACCENT3, lw=1.2))
    ax.text(8.35, 4.5, '步长 ≈ 0.5m', color=ACCENT3, fontsize=8, ha='center')

    # Light direction arrow
    ax.annotate('太阳光', xy=(6.5, 5.3), xytext=(10, 5.3),
                arrowprops=dict(arrowstyle='->', color='orange', lw=1.5), color='orange', fontsize=10, ha='center')

    # Density label with arrow
    ax.annotate('密度递增', xy=(10.5, 3.0), xytext=(12.2, 3.0),
                arrowprops=dict(arrowstyle='->', color='#88aacc', lw=1), color='#88aacc', fontsize=9)

    save(fig, 'ch9_1_volumetric_clouds.png')


def ch9_2_parallax():
    """视差遮蔽映射概念图 — side view of height field with parallax displacement."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Ground surface (height field profile)
    x_vals = np.linspace(1, 9, 200)
    # Create a wavy height profile
    y_vals = 1.2 + 0.5 * np.sin(x_vals * 1.5) + 0.3 * np.sin(x_vals * 3.2 + 1) + 0.15 * np.sin(x_vals * 6 + 2)
    ax.fill_between(x_vals, y_vals, 0, facecolor='#3a3a5a', edgecolor='none', zorder=2)
    ax.plot(x_vals, y_vals, color='#8888aa', linewidth=1.5, zorder=3)
    ax.fill_between(x_vals, y_vals, y_vals + 0.08, facecolor='#555588', alpha=0.5, zorder=3)

    # Height labels
    ax.text(9.3, 1.8, '高度场\n(Height Field)', color='#aaaacc', fontsize=10)

    # Camera / eye
    cam_x, cam_y = 1.5, 4.8
    eye = Circle((cam_x, cam_y), 0.25, facecolor='#333355', edgecolor=ACCENT, linewidth=2, zorder=8)
    ax.add_patch(eye)
    pupil = Circle((cam_x, cam_y), 0.08, facecolor=ACCENT, zorder=9)
    ax.add_patch(pupil)
    ax.text(cam_x, cam_y - 0.5, '视点', color=ACCENT, fontsize=11, ha='center', fontweight='bold')

    # View ray hitting the surface
    hit_x, hit_y = 5.2, 1.42
    # Draw eye ray
    ax.plot([cam_x, hit_x], [cam_y, hit_y], color=ACCENT3, linewidth=2, alpha=0.9, zorder=5)

    # Flat surface reference (dashed)
    flat_y = 1.2
    ax.hlines(flat_y, 1, 9, colors='#666688', linewidth=1, linestyles='dashed', zorder=1)
    ax.text(8.8, flat_y - 0.2, '平坦表面', color='#666688', fontsize=8, ha='right')

    # Point on flat surface (where ray WOULD hit flat plane)
    # Simple linear interpolation
    t_surface = (flat_y - cam_y) / (hit_y - cam_y)
    flat_hit_x = cam_x + t_surface * (hit_x - cam_x)
    # Actually let me compute this properly
    # Ray from (cam_x, cam_y) to (hit_x, hit_y), find x where y=flat_y
    t = (flat_y - cam_y) / (hit_y - cam_y)
    flat_hit_x = cam_x + t * (hit_x - cam_x)
    # This is the UV that would be used for flat texturing
    flat_hit = plt.Circle((flat_hit_x, flat_y), 0.12, facecolor='#666688', edgecolor='white', linewidth=1, zorder=7)
    ax.add_patch(flat_hit)

    # Actual intersection point
    actual_hit = plt.Circle((hit_x, hit_y), 0.14, facecolor=ACCENT3, edgecolor='white', linewidth=1.5, zorder=8)
    ax.add_patch(actual_hit)

    # Parallax offset arrow
    ax.annotate('', xy=(flat_hit_x, flat_y + 0.3), xytext=(hit_x, flat_y + 0.3),
                arrowprops=dict(arrowstyle='<->', color=ACCENT2, lw=1.5))
    offset_mid_x = (flat_hit_x + hit_x) / 2
    ax.text(offset_mid_x, flat_y + 0.55, '视差偏移', color=ACCENT2, fontsize=9, ha='center', fontweight='bold')

    # Labels for both points
    ax.annotate('原始UV\n(平面采样)', (flat_hit_x - 0.1, flat_y - 0.5), color='#8888aa', fontsize=8, ha='center')
    ax.annotate('偏移UV\n(真实采样)', (hit_x + 0.15, hit_y - 0.5), color=ACCENT3, fontsize=8, ha='center')

    # Texture coordinates visualization
    ax.annotate('纹理坐标\ns = s0 + h * tan(theta)', xy=(7.2, 4.5), color='#ccddff', fontsize=10,
                ha='center', bbox=dict(boxstyle='round,pad=0.4', facecolor='#222244', edgecolor='#4444aa', alpha=0.8))

    # View angle annotation
    mid_ray_x, mid_ray_y = (cam_x + hit_x) / 2, (cam_y + hit_y) / 2
    ax.annotate('视线方向', (mid_ray_x + 0.3, mid_ray_y + 0.3), color=ACCENT3, fontsize=9, rotation=-25)

    save(fig, 'ch9_2_parallax.png')


def ch9_3_gbuffers_overview():
    """GBuffers 通道总览 — grid of all gbuffer pass types."""
    # (pid, name, shape_fn, color)
    # shape_fn draws a simple icon at center (cx, cy) with given size
    passes = [
        ('terrain', '地形\nTerrain', 'mountain', ACCENT4),
        ('water', '水面\nWater', 'wave', ACCENT),
        ('entities', '实体\nEntities', 'diamond', ACCENT3),
        ('weather', '天气\nWeather', 'raindrop', '#8888cc'),
        ('hand', '手部\nHand', 'pentagon', ACCENT5),
        ('beaconbeam', '信标光柱\nBeacon Beam', 'star', ACCENT6),
        ('translucent', '半透明\nTranslucent', 'square', '#55bbcc'),
        ('particles', '粒子\nParticles', 'dots', ACCENT2),
        ('clouds', '云层\nClouds', 'cloud', '#aaddff'),
        ('skytext', '天空文字\nSky Text', 'text_icon', '#ccaa88'),
    ]

    def draw_icon(ax, cx, cy, shape, color, size=0.4):
        """Draw a simple geometric icon."""
        if shape == 'mountain':
            ax.add_patch(Polygon([(cx - size, cy - size*0.6), (cx, cy + size), (cx + size, cy - size*0.6)],
                                 facecolor='none', edgecolor=color, linewidth=2))
        elif shape == 'wave':
            xs = np.linspace(cx - size, cx + size, 40)
            ys = cy + size * 0.3 * np.sin(xs * 8)
            ax.plot(xs, ys, color=color, linewidth=2)
        elif shape == 'diamond':
            ax.add_patch(Polygon([(cx, cy + size), (cx + size, cy), (cx, cy - size), (cx - size, cy)],
                                 facecolor='none', edgecolor=color, linewidth=2))
        elif shape == 'raindrop':
            ax.plot([cx - size*0.5, cx, cx + size*0.5], [cy - size, cy + size, cy - size], color=color, linewidth=2)
        elif shape == 'pentagon':
            n = 5
            pts = [(cx + size*np.cos(2*np.pi*i/n - np.pi/2), cy + size*np.sin(2*np.pi*i/n - np.pi/2)) for i in range(n)]
            ax.add_patch(Polygon(pts, facecolor='none', edgecolor=color, linewidth=2))
        elif shape == 'star':
            n = 5
            pts_outer = [(cx + size*np.cos(2*np.pi*i/n - np.pi/2), cy + size*np.sin(2*np.pi*i/n - np.pi/2)) for i in range(n)]
            pts_inner = [(cx + size*0.4*np.cos(2*np.pi*i/n + np.pi/n - np.pi/2), cy + size*0.4*np.sin(2*np.pi*i/n + np.pi/n - np.pi/2)) for i in range(n)]
            star_pts = []
            for o, i in zip(pts_outer, pts_inner):
                star_pts.append(o); star_pts.append(i)
            ax.add_patch(Polygon(star_pts, facecolor='none', edgecolor=color, linewidth=2))
        elif shape == 'square':
            ax.add_patch(Rectangle((cx - size*0.7, cy - size*0.7), size*1.4, size*1.4,
                                    facecolor='none', edgecolor=color, linewidth=2))
        elif shape == 'dots':
            for dx, dy in [(-0.3, -0.15), (0.1, 0.2), (0.3, -0.25), (-0.15, 0.05), (0.2, -0.05)]:
                ax.add_patch(Circle((cx + dx, cy + dy), 0.06, facecolor=color, edgecolor='none'))
        elif shape == 'cloud':
            for dx, dy, r in [(0, 0.05, 0.2), (-0.2, -0.08, 0.15), (0.2, -0.05, 0.17), (-0.1, 0.15, 0.12)]:
                ax.add_patch(Circle((cx + dx, cy + dy), r, facecolor='none', edgecolor=color, linewidth=1.5))
        elif shape == 'text_icon':
            ax.add_patch(Rectangle((cx - size*0.5, cy - size*0.3), size, size*0.6,
                                    facecolor='none', edgecolor=color, linewidth=2))
            ax.plot([cx - size*0.35, cx + size*0.35], [cy + 0.02, cy + 0.02], color=color, linewidth=1)
            ax.plot([cx - size*0.2, cx + size*0.2], [cy - 0.15, cy - 0.15], color=color, linewidth=1)

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(5, 7.5, 'GBuffers 通道总览', color='white', fontsize=18, ha='center', fontweight='bold')

    cols = 5
    rows = 2
    cell_w = 1.6
    cell_h = 2.2
    x_start = 0.8
    y_start = 4.6

    for i, (pid, name, shape, color) in enumerate(passes):
        col = i % cols
        row = i // cols
        cx = x_start + col * (cell_w + 0.25)
        cy = y_start - row * (cell_h + 0.3)

        # Card background
        card = FancyBboxPatch((cx, cy - cell_h + 0.3), cell_w, cell_h,
                               boxstyle="round,pad=0.15",
                               facecolor='#222240', edgecolor=color, linewidth=1.2, alpha=0.9, zorder=2)
        ax.add_patch(card)

        # Icon (geometric shape)
        draw_icon(ax, cx + cell_w / 2, cy - 0.35, shape, color)

        # Colored accent line
        ax.plot([cx + 0.2, cx + cell_w - 0.2], [cy - 0.75, cy - 0.75], color=color, linewidth=2, zorder=3)

        # Label
        ax.text(cx + cell_w / 2, cy - 1.15, name, color='white', fontsize=10, ha='center', va='top', zorder=3,
                linespacing=1.3)

    # Arrow showing data flow
    ax.annotate('', xy=(9.2, 3.0), xytext=(9.2, 5.0),
                arrowprops=dict(arrowstyle='->', color=ACCENT, lw=2))
    ax.text(9.5, 4.0, '合成\n→', color=ACCENT, fontsize=10, ha='center', va='center')

    save(fig, 'ch9_3_gbuffers_overview.png')


def ch9_4_cloud_project():
    """体积云效果对比 — before/after."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    fig.patch.set_facecolor(BG)

    for ax in [ax1, ax2]:
        ax.set_facecolor(BG)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.set_aspect('equal')
        ax.axis('off')

    # ── Left: plain sky ──
    # Sky gradient
    for i in range(40):
        t = i / 40
        r, g, b = 0.05 + 0.15 * (1 - t), 0.05 + 0.15 * (1 - t), 0.15 + 0.4 * (1 - t)
        color = (r, g, b)
        rect = Rectangle((0, 7.8 - i * 0.2), 10, 0.2, facecolor=color, edgecolor='none', zorder=0)
        ax1.add_patch(rect)

    # Sun
    sun = Circle((3, 5.5), 0.8, facecolor='#ffffaa', edgecolor='#ffdd88', linewidth=2, zorder=2)
    ax1.add_patch(sun)
    # Sun glow
    for r in [1.1, 1.4, 1.7]:
        glow = Circle((3, 5.5), r, facecolor='#ffffaa', alpha=0.08, edgecolor='none', zorder=1)
        ax1.add_patch(glow)

    # Ground line
    ax1.fill_between([0, 10], 2.5, 0, facecolor='#2a3a2a', zorder=3)
    ax1.hlines(2.5, 0, 10, colors='#3a5a3a', linewidth=1, zorder=3)

    ax1.text(5, 7.2, '普通天空', color='white', fontsize=16, ha='center', fontweight='bold')
    ax1.text(5, 6.6, '无体积云', color='#8888aa', fontsize=11, ha='center')

    # ── Right: volumetric clouds ──
    for i in range(40):
        t = i / 40
        r, g, b = 0.05 + 0.15 * (1 - t), 0.05 + 0.15 * (1 - t), 0.15 + 0.4 * (1 - t)
        color = (r, g, b)
        rect = Rectangle((0, 7.8 - i * 0.2), 10, 0.2, facecolor=color, edgecolor='none', zorder=0)
        ax2.add_patch(rect)

    sun2 = Circle((3, 5.5), 0.8, facecolor='#ffffaa', edgecolor='#ffdd88', linewidth=2, zorder=4)
    ax2.add_patch(sun2)
    for r in [1.1, 1.4, 1.7]:
        glow = Circle((3, 5.5), r, facecolor='#ffffaa', alpha=0.08, edgecolor='none', zorder=3)
        ax2.add_patch(glow)

    # Clouds
    rng = np.random.default_rng(99)
    for _ in range(30):
        cx = rng.uniform(0.5, 9.5)
        cy = rng.uniform(3.5, 6.0)
        rx = rng.uniform(0.6, 1.8)
        ry = rng.uniform(0.15, 0.35)
        alpha = rng.uniform(0.15, 0.45)
        cloud_shape = 'circle' if rng.random() > 0.3 else 'ellipse'
        if cloud_shape == 'circle':
            blob = Circle((cx, cy), rx / 2, facecolor='white', alpha=alpha, edgecolor='none', zorder=5)
        else:
            blob = FancyBboxPatch((cx - rx, cy - ry), rx * 2, ry * 2,
                                   boxstyle="round,pad=0.1",
                                   facecolor='white', alpha=alpha, edgecolor='none', zorder=5)
        ax2.add_patch(blob)

    ax2.fill_between([0, 10], 2.5, 0, facecolor='#2a3a2a', zorder=6)
    ax2.hlines(2.5, 0, 10, colors='#3a5a3a', linewidth=1, zorder=6)

    ax2.text(5, 7.2, '体积云天空', color='white', fontsize=16, ha='center', fontweight='bold')
    ax2.text(5, 6.6, '光线步进渲染', color=ACCENT, fontsize=11, ha='center')

    # Divider
    ax1.text(9.8, 4, '→', color=ACCENT2, fontsize=24, ha='right', va='center', alpha=0.5)

    save(fig, 'ch9_4_cloud_project.png')


# ═══════════════════════════════════════════════════════════════════
# Chapter 10
# ═══════════════════════════════════════════════════════════════════

def ch10_1_dimensions():
    """三个维度对比 — Overworld / Nether / End."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 5.5))
    fig.patch.set_facecolor(BG)

    dims = [
        (ax1, '主世界', 'Overworld', '#4488ff', '#2266cc', 'sun', True, '蓝色天空 · 太阳 · 昼夜循环'),
        (ax2, '下界', 'Nether', '#cc3333', '#881111', 'fire', False, '红色辉光 · 无天空 · 熔岩照明'),
        (ax3, '末地', 'End', '#8844cc', '#331166', 'void', False, '紫色虚空 · 无天空 · 末影照明'),
    ]

    for ax, name, ename, top_c, bot_c, icon_type, has_sun, desc in dims:
        ax.set_facecolor(BG)
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 8)
        ax.axis('off')

        # Sky gradient
        for i in range(30):
            t = i / 30
            r = float(int(top_c[1:3], 16)) / 255
            g = float(int(top_c[3:5], 16)) / 255
            b = float(int(top_c[5:7], 16)) / 255
            r2 = float(int(bot_c[1:3], 16)) / 255
            g2 = float(int(bot_c[3:5], 16)) / 255
            b2 = float(int(bot_c[5:7], 16)) / 255
            cr = min(1.0, r * (1 - t) + r2 * t + 0.05)
            cg = min(1.0, g * (1 - t) + g2 * t + 0.05)
            cb = min(1.0, b * (1 - t) + b2 * t + 0.05)
            color = (cr, cg, cb)
            rect = Rectangle((0, 7.5 - i * 0.25), 8, 0.25, facecolor=color, edgecolor='none', zorder=0)
            ax.add_patch(rect)

        # Ground
        ax.fill_between([0, 8], 1.8, 0, facecolor='#1a1a2e', zorder=2)
        ax.hlines(1.8, 0, 8, colors='#3a3a5a', linewidth=1, zorder=2)

        # Icon (drawn as shapes)
        if icon_type == 'sun':
            sun_icon = Circle((4, 5.0), 0.5, facecolor='#ffdd44', edgecolor='#ffaa00', linewidth=1.5, zorder=5)
            ax.add_patch(sun_icon)
            for angle in range(0, 360, 45):
                rad = np.radians(angle)
                ax.plot([4 + 0.55*np.cos(rad), 4 + 0.72*np.cos(rad)],
                        [5.0 + 0.55*np.sin(rad), 5.0 + 0.72*np.sin(rad)],
                        color='#ffdd44', linewidth=1.5, zorder=4)
        elif icon_type == 'fire':
            flame = Polygon([(4, 4.3), (3.7, 5.5), (4, 5.0), (4.3, 5.5)],
                             facecolor='#ff6633', edgecolor='#ff3300', linewidth=1.5, zorder=5)
            ax.add_patch(flame)
            flame2 = Polygon([(4, 4.4), (3.85, 5.2), (4, 4.9), (4.15, 5.2)],
                              facecolor='#ffaa00', edgecolor='none', zorder=6)
            ax.add_patch(flame2)
        elif icon_type == 'void':
            void_c = Circle((4, 5.0), 0.55, facecolor='#221144', edgecolor='#6644aa', linewidth=2, zorder=5)
            ax.add_patch(void_c)
            # Small stars
            rng_v = np.random.default_rng(7)
            for _ in range(8):
                sx = 4 + rng_v.uniform(-0.4, 0.4)
                sy = 5.0 + rng_v.uniform(-0.4, 0.4)
                ax.plot(sx, sy, '+', color='#aa88ff', markersize=4, zorder=6)

        # Sun (only for overworld)
        if has_sun:
            sun = Circle((5.5, 5.5), 0.6, facecolor='#ffffbb', edgecolor='#ffdd66', linewidth=1.5, zorder=3)
            ax.add_patch(sun)
            for r in [0.9, 1.2]:
                glow = Circle((5.5, 5.5), r, facecolor='#ffffbb', alpha=0.06, edgecolor='none', zorder=2)
                ax.add_patch(glow)

        # Dimension name
        ax.text(4, 7.3, name, color='white', fontsize=16, ha='center', fontweight='bold')
        ax.text(4, 6.8, ename, color='#8888aa', fontsize=9, ha='center')

        # Description
        ax.text(4, 1.2, desc, color='#aaaacc', fontsize=9, ha='center')
        ax.text(4, 0.7, '天空可见: ' + ('是' if has_sun else '否'), color='#8888aa', fontsize=8, ha='center')

        # Border
        border = FancyBboxPatch((0.2, 0.2), 7.6, 7.6, boxstyle="round,pad=0.2",
                                 facecolor='none', edgecolor='#444466', linewidth=1.2, zorder=10)
        ax.add_patch(border)

    save(fig, 'ch10_1_dimensions.png')


def ch10_2_config_ui():
    """配置界面示意 — wireframe shader settings UI."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # Title bar
    title_bar = FancyBboxPatch((0.5, 10.8), 11, 0.9, boxstyle="round,pad=0.1",
                                facecolor='#222244', edgecolor='#4444aa', linewidth=1.5, zorder=3)
    ax.add_patch(title_bar)
    ax.text(6, 11.25, '光影设置 · Iris Shader', color='white', fontsize=16, ha='center', fontweight='bold')

    # Sidebar
    sidebar = FancyBboxPatch((0.5, 0.5), 2.5, 9.8, boxstyle="round,pad=0.1",
                              facecolor='#1e1e38', edgecolor='#333355', linewidth=1, zorder=2)
    ax.add_patch(sidebar)
    tabs = ['光照', '体积云', '水面', '后处理', '性能']
    for i, tab in enumerate(tabs):
        y = 9.8 - i * 1.6
        is_active = (i == 1)
        tab_color = ACCENT if is_active else '#666688'
        bg_color = '#282850' if is_active else 'none'
        if is_active:
            tab_bg = FancyBboxPatch((0.6, y - 0.5), 2.3, 1.3, boxstyle="round,pad=0.05",
                                     facecolor=bg_color, edgecolor='none', zorder=4)
            ax.add_patch(tab_bg)
        ax.text(1.75, y, tab, color=tab_color, fontsize=10, ha='center', fontweight='bold' if is_active else 'normal')

    # Main content area — volume cloud settings
    main = FancyBboxPatch((3.5, 0.5), 8, 9.8, boxstyle="round,pad=0.1",
                           facecolor='#222240', edgecolor='#3a3a6a', linewidth=1, zorder=2)
    ax.add_patch(main)

    # Section header
    ax.text(7.5, 9.8, '体积云设置', color='white', fontsize=14, ha='center', fontweight='bold')
    ax.hlines(9.4, 4, 11, colors='#4444aa', linewidth=1)

    y_start = 8.5
    row_h = 1.3

    # Row 1: Toggle
    ax.text(4, y_start, '启用体积云', color=FG, fontsize=11, va='center')
    toggle_bg = FancyBboxPatch((9.5, y_start - 0.2), 1.5, 0.6, boxstyle="round,pad=0.05",
                                facecolor=ACCENT4, edgecolor='none', zorder=4)
    ax.add_patch(toggle_bg)
    toggle_knob = Circle((10.2, y_start + 0.1), 0.2, facecolor='white', edgecolor='#44aa44', linewidth=1, zorder=5)
    ax.add_patch(toggle_knob)
    ax.text(10.75, y_start, '开', color=ACCENT4, fontsize=9, ha='center')

    # Row 2: Slider 1 — quality
    y = y_start - row_h
    ax.text(4, y, '渲染质量', color=FG, fontsize=10, va='center')
    slider_bg = Rectangle((6.5, y - 0.08), 4.5, 0.2, facecolor='#333355', edgecolor='#555588', linewidth=0.8, zorder=3)
    ax.add_patch(slider_bg)
    slider_fill = Rectangle((6.5, y - 0.08), 3.0, 0.2, facecolor=ACCENT, edgecolor='none', zorder=4)
    ax.add_patch(slider_fill)
    knob = Circle((9.5, y + 0.02), 0.18, facecolor=ACCENT, edgecolor='white', linewidth=1.2, zorder=5)
    ax.add_patch(knob)
    ax.text(11.3, y, '高', color='white', fontsize=9)

    # Row 3: Slider 2 — render distance
    y = y_start - row_h * 2
    ax.text(4, y, '渲染距离', color=FG, fontsize=10, va='center')
    slider_bg2 = Rectangle((6.5, y - 0.08), 4.5, 0.2, facecolor='#333355', edgecolor='#555588', linewidth=0.8, zorder=3)
    ax.add_patch(slider_bg2)
    slider_fill2 = Rectangle((6.5, y - 0.08), 2.2, 0.2, facecolor=ACCENT, edgecolor='none', zorder=4)
    ax.add_patch(slider_fill2)
    knob2 = Circle((8.7, y + 0.02), 0.18, facecolor=ACCENT, edgecolor='white', linewidth=1.2, zorder=5)
    ax.add_patch(knob2)
    ax.text(11.3, y, '16', color='white', fontsize=9)

    # Row 4: Slider 3 — density
    y = y_start - row_h * 3
    ax.text(4, y, '云层密度', color=FG, fontsize=10, va='center')
    slider_bg3 = Rectangle((6.5, y - 0.08), 4.5, 0.2, facecolor='#333355', edgecolor='#555588', linewidth=0.8, zorder=3)
    ax.add_patch(slider_bg3)
    slider_fill3 = Rectangle((6.5, y - 0.08), 3.8, 0.2, facecolor=ACCENT, edgecolor='none', zorder=4)
    ax.add_patch(slider_fill3)
    knob3 = Circle((10.3, y + 0.02), 0.18, facecolor=ACCENT, edgecolor='white', linewidth=1.2, zorder=5)
    ax.add_patch(knob3)
    ax.text(11.3, y, '密', color='white', fontsize=9)

    # Row 5: Dropdown
    y = y_start - row_h * 4
    ax.text(4, y, '云类型', color=FG, fontsize=10, va='center')
    dropdown = FancyBboxPatch((6.5, y - 0.25), 4.2, 0.7, boxstyle="round,pad=0.08",
                               facecolor='#333355', edgecolor='#555588', linewidth=1, zorder=3)
    ax.add_patch(dropdown)
    ax.text(7.0, y + 0.05, '层级云 ▼', color='white', fontsize=10, va='center')
    # Dropdown arrow
    ax.plot([10.3, 10.5, 10.7], [y + 0.15, y - 0.05, y + 0.15], color='#8888aa', linewidth=1.5)

    # Row 6: Checkbox
    y = y_start - row_h * 5
    chk = FancyBboxPatch((4.0, y - 0.2), 0.5, 0.5, boxstyle="round,pad=0.05",
                          facecolor=ACCENT, edgecolor='white', linewidth=1.2, zorder=4)
    ax.add_patch(chk)
    # Draw checkmark as lines
    ax.plot([4.1, 4.25, 4.45], [y + 0.02, y - 0.1, y + 0.1], color='white', linewidth=2, zorder=5)
    ax.text(4.8, y, '使用时间重投影', color=FG, fontsize=10, va='center')

    # Row 7: Checkbox
    y = y_start - row_h * 6
    chk2 = FancyBboxPatch((4.0, y - 0.2), 0.5, 0.5, boxstyle="round,pad=0.05",
                           facecolor=ACCENT, edgecolor='white', linewidth=1.2, zorder=4)
    ax.add_patch(chk2)
    ax.plot([4.1, 4.25, 4.45], [y + 0.02, y - 0.1, y + 0.1], color='white', linewidth=2, zorder=5)
    ax.text(4.8, y, '动态天气交互', color=FG, fontsize=10, va='center')

    save(fig, 'ch10_2_config_ui.png')


def ch10_3_compat():
    """兼容性决策流程 — IS_IRIS → MC_VERSION → GPU → fallback."""
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Helper to draw decision box
    def decision_box(cx, cy, text, subtext='', color=ACCENT, w=2.8, h=1.0):
        box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.2",
                              facecolor='#1e1e3a', edgecolor=color, linewidth=2, zorder=5)
        ax.add_patch(box)
        ax.text(cx, cy + 0.1, text, color='white', fontsize=11, ha='center', fontweight='bold')
        if subtext:
            ax.text(cx, cy - 0.3, subtext, color='#8888aa', fontsize=8, ha='center')

    def path_box(cx, cy, text, color=ACCENT4, w=2.2, h=0.7):
        box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.15",
                              facecolor='#1a2a1a', edgecolor=color, linewidth=1.5, zorder=5)
        ax.add_patch(box)
        ax.text(cx, cy, text, color=color, fontsize=10, ha='center', fontweight='bold')

    def arrow(x1, y1, x2, y2, label='', color='#666688', lw=1.2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle='->', color=color, lw=lw, connectionstyle='arc3,rad=0'))
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx - 0.3, my + 0.2, label, color='#8888aa', fontsize=8, ha='right')

    # Root
    decision_box(3, 7, 'IS_IRIS?', '检测是否为 Iris 加载', ACCENT6, w=3.0)

    # Yes branch
    arrow(4.2, 7, 5.5, 7, '是')
    decision_box(7, 7, 'MC_VERSION?', '1.20+ / 1.19 / 1.18-', ACCENT, w=3.2)

    # Version branches
    arrow(7, 6.2, 2.2, 5.0, '1.20+')
    arrow(7, 6.2, 7, 5.0, '1.19')
    arrow(7, 6.2, 11.8, 5.0, '1.18-')

    # GPU level
    decision_box(2.2, 4.0, 'GPU 检测', 'Vendor: NV/AMD/Intel', ACCENT5, w=2.8)
    decision_box(7, 4.0, 'GPU 检测', 'Vendor: NV/AMD/Intel', ACCENT5, w=2.8)
    decision_box(11.8, 4.0, '降级路径', '无高级特性', ACCENT2, w=2.5)

    # GPU branches
    for base_x in [2.2, 7]:
        arrow(base_x - 0.8, 3.2, base_x - 2.2, 2.0, 'NV')
        arrow(base_x, 3.2, base_x, 2.0, 'AMD')
        arrow(base_x + 0.8, 3.2, base_x + 2.2, 2.0, 'Intel')

    # Result boxes
    path_box(0, 1.2, '完整路径\n全特性', ACCENT4)
    path_box(2.2, 1.2, '标准路径\n核心特性', ACCENT3)
    path_box(4.4, 1.2, '基础路径\n限制特性', ACCENT6)
    path_box(4.8, 1.2, '完整路径\n全特性', ACCENT4)
    path_box(7, 1.2, '标准路径\n核心特性', ACCENT3)
    path_box(9.2, 1.2, '基础路径\n限制特性', ACCENT6)
    path_box(11.8, 1.2, '最低兼容\n无光影', ACCENT2)

    # No branch (right side)
    arrow(3, 6.6, 10, 6.6, '否 (OptiFine)')
    path_box(12.5, 6.6, 'OF 兼容\n降级路径', ACCENT2, w=2.5)

    # Title
    ax.text(7, 7.8, '兼容性决策流程', color='white', fontsize=16, ha='center', fontweight='bold')

    # Legend
    legend_y = 0.3
    for i, (color, label) in enumerate([(ACCENT, '决策节点'), (ACCENT4, '完整路径'), (ACCENT3, '标准路径'), (ACCENT6, '降级路径')]):
        lx = 10.5
        ax.plot([lx - 0.3, lx + 0.1], [legend_y - i * 0.25, legend_y - i * 0.25], color=color, linewidth=4)
        ax.text(lx + 0.3, legend_y - i * 0.25, label, color='#8888aa', fontsize=7, va='center')

    save(fig, 'ch10_3_compat.png')


def ch10_4_bsl_arch():
    """BSL 架构图 — three-layer pyramid/flow."""
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(6, 8.5, 'BSL 光影架构', color='white', fontsize=18, ha='center', fontweight='bold')
    ax.text(6, 8.1, '分层设计 · 模块化 · 可扩展', color='#8888aa', fontsize=10, ha='center')

    # ── Layer 1: Dimensions (top) ──
    layer1_y = 6.5
    l1 = FancyBboxPatch((0.5, layer1_y - 0.5), 11, 1.2, boxstyle="round,pad=0.2",
                          facecolor='#222250', edgecolor=ACCENT5, linewidth=2, zorder=2)
    ax.add_patch(l1)
    ax.text(6, layer1_y + 0.4, '维度层 (Dimension)', color=ACCENT5, fontsize=13, ha='center', fontweight='bold')

    dims = ['主世界\nOverworld', '下界\nNether', '末地\nEnd']
    dim_x = [2.8, 6.0, 9.2]
    for dx, dn in zip(dim_x, dims):
        db = FancyBboxPatch((dx - 1.1, layer1_y - 0.25), 2.2, 0.7, boxstyle="round,pad=0.08",
                              facecolor='#2a2a5a', edgecolor='#5555aa', linewidth=1, zorder=3)
        ax.add_patch(db)
        ax.text(dx, layer1_y + 0.1, dn, color='#ccccff', fontsize=9, ha='center', linespacing=1.3)

    # Arrow between layer 1 and 2
    ax.annotate('', xy=(6, 4.6), xytext=(6, 5.8),
                arrowprops=dict(arrowstyle='<->', color='#5555aa', lw=1.5))
    ax.text(7, 5.2, '选择对应\n维度程序', color='#8888aa', fontsize=8, ha='center')

    # ── Layer 2: Program Templates (middle) ──
    layer2_y = 3.5
    l2 = FancyBboxPatch((0.5, layer2_y - 0.5), 11, 1.2, boxstyle="round,pad=0.2",
                          facecolor='#222250', edgecolor=ACCENT, linewidth=2, zorder=2)
    ax.add_patch(l2)
    ax.text(6, layer2_y + 0.4, '程序模板层 (Program Templates)', color=ACCENT, fontsize=13, ha='center', fontweight='bold')

    progs = ['gbuffers_\nterrain', 'gbuffers_\nwater', 'composite', 'deferred', 'shadow']
    prog_x = [1.8, 3.8, 6.0, 8.2, 10.2]
    for px, pn in zip(prog_x, progs):
        pw = 1.7 if '\n' not in pn else 1.7
        pb = FancyBboxPatch((px - pw / 2, layer2_y - 0.25), pw, 0.7, boxstyle="round,pad=0.08",
                              facecolor='#1a2a3a', edgecolor='#3388aa', linewidth=1, zorder=3)
        ax.add_patch(pb)
        ax.text(px, layer2_y + 0.1, pn, color='#aaddff', fontsize=8, ha='center', linespacing=1.2)

    # Arrow between layer 2 and 3
    ax.annotate('', xy=(6, 1.6), xytext=(6, 2.8),
                arrowprops=dict(arrowstyle='<->', color='#5555aa', lw=1.5))
    ax.text(7, 2.2, '引用共享\n功能模块', color='#8888aa', fontsize=8, ha='center')

    # ── Layer 3: Library Modules (bottom) ──
    layer3_y = 1.0
    l3 = FancyBboxPatch((0.5, 0.2), 11, 1.0, boxstyle="round,pad=0.2",
                          facecolor='#222250', edgecolor=ACCENT4, linewidth=2, zorder=2)
    ax.add_patch(l3)
    ax.text(6, layer3_y + 0.1, '库模块层 (Library Modules)', color=ACCENT4, fontsize=13, ha='center', fontweight='bold')

    libs = ['lighting', 'shadows', 'tonemap', 'PBR', 'BRDF', 'noise']
    lib_x = [1.5, 3.3, 5.1, 6.9, 8.7, 10.5]
    for lx, ln in zip(lib_x, libs):
        lb = FancyBboxPatch((lx - 0.75, 0.35), 1.5, 0.55, boxstyle="round,pad=0.06",
                              facecolor='#1a2a1a', edgecolor='#44aa44', linewidth=1, zorder=3)
        ax.add_patch(lb)
        ax.text(lx, 0.62, ln, color='#aaffaa', fontsize=8, ha='center')

    # Side annotations
    ax.annotate('抽象级别\n高 ↑', xy=(0.2, 4.5), xytext=(0.2, 4.5),
                color='#666688', fontsize=9, ha='center', rotation=90)
    ax.annotate('复用性\n高 ↑', xy=(11.8, 4.5), xytext=(11.8, 4.5),
                color='#666688', fontsize=9, ha='center', rotation=-90)

    save(fig, 'ch10_4_bsl_arch.png')


def ch10_5_next_steps():
    """学习路径时间线 — roadmap/timeline."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')

    ax.text(7, 5.5, 'Iris Shader 学习路径', color='white', fontsize=18, ha='center', fontweight='bold')
    ax.text(7, 5.1, '从零到工业级光影开发', color='#8888aa', fontsize=10, ha='center')

    # Timeline line
    ax.hlines(3, 1, 13, colors='#4444aa', linewidth=2, zorder=1)

    # Milestone dots
    milestones = [
        (1.5, ACCENT4), (5, ACCENT3), (8.5, ACCENT6), (12, ACCENT2),
    ]
    for mx, mc in milestones:
        dot = Circle((mx, 3), 0.15, facecolor=mc, edgecolor='white', linewidth=1.5, zorder=4)
        ax.add_patch(dot)

    # Nodes
    nodes = [
        (1.5, 4.2, '快速体验', '3 小时', ACCENT4,
         '下载 Iris\n安装默认光影\n感受基础效果'),
        (5, 4.2, '扎实基础', '3 周', ACCENT3,
         '学习 GLSL 语法\n理解渲染管线\n修改简单参数'),
        (8.5, 4.2, '完整光影', '2 月', ACCENT6,
         '实现完整 shader\n体积云 / 水面\n后处理特效'),
        (12, 4.2, '工业级能力', '∞', ACCENT2,
         '性能优化\n多 GPU 兼容\n贡献开源社区'),
    ]

    for mx, my, title, time_str, color, desc in nodes:
        # Node card
        card_w, card_h = 2.8, 1.8
        card = FancyBboxPatch((mx - card_w / 2, my - card_h / 2), card_w, card_h,
                               boxstyle="round,pad=0.15",
                               facecolor='#222240', edgecolor=color, linewidth=1.5, zorder=3)
        ax.add_patch(card)

        # Title
        ax.text(mx, my + 0.55, title, color='white', fontsize=12, ha='center', fontweight='bold')
        ax.text(mx, my + 0.2, time_str, color=color, fontsize=10, ha='center', fontweight='bold')

        # Desc
        ax.text(mx, my - 0.5, desc, color='#aaaacc', fontsize=8, ha='center', linespacing=1.4)

        # Connector
        ax.plot([mx, mx], [3.15, my - card_h / 2], color=color, linewidth=1.5, alpha=0.6, zorder=2)

    # Arrow between dots
    for i in range(len(milestones) - 1):
        x1, c1 = milestones[i]
        x2, c2 = milestones[i + 1]
        ax.annotate('', xy=(x2 - 0.25, 3), xytext=(x1 + 0.25, 3),
                     arrowprops=dict(arrowstyle='->', color='#5555aa', lw=1.5))

    # Arrow annotations along timeline
    for (x1, _), (x2, _) in zip(milestones[:-1], milestones[1:]):
        mx = (x1 + x2) / 2
        ax.text(mx, 2.6, '→', color='#5555aa', fontsize=14, ha='center')

    save(fig, 'ch10_5_next_steps.png')


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f"输出目录: {OUTDIR}")
    print("生成图表...\n")

    print("[Chapter 9]")
    ch9_1_volumetric_clouds()
    ch9_2_parallax()
    ch9_3_gbuffers_overview()
    ch9_4_cloud_project()

    print("\n[Chapter 10]")
    ch10_1_dimensions()
    ch10_2_config_ui()
    ch10_3_compat()
    ch10_4_bsl_arch()
    ch10_5_next_steps()

    print("\n全部完成！")
