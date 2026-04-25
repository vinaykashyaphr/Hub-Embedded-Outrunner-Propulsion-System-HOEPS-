"""
Propeller blade geometry visualization.

Generates plots of the BEM-designed blade:
- Twist distribution (blade angle vs radial position)
- Chord distribution (chord length vs radial position)
- Blade planform (top-view outline)

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

# import matplotlib
# matplotlib.use('Agg')

import numpy as np
from propeller.bem import BladeGeometry


def plot_twist_distribution(geometry: BladeGeometry, save_path: str = None):
    """
    Plot blade angle (twist) vs radial position.
    Shows characteristic decreasing twist from hub to tip.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return

    r = [s.radial_position_m for s in geometry.stations]
    angles = [s.blade_angle_deg for s in geometry.stations]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(r, angles, 'o-', color='#1F4E79', linewidth=2,
            markersize=8, markerfacecolor='white', markeredgewidth=2)

    for ri, ai in zip(r, angles):
        ax.annotate(f'{ai:.1f}°',
                    xy=(ri, ai), xytext=(8, 4),
                    textcoords='offset points',
                    fontsize=9, color='#595959')

    ax.set_xlabel('Radial Position (m)', fontsize=12)
    ax.set_ylabel('Blade Angle (deg)', fontsize=12)
    ax.set_title('MPSE Ducted Propeller — Blade Twist Distribution', fontsize=13)
    ax.axvline(geometry.hub_radius_m, color='#AAAAAA', linestyle='--',
               linewidth=1, label=f'Hub radius ({geometry.hub_radius_m} m)')
    ax.axvline(geometry.tip_radius_m, color='#AAAAAA', linestyle=':',
               linewidth=1, label=f'Tip radius ({geometry.tip_radius_m} m)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_chord_distribution(geometry: BladeGeometry, save_path: str = None):
    """
    Plot chord length vs radial position.
    Shows decreasing chord from hub to tip.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return

    r = [s.radial_position_m for s in geometry.stations]
    chords = [s.chord_m * 1000 for s in geometry.stations]  # convert to mm

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(r, chords, 's-', color='#2E75B6', linewidth=2,
            markersize=8, markerfacecolor='white', markeredgewidth=2)

    for ri, ci in zip(r, chords):
        ax.annotate(f'{ci:.1f} mm',
                    xy=(ri, ci), xytext=(8, 4),
                    textcoords='offset points',
                    fontsize=9, color='#595959')

    ax.set_xlabel('Radial Position (m)', fontsize=12)
    ax.set_ylabel('Chord Length (mm)', fontsize=12)
    ax.set_title('MPSE Ducted Propeller — Chord Distribution', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.axvline(geometry.hub_radius_m, color='#AAAAAA', linestyle='--',
               linewidth=1, label='Hub radius')
    ax.axvline(geometry.tip_radius_m, color='#AAAAAA', linestyle=':',
               linewidth=1, label='Tip radius')
    ax.legend(fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_blade_planform(geometry: BladeGeometry, save_path: str = None):
    """
    2D top-view planform of one blade.
    Shows the tapered shape from hub chord to tip chord.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return

    r = np.array([s.radial_position_m for s in geometry.stations])
    c = np.array([s.chord_m for s in geometry.stations])

    # Leading and trailing edge lines (symmetric about chord centre)
    leading_edge = c / 2.0
    trailing_edge = -c / 2.0

    fig, ax = plt.subplots(figsize=(10, 4))

    # Fill blade shape
    r_full = np.concatenate([r, r[::-1]])
    c_full = np.concatenate([leading_edge, trailing_edge[::-1]])
    ax.fill(r_full, c_full * 1000, color='#2E75B6', alpha=0.3)
    ax.plot(r, leading_edge * 1000, '-', color='#1F4E79', linewidth=2,
            label='Leading edge')
    ax.plot(r, trailing_edge * 1000, '-', color='#1F4E79', linewidth=2,
            label='Trailing edge')

    # Station markers
    for ri, lei, tei in zip(r, leading_edge * 1000, trailing_edge * 1000):
        ax.plot([ri, ri], [tei, lei], '--', color='#AAAAAA',
                linewidth=0.8, alpha=0.6)

    ax.set_xlabel('Radial Position (m)', fontsize=12)
    ax.set_ylabel('Chord (mm, symmetric)', fontsize=12)
    ax.set_title(f'MPSE Ducted Propeller — Blade Planform  '
                 f'(D={geometry.tip_diameter_m():.2f} m, '
                 f'{geometry.num_blades} blades)', fontsize=13)
    ax.axhline(0, color='#AAAAAA', linewidth=0.5)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    else:
        plt.show()
    plt.close()


def plot_all(geometry: BladeGeometry, output_dir: str = "."):
    """Generate all blade geometry plots and save to output_dir."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    plot_twist_distribution(geometry,
        save_path=os.path.join(output_dir, "blade_twist.png"))
    plot_chord_distribution(geometry,
        save_path=os.path.join(output_dir, "blade_chord.png"))
    plot_blade_planform(geometry,
        save_path=os.path.join(output_dir, "blade_planform.png"))
    print(f"All plots saved to {output_dir}/")
