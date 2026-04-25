"""
Ducted axial propeller design using Blade Element Momentum (BEM) theory.

Implements the analytical design procedure from Chapter 6.1 of the MPSE report,
following the vortex-corrected BEM method of Adkins (1994) extended to ducted
configurations per Page (1996).

Physical equations:
    Stage work:   Wst = u * Cy3
    Mass flow:    mdot = rho * A * V
    Power:        P = mdot * u * Cy3
    Blade angle:  phi = arctan(V / (u * (1 - a))) + pitch_offset
    Chord:        c = (4 * pi * K) / (Cl * B * W)

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from scipy.integrate import quad
from typing import Optional



@dataclass
class PropellerSpec:
    """Input specification for propeller design."""
    required_power_w: float        # W  — from motor rated output
    rated_speed_rpm: float         # rpm
    tip_radius_m: float            # m  — R
    hub_radius_m: float            # m  — Rh
    freestream_velocity_ms: float  # m/s — V
    air_density_kgm3: float        # kg/m^3 — rho
    num_blades: int                # B
    design_cl: float               # Cl — design lift coefficient
    num_stations: int = 5          # radial stations from hub to tip
    pitch_offset_deg: float = 3.0  # geometric pitch correction



@dataclass
class BladeStation:
    """Aerodynamic properties at one radial station."""
    radial_position_m: float
    blade_angle_deg: float
    chord_m: float
    inflow_angle_deg: float
    tangential_velocity_ms: float
    axial_inflow_factor: float



@dataclass
class BladeGeometry:
    """Complete propeller blade geometry result."""
    stations: list[BladeStation]
    tip_radius_m: float
    hub_radius_m: float
    num_blades: int
    design_efficiency: Optional[float] = None

    def tip_diameter_m(self) -> float:
        return 2.0 * self.tip_radius_m

    def hub_diameter_m(self) -> float:
        return 2.0 * self.hub_radius_m

    def print_geometry_table(self) -> None:
        """Print blade geometry matching Table 6.1 format."""
        print("=" * 60)
        print("  Ducted Propeller Blade Geometry — BEM Design")
        print("=" * 60)
        print(f"  {'Radial (m)':<14} {'Blade Angle (deg)':<20} {'Chord (m)':<14}")
        print("-" * 60)
        for s in self.stations:
            print(f"  {s.radial_position_m:<14.4f} {s.blade_angle_deg:<20.2f} {s.chord_m:<14.5f}")
        print("=" * 60)
        print(f"  Tip Diameter    : {self.tip_diameter_m():.3f} m")
        print(f"  Hub Diameter    : {self.hub_diameter_m():.3f} m")
        print(f"  Number of Blades: {self.num_blades}")
        if self.design_efficiency is not None:
            print(f"  Design Efficiency: {self.design_efficiency*100:.1f}%")
        print("=" * 60)



class BEMDesigner:
    """
    Designs a ducted axial propeller blade using BEM theory.

    Usage:
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
        designer = BEMDesigner(spec)
        geometry = designer.design()
        geometry.print_geometry_table()
    """

    def __init__(self, spec: PropellerSpec):
        self.spec = spec
        self._omega = (math.pi / 30.0) * spec.rated_speed_rpm

    def _radial_stations(self) -> np.ndarray:
        """Generate radial stations from hub to tip."""
        return np.linspace(
            self.spec.hub_radius_m,
            self.spec.tip_radius_m,
            self.spec.num_stations,
        )

    def _duct_area(self) -> float:
        """Annular duct area A = pi * (R^2 - Rh^2)"""
        return math.pi * (
            self.spec.tip_radius_m**2 - self.spec.hub_radius_m**2
        )

    def _mass_flow(self) -> float:
        """mdot = rho * A * V"""
        return (
            self.spec.air_density_kgm3
            * self._duct_area()
            * self.spec.freestream_velocity_ms
        )

    def _blade_angular_velocity(self, r: np.ndarray) -> np.ndarray:
        """u = omega * r"""
        return self._omega * r

    def _tangential_velocity(self, u: np.ndarray, mdot: float) -> np.ndarray:
        """
        vt = P / (mdot * u)
        From Euler work equation: Wst = u * Cy3, P = mdot * u * vt
        """
        return self.spec.required_power_w / (mdot * u)

    def _axial_inflow_factor(self, vt: np.ndarray, u: np.ndarray) -> np.ndarray:
        """a = vt / (2 * u)"""
        return vt / (2.0 * u)

    def _inflow_angle_rad(self, u: np.ndarray, a: np.ndarray) -> np.ndarray:
        """phi = arctan(V / (u * (1 - a)))"""
        return np.arctan(
            self.spec.freestream_velocity_ms / (u * (1.0 - a))
        )

    def _blade_angle_deg(self, phi_rad: np.ndarray) -> np.ndarray:
        """blade angle = phi_degrees + pitch_offset"""
        return np.degrees(phi_rad) + self.spec.pitch_offset_deg

    def _circulation(self, r: np.ndarray, vt: np.ndarray) -> np.ndarray:
        """K = r * vt  (bound vortex circulation)"""
        return r * vt

    def _chord(
        self,
        K: np.ndarray,
        u: np.ndarray,
        a: np.ndarray,
        phi_rad: np.ndarray,
    ) -> np.ndarray:
        """
        c = (4 * pi * K) / (Cl * B * W)
        where W = sqrt(u^2 + V^2) is the resultant velocity
        """
        V = self.spec.freestream_velocity_ms
        W = np.sqrt(u**2 + V**2)
        return (4.0 * math.pi * K) / (
            self.spec.design_cl * self.spec.num_blades * W
        )

    def _compute_efficiency(
        self, r: np.ndarray, K: np.ndarray, a: np.ndarray
    ) -> float:
        """
        Compute propulsive efficiency via constraint integrals.
        eta = T*V / P
        """
        Rh = self.spec.hub_radius_m
        R = self.spec.tip_radius_m
        V = self.spec.freestream_velocity_ms
        a0 = float(a[0])

        ndr0 = Rh / R

        def J_integrand(ndr):
            return 4.0 * self._omega * ndr / (V**2)

        def I1_integrand(ndr):
            return 4.0 * self._omega * ndr * (1.0 + a0) / (V**2)

        def I2_integrand(ndr):
            return 4.0 * ndr * self._omega * a0 / (V**2)

        J1, _ = quad(J_integrand, ndr0, 1.0)
        I1, _ = quad(I1_integrand, ndr0, 1.0)
        I2, _ = quad(I2_integrand, ndr0, 1.0)

        # Use mean K across stations
        K_mean = float(np.mean(K))
        rho = self.spec.air_density_kgm3

        Pc = K_mean * J1
        Tc = (K_mean * I1) - (K_mean**2 * I2)

        q = 0.5 * rho * V**2 * math.pi * R**2
        T = Tc * q
        P = Pc * rho * V**3 * math.pi * R**2 / 2.0

        if P > 0:
            return float(np.mean(T * V / P))
        return 0.0

    def design(self) -> BladeGeometry:
        """
        Run the full BEM design procedure.

        Returns:
            BladeGeometry with all radial stations computed.
        """
        r = self._radial_stations()
        mdot = self._mass_flow()
        u = self._blade_angular_velocity(r)
        vt = self._tangential_velocity(u, mdot)
        a = self._axial_inflow_factor(vt, u)
        phi_rad = self._inflow_angle_rad(u, a)
        blade_angle = self._blade_angle_deg(phi_rad)
        K = self._circulation(r, vt)
        c = self._chord(K, u, a, phi_rad)
        eta = self._compute_efficiency(r, K, a)

        stations = [
            BladeStation(
                radial_position_m=float(r[i]),
                blade_angle_deg=float(blade_angle[i]),
                chord_m=float(c[i]),
                inflow_angle_deg=float(np.degrees(phi_rad[i])),
                tangential_velocity_ms=float(vt[i]),
                axial_inflow_factor=float(a[i]),
            )
            for i in range(len(r))
        ]

        return BladeGeometry(
            stations=stations,
            tip_radius_m=self.spec.tip_radius_m,
            hub_radius_m=self.spec.hub_radius_m,
            num_blades=self.spec.num_blades,
            design_efficiency=eta,
        )
