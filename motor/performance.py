"""
Analytical performance estimation for the MPSE outrunner BLDC motor.

Estimates copper loss, core loss, and efficiency from motor geometry
and material properties — providing analytical verification alongside
the FEM results from Ansys Maxwell (Table 5.4 of MPSE report).

FEM reference results (Ansys Maxwell RMxprt, Table 5.4):
    Output Power    : 12.44 kW
    Input Power     : 13.86 kW
    Efficiency      : 89.78%
    Rated Speed     : 2277.65 rpm
    Rated Torque    : 52.17 Nm
    Avg Input Current: 34.65 A
    Total Losses    : 1415.9 W

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

import math
from dataclasses import dataclass
from motor.materials import CoreMaterial, PermanentMagnet, JNEX900
from motor.sizing import MotorGeometry


@dataclass
class MotorPerformance:
    """Analytical performance estimate for the BLDC motor."""
    output_power_w: float
    copper_loss_w: float
    core_loss_w: float
    total_loss_w: float
    input_power_w: float
    efficiency: float
    rated_torque_nm: float
    rated_speed_rpm: float
    phase_current_a: float

    def print_performance(self) -> None:
        print("=" * 55)
        print("  MPSE Motor Performance — Analytical Estimate")
        print("=" * 55)
        print(f"  Output Power      : {self.output_power_w/1000:.2f} kW")
        print(f"  Input Power       : {self.input_power_w/1000:.2f} kW")
        print(f"  Efficiency        : {self.efficiency*100:.2f}%")
        print(f"  Rated Torque      : {self.rated_torque_nm:.2f} Nm")
        print(f"  Rated Speed       : {self.rated_speed_rpm:.1f} rpm")
        print(f"  Phase Current     : {self.phase_current_a:.2f} A")
        print("-" * 55)
        print(f"  Copper Loss       : {self.copper_loss_w:.1f} W")
        print(f"  Core Loss         : {self.core_loss_w:.1f} W")
        print(f"  Total Losses      : {self.total_loss_w:.1f} W")
        print("-" * 55)
        print("  FEM Reference (Ansys Maxwell):")
        print(f"    Efficiency      : 89.78%")
        print(f"    Rated Torque    : 52.17 Nm")
        print(f"    Total Losses    : 1415.9 W")
        print("=" * 55)


class MotorPerformanceEstimator:
    """
    Estimates motor performance analytically from geometry and materials.

    Uses simplified loss models:
    - Copper loss: P_cu = 3 * I^2 * R_phase
    - Core loss:   P_fe = core_loss_density * core_mass
    - Efficiency:  eta = P_out / (P_out + P_cu + P_fe)

    Usage:
        estimator = MotorPerformanceEstimator(
            geometry=geom,
            core_material=JNEX900,
            rated_power_w=13000,
            rated_speed_rpm=2300,
        )
        perf = estimator.estimate()
        perf.print_performance()
    """

    # Copper resistivity at 75 degC operating temperature
    COPPER_RESISTIVITY = 2.0e-8   # ohm.m (elevated from 1.68e-8 at 20C)
    # Iron density for core mass estimation
    IRON_DENSITY = 7650.0         # kg/m^3 (amorphous steel)
    # DC bus voltage — back-calculated from FEM reference:
    # V_dc = P_in / (3 * I_phase) * sqrt(3) = 13860 / (3 * 34.65) * sqrt(3) ~ 231V
    DC_BUS_VOLTAGE = 231.0        # V

    def __init__(
        self,
        geometry: MotorGeometry,
        core_material: CoreMaterial,
        rated_power_w: float,
        rated_speed_rpm: float,
        num_turns_per_coil: int = 8,
    ):
        self.geom = geometry
        self.core = core_material
        self.rated_power_w = rated_power_w
        self.rated_speed_rpm = rated_speed_rpm
        self.num_turns = num_turns_per_coil

    def _omega_m(self) -> float:
        return (math.pi / 30.0) * self.rated_speed_rpm

    def _rated_torque(self) -> float:
        return self.rated_power_w / self._omega_m()

    def _electrical_frequency(self) -> float:
        return self.geom.electrical_frequency_hz(self.rated_speed_rpm)

    def _phase_resistance(self) -> float:
        """
        Estimate winding resistance per phase.

        R = rho * L_conductor / A_conductor
        L_conductor ~ 2 * (stack_length + end_turn_length) * turns_per_phase
        A_conductor ~ slot_area * kcu / turns_per_slot
        """
        # Slot cross-section area (rectangular approximation)
        ws = self.geom.avg_slot_width_mm * 1e-3
        hs = self.geom.slot_depth_mm * 1e-3
        slot_area = ws * hs * self.geom.slot_fill_factor

        # Turns per slot (2 coil sides per slot for concentrated winding)
        turns_per_slot = self.num_turns * 2
        conductor_area = slot_area / turns_per_slot

        # Conductor length estimate
        stack_m = self.geom.stack_length_mm * 1e-3
        # End turn approximation: pi * (stator_inner_radius / num_poles)
        end_turn = math.pi * (self.geom.stator_inner_radius_mm * 1e-3) / self.geom.num_poles
        conductor_length = 2.0 * (stack_m + end_turn) * self.num_turns

        if conductor_area <= 0:
            return 0.1  # fallback

        return self.COPPER_RESISTIVITY * conductor_length / conductor_area

    def _phase_current(self, R_phase: float) -> float:
        """
        Estimate phase current from power and assumed DC bus voltage.
        For a 3-phase BLDC: P = sqrt(3) * V_line * I * pf
        Simplified: I = P / (3 * V_phase) with assumed V_phase.

        For 13kW at ~89% efficiency, FEM shows 34.65A.
        We estimate from input power and assumed phase voltage.
        """
        # Assume phase voltage ~ DC_BUS / sqrt(3) for star connection
        V_phase = self.DC_BUS_VOLTAGE / math.sqrt(3.0)
        # P_in estimate assuming target efficiency
        P_in_estimate = self.rated_power_w / self.spec.target_efficiency if hasattr(self, 'spec') else self.rated_power_w / 0.88
        # I = P_in / (3 * V_phase) for balanced 3-phase
        I = P_in_estimate / (3.0 * V_phase)
        return I

    def _copper_loss(self, I: float, R_phase: float) -> float:
        """P_cu = 3 * I^2 * R_phase"""
        return 3.0 * I**2 * R_phase

    def _core_mass(self) -> float:
        """
        Estimate stator core mass.
        Volume ~ annular ring of (outer_radius - inner_radius) * stack_length
        """
        r_outer = self.geom.stator_outer_radius_mm * 1e-3
        r_inner = self.geom.stator_inner_radius_mm * 1e-3
        L = self.geom.stack_length_mm * 1e-3
        # Stator ring volume minus slot volume (approx 40% slot fill)
        ring_volume = math.pi * (r_outer**2 - r_inner**2) * L * 0.6
        return ring_volume * self.IRON_DENSITY

    def _core_loss(self) -> float:
        """
        P_fe = core_loss_density(freq) * core_mass
        Uses interpolated loss density from material datasheet.
        """
        freq = self._electrical_frequency()
        loss_density = self.core.core_loss_at(freq)  # W/kg
        mass = self._core_mass()
        return loss_density * mass

    def estimate(self) -> MotorPerformance:
        """Run full analytical performance estimation."""
        R_phase = self._phase_resistance()
        I = self._phase_current(R_phase)
        P_cu = self._copper_loss(I, R_phase)
        P_fe = self._core_loss()
        P_loss = P_cu + P_fe
        P_in = self.rated_power_w + P_loss
        eta = self.rated_power_w / P_in if P_in > 0 else 0.0
        T = self._rated_torque()

        return MotorPerformance(
            output_power_w=self.rated_power_w,
            copper_loss_w=P_cu,
            core_loss_w=P_fe,
            total_loss_w=P_loss,
            input_power_w=P_in,
            efficiency=eta,
            rated_torque_nm=T,
            rated_speed_rpm=self.rated_speed_rpm,
            phase_current_a=I,
        )
