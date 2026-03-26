#!/usr/bin/env python3
"""
generate_diagrams.py
Generates all proposal figures for the GSoC 2026 SITL Model Generation proposal.
Run from the repo root: python3 docs/generate_diagrams.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as FancyArrow
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# FIGURE 1: Pipeline Architecture
# ─────────────────────────────────────────────────────────────
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    ax.axis('off')
    fig.patch.set_facecolor('#FAFAFA')

    COLORS = {
        'input':    '#4A90D9',
        'stage1':   '#5BA55B',
        'stage2':   '#E8A838',
        'stage3':   '#9B59B6',
        'stage4':   '#E74C3C',
        'output':   '#2C7BB6',
        'arrow':    '#555555',
        'text':     'white',
        'subtext':  '#333333',
    }

    def box(ax, x, y, w, h, label, sublabel, color, fontsize=9):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white',
                              linewidth=1.5, zorder=3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color='white', zorder=4)
        ax.text(x + w/2, y + h*0.28, sublabel,
                ha='center', va='center', fontsize=6.5,
                color='white', alpha=0.9, zorder=4, wrap=True)

    def arrow(ax, x1, x2, y):
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle='->', color=COLORS['arrow'],
                                   lw=1.8), zorder=5)

    # Input
    box(ax, 0.2, 2.8, 2.0, 1.4, 'DataFlash Log', '.bin file\n(real flight)',
        COLORS['input'])

    arrow(ax, 2.2, 2.8, 3.5)

    # Stage 1
    box(ax, 2.8, 2.8, 2.4, 1.4, 'Stage 1\nLog Parser',
        'pymavlink DFReader\nTime alignment\nSegment detection',
        COLORS['stage1'])

    arrow(ax, 5.2, 5.8, 3.5)

    # Stage 2
    box(ax, 5.8, 2.8, 2.4, 1.4, 'Stage 2\nSegment Selector',
        'Hover windows\nRate steps\nSYSID chirp windows',
        COLORS['stage2'])

    arrow(ax, 8.2, 8.8, 3.5)

    # Stage 3
    box(ax, 8.8, 2.8, 2.4, 1.4, 'Stage 3\nDynamics Optimizer',
        'Grey-box NLLS\nInertia, drag, thrust\nConfidence intervals',
        COLORS['stage3'])

    arrow(ax, 11.2, 11.8, 3.5)

    # Stage 4
    box(ax, 11.8, 2.8, 2.4, 1.4, 'Stage 4\nSensor Estimator',
        'IMU bias + noise\nScale factors\n.parm writer',
        COLORS['stage4'])

    # Outputs (below, from stage 3 and 4)
    arrow(ax, 10.0, 10.0, 2.8)   # down from stage 3
    arrow(ax, 13.0, 13.0, 2.8)   # down from stage 4

    box(ax, 8.8, 1.1, 2.4, 1.5, 'JSON Frame Model',
        'mass, inertia\ndisc_area, mdrag_coef\nSITL-compatible',
        COLORS['output'], fontsize=8)

    box(ax, 11.8, 1.1, 2.4, 1.5, 'SIM_* .parm File',
        'ACC_BIAS, GYR_BIAS\nACC_RND, GYR_RND\nMAVProxy loadable',
        COLORS['output'], fontsize=8)

    # Validation loop arrow
    ax.annotate('', xy=(14.2, 3.5), xytext=(14.2, 5.5),
                arrowprops=dict(arrowstyle='->', color='#888888',
                                lw=1.5, linestyle='dashed'), zorder=5)
    box(ax, 13.5, 5.5, 2.2, 1.0, 'Validation',
        'RMS error, PSD,\nCI metrics',
        '#888888', fontsize=8)

    ax.text(8.0, 6.6, 'SITL Model Generation Pipeline',
            ha='center', fontsize=14, fontweight='bold', color='#222222')
    ax.text(8.0, 6.1, 'ArduPilot DataFlash .bin log  ->  tuned SITL frame model + sensor parameters',
            ha='center', fontsize=9, color='#555555', style='italic')

    plt.tight_layout()
    path = os.path.join(OUT, "fig1_pipeline.png")
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────
# FIGURE 2: Gantt Chart Timeline
# ─────────────────────────────────────────────────────────────
def fig_gantt():
    fig, ax = plt.subplots(figsize=(18, 8))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    phases = [
        ("Community Bonding",       0,   4,  '#AAAAAA'),
        ("Phase 1: Log Parser",     4,   7,  '#5BA55B'),
        ("Phase 2: Dynamics Model", 7,  10,  '#E8A838'),
        ("Phase 3: Uncertainty",   10,  12,  '#9B59B6'),
        ("Phase 4: Sensor + CLI",  12,  14,  '#E74C3C'),
        ("Phase 5: Validation",    14,  16,  '#2C7BB6'),
        ("Buffer / Polish",        15,  16,  '#BBBBBB'),
    ]

    # Milestone labels rotated vertically to avoid overlapping title or each other
    milestones = [
        (7,  "M1: Parser complete — 3 logs, CI passing"),
        (10, "M2: JSON model loads in SITL"),
        (12, "M3: CIs on all parameters"),
        (14, "M4: Full CLI end-to-end"),
        (16, "M5: ≥30% error reduction vs default"),
    ]

    n = len(phases)
    for i, (label, start, end, color) in enumerate(phases):
        y = n - i - 1
        bar_width = end - start
        ax.barh(y, bar_width, left=start, height=0.68,
                color=color, alpha=0.88, edgecolor='white', linewidth=1.5)
        # Show text only if bar is wide enough; otherwise use abbreviated label
        if bar_width >= 2:
            fs = 10.5 if bar_width >= 3 else 9.5
            ax.text(start + bar_width / 2, y, label,
                    va='center', ha='center', fontsize=fs,
                    fontweight='bold', color='white', clip_on=True)
        else:
            # 1-week buffer bar — abbreviated label outside right edge
            ax.text(end + 0.1, y, label,
                    va='center', ha='left', fontsize=8.5,
                    fontweight='bold', color='#888888')

    for week, label in milestones:
        ax.axvline(x=week, color='#CC3333', linewidth=1.4,
                   linestyle='--', alpha=0.75, zorder=5)
        # Vertical label placed just to the right of the milestone line
        ax.text(week + 0.12, 0.35, label,
                ha='left', va='bottom', fontsize=8,
                color='#CC3333', fontweight='bold',
                rotation=90, rotation_mode='anchor')

    weeks = list(range(0, 17))
    week_labels = ['Bonding'] + [f'W{i}' for i in range(1, 17)]
    ax.set_xticks(weeks)
    ax.set_xticklabels(week_labels, fontsize=9.5)
    ax.set_yticks([])
    ax.set_xlim(0, 18.0)
    ax.set_ylim(-0.5, n - 0.3)
    ax.set_xlabel('Week', fontsize=11)
    ax.set_title('GSoC 2026 Development Timeline  (350 hours over 12 weeks)',
                 fontsize=13, fontweight='bold', pad=14)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(OUT, "fig2_timeline.png")
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────
# FIGURE 3: Sim-to-Real Gap Concept
# ─────────────────────────────────────────────────────────────
def fig_sim_real_gap():
    np.random.seed(42)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.patch.set_facecolor('#FAFAFA')
    t = np.linspace(0, 4*np.pi, 300)

    # Panel 1: Real flight
    ax = axes[0]
    real_signal = np.sin(t) * np.exp(-0.1*t) + 0.08 * np.random.randn(len(t))
    ax.plot(t, real_signal, color='#2C7BB6', lw=2, label='Real flight (IMU)')
    ax.set_title('Real Vehicle\n(DataFlash .bin log)', fontweight='bold', fontsize=10)
    ax.set_xlabel('Time (s)', fontsize=9)
    ax.set_ylabel('Roll rate (rad/s)', fontsize=9)
    ax.legend(fontsize=8)
    ax.set_facecolor('#F5F5F5')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Panel 2: Default SITL (poor match)
    ax = axes[1]
    default_sim = np.sin(t * 1.18) * np.exp(-0.06*t) * 1.3
    ax.plot(t, real_signal, color='#2C7BB6', lw=1.5, alpha=0.5, label='Real')
    ax.plot(t, default_sim, color='#E74C3C', lw=2, linestyle='--', label='Default SITL')
    ax.fill_between(t, real_signal, default_sim, alpha=0.15, color='#E74C3C')
    ax.set_title('Default SITL Model\n(generic parameters, large gap)', fontweight='bold', fontsize=10)
    ax.set_xlabel('Time (s)', fontsize=9)
    ax.set_ylabel('Roll rate (rad/s)', fontsize=9)
    ax.legend(fontsize=8)
    ax.text(6, 0.8, 'Sim-to-real\ngap', color='#E74C3C', fontsize=9,
            ha='center', fontweight='bold')
    ax.set_facecolor('#F5F5F5')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Panel 3: Fitted SITL (good match)
    ax = axes[2]
    fitted_sim = np.sin(t) * np.exp(-0.1*t) * 1.02 + 0.02 * np.random.randn(len(t))
    ax.plot(t, real_signal, color='#2C7BB6', lw=1.5, alpha=0.5, label='Real')
    ax.plot(t, fitted_sim, color='#5BA55B', lw=2, linestyle='--', label='Fitted SITL')
    ax.fill_between(t, real_signal, fitted_sim, alpha=0.1, color='#5BA55B')
    ax.set_title('Fitted SITL Model\n(this project, small gap)', fontweight='bold', fontsize=10)
    ax.set_xlabel('Time (s)', fontsize=9)
    ax.set_ylabel('Roll rate (rad/s)', fontsize=9)
    ax.legend(fontsize=8)
    ax.text(6, 0.8, 'Reduced\ngap', color='#5BA55B', fontsize=9,
            ha='center', fontweight='bold')
    ax.set_facecolor('#F5F5F5')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.suptitle('Sim-to-Real Gap: What This Project Fixes',
                 fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    path = os.path.join(OUT, "fig3_sim_real_gap.png")
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────
# FIGURE 4: Optimization Loop
# ─────────────────────────────────────────────────────────────
def fig_optimizer():
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(-1.0, 7.5)
    ax.axis('off')
    fig.patch.set_facecolor('#FAFAFA')

    COLORS = ['#4A90D9', '#5BA55B', '#E8A838', '#9B59B6', '#E74C3C']

    def box(ax, x, y, w, h, lines, color):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.15",
                              facecolor=color, edgecolor='white',
                              linewidth=2, zorder=3, alpha=0.9)
        ax.add_patch(rect)
        for i, line in enumerate(lines):
            fs = 11 if i == 0 else 9
            fw = 'bold' if i == 0 else 'normal'
            ax.text(x + w/2, y + h - 0.22 - i*0.32, line,
                    ha='center', va='top', fontsize=fs,
                    fontweight=fw, color='white', zorder=4)

    def arr(ax, x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#555',
                                   lw=1.8), zorder=5)

    # Main boxes — raised to y=2.8 for headroom below
    box(ax, 0.2, 2.8, 2.4, 1.8,
        ['Flight Log', '.bin DataFlash', 'CTUN, IMU, RCOU'], COLORS[0])
    arr(ax, 2.6, 3.7, 3.2, 3.7)

    box(ax, 3.2, 2.8, 2.4, 1.8,
        ['Physics Model', 'Rigid body', 'thrust + drag'], COLORS[1])
    arr(ax, 5.6, 3.7, 6.2, 3.7)

    box(ax, 6.2, 2.8, 2.4, 1.8,
        ['Residual', 'sim(θ) − real', 'across windows'], COLORS[2])
    arr(ax, 8.6, 3.7, 9.2, 3.7)

    box(ax, 9.2, 2.8, 2.4, 1.8,
        ['Optimizer', 'scipy NLLS', 'Huber loss'], COLORS[3])

    # Feedback arc — curves BELOW the boxes; text sits well below the arc
    ax.annotate('', xy=(4.4, 2.8), xytext=(10.4, 2.8),
                arrowprops=dict(arrowstyle='->',
                                connectionstyle='arc3,rad=-0.4',
                                color='#E74C3C', lw=2.0,
                                linestyle='dashed'), zorder=5)
    # Text placed below the arc (arc dips to ~y=1.4 at its lowest point)
    ax.text(7.4, -0.55, 'Update θ until residual is minimized',
            ha='center', va='center', fontsize=10, color='#E74C3C',
            fontweight='bold', zorder=6)

    # Output box — top of figure
    arr(ax, 10.4, 4.6, 10.4, 5.4)
    box(ax, 9.2, 5.4, 2.4, 1.5,
        ['Output', 'θ* = [inertia,', 'drag, thrust, ...]'],
        '#2C7BB6')

    ax.text(6.5, 7.0, 'Grey-Box System Identification Loop',
            ha='center', fontsize=13, fontweight='bold', color='#222')

    plt.tight_layout()
    path = os.path.join(OUT, "fig4_optimizer.png")
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved {path}")


# ─────────────────────────────────────────────────────────────
# FIGURE 5: Hours breakdown pie/bar
# ─────────────────────────────────────────────────────────────
def fig_hours():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#FAFAFA')

    phases = ['Log Parser\n(70h)', 'Dynamics Model\n(80h)',
              'Uncertainty\n(70h)', 'Sensor Params\n(40h)',
              'Validation + Docs\n(40h)', 'Buffer\n(50h)']
    hours = [70, 80, 70, 40, 40, 50]
    colors = ['#5BA55B', '#E8A838', '#9B59B6', '#E74C3C', '#2C7BB6', '#AAAAAA']

    # Pie — use pctdistance inside wedge, labeldistance outside
    wedges, texts, autotexts = ax1.pie(
        hours, labels=phases, colors=colors,
        autopct='%1.0f%%', startangle=140,
        pctdistance=0.72, labeldistance=1.18,
        textprops={'fontsize': 9},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color('white')
        at.set_fontweight('bold')
    ax1.set_title('Hours by Phase  (350h total)',
                  fontweight='bold', fontsize=12)

    # Stacked bar showing cumulative progress
    cumulative = np.cumsum([0] + hours)
    ax2.set_facecolor('#F5F5F5')
    bar_h = 0.55
    for i in range(len(phases)):
        ax2.barh(0, hours[i], left=cumulative[i],
                 color=colors[i], height=bar_h, edgecolor='white', linewidth=1.2)
        if hours[i] >= 40:
            ax2.text(cumulative[i] + hours[i] / 2, 0,
                     f'{hours[i]}h', ha='center', va='center',
                     fontsize=9.5, fontweight='bold', color='white')

    week_markers = [0, 70, 150, 220, 260, 300, 350]
    week_labels  = ['Start', 'Wk3', 'Wk6', 'Wk8', 'Wk10', 'Wk12', 'End']
    ax2.set_xticks(week_markers)
    ax2.set_xticklabels(week_labels, fontsize=10)
    ax2.set_yticks([])
    ax2.set_xlim(0, 370)
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_xlabel('Cumulative Hours', fontsize=11)
    ax2.set_title('Cumulative Work Distribution', fontweight='bold', fontsize=12)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(OUT, "fig5_hours.png")
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved {path}")


if __name__ == '__main__':
    print("Generating proposal figures...")
    fig_pipeline()
    fig_gantt()
    fig_sim_real_gap()
    fig_optimizer()
    fig_hours()
    print("All figures saved to docs/figures/")
