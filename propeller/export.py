"""
DXF export for BEM-designed ducted propeller blade geometry.

Writes a DXF drawing containing:
  - PLANFORM layer   : 2D top-view outline of the blade (leading/trailing
                        edge lines built from chord length at each station),
                        optionally repeated/rotated for every blade.
  - STATIONS_3D layer: one twisted chord-line per radial station, positioned
                        along the spanwise (Z) axis at its blade angle. This
                        is the standard "rib" representation used to loft a
                        3D blade surface in CAD (SolidWorks/Fusion/etc.).
  - HUB_TIP layer     : reference circles at hub and tip radius.
  - STATION_PTS layer : POINT + TEXT entities labelling each station with
                        radius / chord / blade angle, for quick QA.

Requires: pip install ezdxf

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

import math

import ezdxf
from ezdxf.enums import TextEntityAlignment

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from propeller.bem import BladeGeometry


def _station_edge_points(radial_m: float, chord_m: float, blade_angle_deg: float):
    """
    Leading-edge / trailing-edge endpoints of the chord line at one station,
    in the LOCAL (tangential, axial) plane, centred on the pitch axis.

    tangential-axis -> local X, axial(flow)-axis -> local Y
    """
    beta = math.radians(blade_angle_deg)
    half_c = chord_m / 2.0
    dx = half_c * math.cos(beta)
    dy = half_c * math.sin(beta)
    leading = (dx, dy)
    trailing = (-dx, -dy)
    return leading, trailing


def _rotate_xy(point, angle_rad):
    x, y = point
    ca, sa = math.cos(angle_rad), math.sin(angle_rad)
    return (x * ca - y * sa, x * sa + y * ca)


def export_blade_to_pdf(
    geometry: BladeGeometry,
    filepath: str,
    include_all_blades: bool = True,
    include_stations_3d: bool = True,
    include_labels: bool = True,
    units_scale: float = 1.0,
    dpi: int = 300,
) -> str:
    """
    Export the blade geometry as a PDF drawing using a 2D projected planform.

    This keeps the PDF export simple and consistent with the DXF planform
    view, while optionally adding the station rib lines and labels.
    """

    s = units_scale
    stations = geometry.stations
    num_blades = max(1, geometry.num_blades)
    blade_angle_step = 2.0 * math.pi / num_blades

    leading_pts = []
    trailing_pts = []
    for st in stations:
        le, te = _station_edge_points(
            st.radial_position_m, st.chord_m, st.blade_angle_deg
        )
        leading_pts.append((le[0] * s, st.radial_position_m * s))
        trailing_pts.append((te[0] * s, st.radial_position_m * s))

    outline = leading_pts + trailing_pts[::-1] + [leading_pts[0]]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect("equal")

    n_copies = num_blades if include_all_blades else 1
    for k in range(n_copies):
        theta = k * blade_angle_step
        rotated = [_rotate_xy(pt, theta) for pt in outline]
        x = [pt[0] for pt in rotated]
        y = [pt[1] for pt in rotated]
        ax.plot(x, y, color="tab:blue", linewidth=2.0)

    ax.add_patch(
        Circle(
            (0, 0),
            geometry.hub_radius_m * s,
            fill=False,
            edgecolor="gray",
            linestyle="--",
            linewidth=1,
        )
    )
    ax.add_patch(
        Circle(
            (0, 0),
            geometry.tip_radius_m * s,
            fill=False,
            edgecolor="gray",
            linestyle="--",
            linewidth=1,
        )
    )

    if include_stations_3d:
        for st in stations:
            le, te = _station_edge_points(
                st.radial_position_m, st.chord_m, st.blade_angle_deg
            )
            p_le = (le[0] * s, le[1] * s)
            p_te = (te[0] * s, te[1] * s)
            for k in range(n_copies):
                theta = k * blade_angle_step
                p_le_r = _rotate_xy(p_le, theta)
                p_te_r = _rotate_xy(p_te, theta)
                ax.plot(
                    [p_le_r[0], p_te_r[0]],
                    [p_le_r[1], p_te_r[1]],
                    color="tab:green",
                    linewidth=0.8,
                    alpha=0.75,
                )

    if include_labels:
        for st, (lx, ly) in zip(stations, leading_pts):
            label = (
                f"r={st.radial_position_m:.3f}m  "
                f"c={st.chord_m * 1000:.1f}mm  "
                f"beta={st.blade_angle_deg:.1f}deg"
            )
            for k in range(n_copies):
                theta = k * blade_angle_step
                lx_r, ly_r = _rotate_xy((lx, ly), theta)
                ax.plot(lx_r, ly_r, "o", color="tab:red", markersize=3)
                ax.text(
                    lx_r + 0.01 * s,
                    ly_r + 0.01 * s,
                    label,
                    fontsize=7,
                    color="black",
                    clip_on=False,
                )

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title(
        "MPSE Ducted Propeller - Blade Planform",
        fontsize=12,
    )
    ax.grid(True, alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(filepath, format="pdf", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return filepath


def export_blade_to_dxf(
    geometry: BladeGeometry,
    filepath: str,
    dxfversion: str = "R2010",
    include_all_blades: bool = True,
    include_stations_3d: bool = True,
    include_labels: bool = True,
    units_scale: float = 1.0,
) -> str:
    """
    Export a BladeGeometry to a DXF file.

    Args:
        geometry: result of BEMDesigner.design()
        filepath: output .dxf path
        dxfversion: ezdxf DXF version string (e.g. "R2010", "R2013")
        include_all_blades: if True, draw the planform for every blade
            (rotated by 360/B about the hub axis) instead of just one.
        include_stations_3d: if True, add the twisted per-station chord
            lines along the spanwise (Z) axis for lofting.
        include_labels: if True, annotate each station with radius, chord
            and blade angle as TEXT entities.
        units_scale: multiply all coordinates by this factor (e.g. 1000.0
            to write the drawing in millimetres instead of metres).

    Returns:
        The filepath written.
    """
    doc = ezdxf.new(dxfversion=dxfversion, setup=True)
    doc.units = ezdxf.units.M
    msp = doc.modelspace()

    for name, color in (
        ("PLANFORM", 5),      # blue
        ("STATIONS_3D", 3),   # green
        ("HUB_TIP", 8),       # grey
        ("STATION_PTS", 1),   # red
    ):
        if name not in doc.layers:
            doc.layers.add(name=name, color=color)

    s = units_scale
    stations = geometry.stations
    num_blades = max(1, geometry.num_blades)
    blade_angle_step = 2.0 * math.pi / num_blades

    # planform outline(s)
    leading_pts = []
    trailing_pts = []
    for st in stations:
        le, te = _station_edge_points(
            st.radial_position_m, st.chord_m, st.blade_angle_deg
        )
        # Planform view: local X = tangential -> world X, radial -> world Y
        leading_pts.append((le[0] * s, st.radial_position_m * s))
        trailing_pts.append((te[0] * s, st.radial_position_m * s))

    outline = leading_pts + trailing_pts[::-1] + [leading_pts[0]]

    n_copies = num_blades if include_all_blades else 1
    for k in range(n_copies):
        theta = k * blade_angle_step
        rotated = [_rotate_xy(pt, theta) for pt in outline]
        msp.add_lwpolyline(
            rotated, format="xy", dxfattribs={"layer": "PLANFORM"}
        )

    # hub / tip reference circles
    msp.add_circle(
        center=(0, 0), radius=geometry.hub_radius_m * s,
        dxfattribs={"layer": "HUB_TIP"},
    )
    msp.add_circle(
        center=(0, 0), radius=geometry.tip_radius_m * s,
        dxfattribs={"layer": "HUB_TIP"},
    )

    # 3D twisted station chord lines (for lofting) 
    if include_stations_3d:
        for st in stations:
            le, te = _station_edge_points(
                st.radial_position_m, st.chord_m, st.blade_angle_deg
            )
            z = st.radial_position_m * s
            p_le = (le[0] * s, le[1] * s, z)
            p_te = (te[0] * s, te[1] * s, z)
            msp.add_line(p_le, p_te, dxfattribs={"layer": "STATIONS_3D"})

    # station labels 
    if include_labels:
        for st, (lx, ly) in zip(stations, leading_pts):
            label = (
                f"r={st.radial_position_m:.3f}m  "
                f"c={st.chord_m * 1000:.1f}mm  "
                f"beta={st.blade_angle_deg:.1f}deg"
            )
            msp.add_point((lx, ly), dxfattribs={"layer": "STATION_PTS"})
            text = msp.add_text(
                label,
                height=max(geometry.tip_radius_m * s * 0.02, 1e-3),
                dxfattribs={"layer": "STATION_PTS"},
            )
            text.set_placement(
                (lx, ly), align=TextEntityAlignment.LEFT
            )

    doc.saveas(filepath)
    return filepath


if __name__ == "__main__":
    from propeller.bem import BEMDesigner, PropellerSpec

    spec = PropellerSpec(
        required_power_w=12000,
        rated_speed_rpm=2260,
        tip_radius_m=0.5,
        hub_radius_m=0.13,
        freestream_velocity_ms=40.0,
        air_density_kgm3=1.23,
        num_blades=5,
        design_cl=0.7,
    )
    geometry = BEMDesigner(spec).design()
    geometry.print_geometry_table()
    print("Exporting blade geometry to DXF: plots/mpse_propeller_blade.dxf")
    export_blade_to_dxf(geometry, "plots/mpse_propeller_blade.dxf")
    print("Exporting blade geometry to PDF: plots/mpse_propeller_blade.pdf")
    export_blade_to_pdf(geometry, "plots/mpse_propeller_blade.pdf")