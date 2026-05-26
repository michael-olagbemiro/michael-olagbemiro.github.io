python3 << 'EOF'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(12, 9))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)
ax.axis('off')

# ── Colour scheme ────────────────────────────────────────────────────────────
COL_SPINE  = '#1e40af'   # dark blue
COL_LEAF   = '#0369a1'   # mid blue
COL_HOST   = '#0f766e'   # teal
COL_LINK   = '#475569'   # slate
COL_LABEL  = '#1e293b'   # near black
COL_IP     = '#64748b'   # muted grey
COL_AS     = '#ffffff'   # white (inside boxes)
COL_BG     = '#f8fafc'   # near white background

fig.patch.set_facecolor(COL_BG)
ax.set_facecolor(COL_BG)

def draw_node(ax, x, y, label, sublabel, color, width=2.2, height=0.7):
    box = mpatches.FancyBboxPatch(
        (x - width/2, y - height/2), width, height,
        boxstyle="round,pad=0.08",
        linewidth=1.5,
        edgecolor='white',
        facecolor=color,
        zorder=3
    )
    ax.add_patch(box)
    ax.text(x, y + 0.06, label, ha='center', va='center',
            fontsize=10, fontweight='bold', color='white', zorder=4)
    ax.text(x, y - 0.18, sublabel, ha='center', va='center',
            fontsize=7.5, color='#bfdbfe', zorder=4)

def draw_link(ax, x1, y1, x2, y2, label1='', label2='', color=COL_LINK):
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=1.5,
            zorder=1, solid_capstyle='round')
    if label1:
        mx = x1 + (x2-x1)*0.22
        my = y1 + (y2-y1)*0.22
        ax.text(mx, my, label1, fontsize=6.5, color=COL_IP,
                ha='center', va='center',
                bbox=dict(facecolor=COL_BG, edgecolor='none', pad=1),
                zorder=5)
    if label2:
        mx = x1 + (x2-x1)*0.78
        my = y1 + (y2-y1)*0.78
        ax.text(mx, my, label2, fontsize=6.5, color=COL_IP,
                ha='center', va='center',
                bbox=dict(facecolor=COL_BG, edgecolor='none', pad=1),
                zorder=5)

# ── Node positions ───────────────────────────────────────────────────────────
# Spines — top row
SP1 = (3.5, 8.2)
SP2 = (8.5, 8.2)

# Leaves — middle row
L1  = (3.5, 5.5)
L2  = (8.5, 5.5)

# Hosts — bottom row
# leaf1 hosts: host1, host3, host4, host5
H1  = (1.2, 2.8)
H3  = (2.8, 2.8)
H4  = (4.2, 2.8)
H5  = (5.6, 2.8)
# leaf2 host: host2
H2  = (8.5, 2.8)

# ── Draw links ───────────────────────────────────────────────────────────────
# Spine1 <-> Leaf1
draw_link(ax, *SP1, *L1,
          '10.1.0.1/30', '10.1.0.2/30')
# Spine1 <-> Leaf2
draw_link(ax, *SP1, *L2,
          '10.1.1.1/30', '10.1.1.2/30')
# Spine2 <-> Leaf1
draw_link(ax, *SP2, *L1,
          '10.1.2.1/30', '10.1.2.2/30')
# Spine2 <-> Leaf2
draw_link(ax, *SP2, *L2,
          '10.1.3.1/30', '10.1.3.2/30')

# Leaf1 <-> hosts
draw_link(ax, *L1, *H1,
          '10.0.1.1/24', '10.0.1.10/24')
draw_link(ax, *L1, *H3,
          '10.0.4.1/30', '10.0.4.2/30')
draw_link(ax, *L1, *H4,
          '10.0.5.1/30', '10.0.5.2/30')
draw_link(ax, *L1, *H5,
          '10.0.6.1/30', '10.0.6.2/30')

# Leaf2 <-> host2
draw_link(ax, *L2, *H2,
          '10.0.2.1/24', '10.0.2.10/24')

# ── Draw nodes ───────────────────────────────────────────────────────────────
draw_node(ax, *SP1, 'spine1', 'AS 65000  |  lo 10.255.0.1/32', COL_SPINE)
draw_node(ax, *SP2, 'spine2', 'AS 65000  |  lo 10.255.0.2/32', COL_SPINE)
draw_node(ax, *L1,  'leaf1',  'AS 65001  |  lo 10.255.0.11/32', COL_LEAF)
draw_node(ax, *L2,  'leaf2',  'AS 65002  |  lo 10.255.0.12/32', COL_LEAF)
draw_node(ax, *H1,  'host1',  '10.0.1.10/24', COL_HOST, width=1.8)
draw_node(ax, *H3,  'host3',  '10.0.4.2/30',  COL_HOST, width=1.8)
draw_node(ax, *H4,  'host4',  '10.0.5.2/30',  COL_HOST, width=1.8)
draw_node(ax, *H5,  'host5',  '10.0.6.2/30',  COL_HOST, width=1.8)
draw_node(ax, *H2,  'host2',  '10.0.2.10/24', COL_HOST, width=1.8)

# ── Tier labels (left margin) ────────────────────────────────────────────────
for y, label in [(8.2, 'Spine tier'), (5.5, 'Leaf tier'), (2.8, 'Host tier')]:
    ax.text(0.15, y, label, fontsize=8, color='#94a3b8',
            ha='left', va='center', style='italic')

# ── Annotations ──────────────────────────────────────────────────────────────
# Senders bracket
ax.annotate('', xy=(5.9, 2.2), xytext=(0.9, 2.2),
            arrowprops=dict(arrowstyle='<->', color='#f59e0b', lw=1.5))
ax.text(3.4, 1.85, '4 senders (incast sweep)',
        fontsize=8, color='#f59e0b', ha='center', fontweight='bold')

# Receiver annotation
ax.text(8.5, 2.15, 'receiver',
        fontsize=8, color='#f59e0b', ha='center', fontweight='bold')

# eBGP session annotations
ax.text(6.0, 7.1, 'eBGP sessions', fontsize=8,
        color='#94a3b8', ha='center', style='italic')

# Congestion point arrow
ax.annotate('congestion\npoint', xy=(3.5, 6.2), xytext=(1.2, 7.0),
            fontsize=8, color='#ef4444', ha='center',
            arrowprops=dict(arrowstyle='->', color='#ef4444', lw=1.2))

# ── Legend ───────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=COL_SPINE, label='Spine  (AS 65000, SR Linux)'),
    mpatches.Patch(facecolor=COL_LEAF,  label='Leaf   (AS 65001/65002, SR Linux)'),
    mpatches.Patch(facecolor=COL_HOST,  label='Host   (network-multitool)'),
]
ax.legend(handles=legend_items, loc='lower right',
          fontsize=8, framealpha=0.9, edgecolor='#e2e8f0')

# ── Title ────────────────────────────────────────────────────────────────────
ax.set_title('BGP Leaf-Spine Topology — containerlab / SR Linux',
             fontsize=11, color=COL_LABEL, pad=12, fontweight='bold')

plt.tight_layout()

import os
os.makedirs('/home/michaelolagbemiro123/roce-lab/figures', exist_ok=True)
plt.savefig('/home/michaelolagbemiro123/roce-lab/figures/topology.pdf',
            bbox_inches='tight', facecolor=COL_BG)
plt.savefig('/home/michaelolagbemiro123/roce-lab/figures/topology.png',
            bbox_inches='tight', facecolor=COL_BG, dpi=150)
print("Saved topology.pdf and topology.png")
