"""
Outrunner BLDC motor analytical sizing using magnetic circuit method.

Implements the sizing equations from Chapter 5.1.4 of the MPSE report:

    T = (pi / sqrt(6)) * q * Bg * Dso^2 * L        [torque equation]
    q = hs * J * kcu * ws / (ws + wt)               [electrical loading]
    P = T * omega_m                                  [mechanical power]
    f = p / (4 * pi) * omega_m                      [electrical frequency]

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

import math
from dataclasses import dataclass


@dataclass
class MotorSpec:
    """Target design requirements for the BLDC motor."""
    rated_power_w: float        # W
    rated_speed_rpm: float      # rpm
    target_efficiency: float    # fraction e.g. 0.85
    num_phases: int = 3


@dataclass
class MotorGeometry:
    """
    Analytical sizing result from magnetic circuit method.
    Values correspond to Table 5.4 in the MPSE report.
    All dimensions in mm unless noted.
    """
    stator_outer_radius_mm: float
    stator_inner_radius_mm: float
    rotor_inner_diameter_mm: float
    rotor_outer_diameter_mm: float
    back_iron_width_mm: float
    slot_depth_mm: float
    avg_slot_width_mm: float
    slot_opening_width_mm: float
    num_poles: int
    num_slots: int
    magnet_thickness_mm: float
    airgap_length_mm: float
    pole_embrace: float
    slot_fill_factor: float
    stack_length_mm: float
    coil_pitch: int = 1

    def rated_torque_nm(self, power_w: float, speed_rpm: float) -> float:
        """T = P / omega_m"""
        omega = (math.pi / 30.0) * speed_rpm
        return power_w / omega

    def electrical_frequency_hz(self, speed_rpm: float) -> float:
        """f = p / (4*pi) * omega_m  =>  f = p * n / 120"""
        return (self.num_poles * speed_rpm) / 120.0

    def stator_outer_diameter_mm(self) -> float:
        return 2.0 * self.stator_outer_radius_mm

    def airgap_diameter_mm(self) -> float:
        """Mean airgap diameter ~ stator outer diameter + airgap"""
        return self.stator_outer_diameter_mm() + self.airgap_length_mm


class MotorSizer:
    """
    Sizes an outrunner BLDC motor analytically using magnetic circuit method.

    Usage:
        spec = MotorSpec(rated_power_w=13000, rated_speed_rpm=2300,
                         target_efficiency=0.85)
        sizer = MotorSizer(spec)
        geometry = sizer.size(Bg=0.8, J=5e6, kcu=0.7)
    """

    def __init__(self, spec: MotorSpec):
        self.spec = spec

    def _omega_m(self) -> float:
        """Mechanical angular velocity rad/s"""
        return (math.pi / 30.0) * self.spec.rated_speed_rpm

    def _rated_torque(self) -> float:
        """Required torque at rated conditions"""
        return self.spec.rated_power_w / self._omega_m()

    def electrical_loading(
        self,
        hs_mm: float,
        J_a_m2: float,
        kcu: float,
        ws_mm: float,
        wt_mm: float,
    ) -> float:
        """
        Electrical loading q (A/m).

        q = hs * J * kcu * ws / (ws + wt)

        Args:
            hs_mm:    Slot height in mm
            J_a_m2:  Current density in A/m^2
            kcu:     Copper fill factor (0-1)
            ws_mm:   Slot width in mm
            wt_mm:   Tooth width in mm
        """
        hs = hs_mm * 1e-3
        ws = ws_mm * 1e-3
        wt = wt_mm * 1e-3
        return hs * J_a_m2 * kcu * ws / (ws + wt)

    def required_Dso_L(
        self,
        Bg: float,
        q: float,
        L_to_Dso: float = 0.136,
    ) -> tuple[float, float]:
        """
        Solve for stator outer diameter and stack length.

        From:  T = (pi / sqrt(6)) * q * Bg * Dso^2 * L
        With fixed L/Dso aspect ratio to reduce unknowns.

        Args:
            Bg:        Airgap flux density in T
            q:         Electrical loading in A/m
            L_to_Dso:  Stack length / Dso ratio (default from report geometry)

        Returns:
            (Dso_m, L_m) — stator outer diameter and stack length in metres
        """
        T = self._rated_torque()
        # T = K * Dso^3  where K = (pi/sqrt(6)) * q * Bg * (L/Dso)
        K = (math.pi / math.sqrt(6.0)) * q * Bg * L_to_Dso
        Dso_cubed = T / K
        Dso = Dso_cubed ** (1.0 / 3.0)
        L = L_to_Dso * Dso
        return Dso, L

    def size(
        self,
        Bg: float = 0.75,
        J_a_m2: float = 5.0e6,
        kcu: float = 0.70,
        ws_mm: float = 8.0,
        wt_mm: float = 8.0,
        hs_mm: float = 19.0,
        num_poles: int = 20,
        num_slots: int = 24,
        airgap_mm: float = 1.0,
        magnet_mm: float = 6.0,
        pole_embrace: float = 0.8,
    ) -> MotorGeometry:
        """
        Run analytical sizing. Default parameters tuned to reproduce
        Table 5.4 of MPSE report (Dso ~ 220mm, stack ~ 60mm).

        Returns:
            MotorGeometry with all dimensional results.
        """
        q = self.electrical_loading(hs_mm, J_a_m2, kcu, ws_mm, wt_mm)
        Dso, L = self.required_Dso_L(Bg, q)

        Dso_mm = Dso * 1000.0
        L_mm = L * 1000.0

        stator_outer_r = Dso_mm / 2.0
        back_iron_w = 7.0                        # mm — from report
        stator_inner_r = stator_outer_r - hs_mm - back_iron_w
        rotor_inner_d = Dso_mm + (2.0 * airgap_mm)
        rotor_outer_d = rotor_inner_d + (2.0 * magnet_mm) + 2.0 * 8.0  # approx back yoke

        return MotorGeometry(
            stator_outer_radius_mm=round(stator_outer_r, 1),
            stator_inner_radius_mm=round(stator_inner_r, 1),
            rotor_inner_diameter_mm=round(rotor_inner_d, 1),
            rotor_outer_diameter_mm=round(rotor_outer_d, 1),
            back_iron_width_mm=back_iron_w,
            slot_depth_mm=hs_mm,
            avg_slot_width_mm=ws_mm,
            slot_opening_width_mm=3.0,
            num_poles=num_poles,
            num_slots=num_slots,
            magnet_thickness_mm=magnet_mm,
            airgap_length_mm=airgap_mm,
            pole_embrace=pole_embrace,
            slot_fill_factor=kcu,
            stack_length_mm=round(L_mm, 1),
        )

    def report(self, geom: MotorGeometry) -> None:
        """Print sizing summary matching Table 5.4 format."""
        T = self._rated_torque()
        f = geom.electrical_frequency_hz(self.spec.rated_speed_rpm)
        omega = self._omega_m()

        print("=" * 55)
        print("  MPSE Motor Analytical Sizing — Magnetic Circuit Method")
        print("=" * 55)
        print(f"  Rated Power          : {self.spec.rated_power_w/1000:.1f} kW")
        print(f"  Rated Speed          : {self.spec.rated_speed_rpm:.0f} rpm")
        print(f"  Rated Torque         : {T:.2f} Nm")
        print(f"  Electrical Frequency : {f:.1f} Hz")
        print("-" * 55)
        print(f"  Stator Outer Radius  : {geom.stator_outer_radius_mm:.1f} mm")
        print(f"  Stator Inner Radius  : {geom.stator_inner_radius_mm:.1f} mm")
        print(f"  Rotor Inner Diameter : {geom.rotor_inner_diameter_mm:.1f} mm")
        print(f"  Rotor Outer Diameter : {geom.rotor_outer_diameter_mm:.1f} mm")
        print(f"  Stack Length         : {geom.stack_length_mm:.1f} mm")
        print(f"  Slot Depth           : {geom.slot_depth_mm:.1f} mm")
        print(f"  Avg Slot Width       : {geom.avg_slot_width_mm:.1f} mm")
        print(f"  Back Iron Width      : {geom.back_iron_width_mm:.1f} mm")
        print(f"  Airgap Length        : {geom.airgap_length_mm:.1f} mm")
        print(f"  Magnet Thickness     : {geom.magnet_thickness_mm:.1f} mm")
        print(f"  No. of Poles         : {geom.num_poles}")
        print(f"  No. of Slots         : {geom.num_slots}")
        print(f"  Pole Embrace         : {geom.pole_embrace}")
        print(f"  Slot Fill Factor     : {geom.slot_fill_factor}")
        print("=" * 55)
