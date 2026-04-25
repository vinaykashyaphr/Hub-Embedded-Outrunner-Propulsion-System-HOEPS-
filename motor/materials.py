"""
Motor material properties for MPSE design.

Data sourced from:
- Table 5.1: SmCo28 permanent magnet properties
- Table 5.2: 10JNEX900 amorphous electrical steel properties

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PermanentMagnet:
    """Permanent magnet material properties."""
    name: str
    residual_flux_density: float       # T  — Br
    coercive_force: float              # A/m — Hc
    max_energy_density: float          # J/m3 — (BH)max
    relative_recoil_permeability: float  # dimensionless — mu_r
    remanence: float                   # T
    max_working_temp: float            # degC
    curie_temp: float                  # degC


@dataclass(frozen=True)
class CoreMaterial:
    """Electrical steel core material properties."""
    name: str
    lamination_thickness: float        # mm
    dc_max_relative_permeability: float
    saturation_magnetization: float    # T
    specific_resistance: float         # micro-ohm.m
    # Core losses at (frequency_hz, flux_density_T) pairs
    # W/kg values from datasheet
    core_loss_W10_50: float            # W/kg at 50 Hz, 1T
    core_loss_W10_400: float           # W/kg at 400 Hz, 1T
    core_loss_W10_1k: float            # W/kg at 1000 Hz, 1T
    core_loss_W5_2k: float             # W/kg at 2000 Hz, 0.5T
    core_loss_W2_5k: float             # W/kg at 5000 Hz, 0.2T

    def core_loss_at(self, freq_hz: float) -> float:
        """
        Interpolate core loss (W/kg) at given electrical frequency.
        Uses log-linear interpolation between known datasheet points.

        Args:
            freq_hz: Electrical frequency in Hz

        Returns:
            Core loss in W/kg (at approximately 1T flux density)
        """
        freqs = np.array([50.0, 400.0, 1000.0])
        losses = np.array([self.core_loss_W10_50,
                           self.core_loss_W10_400,
                           self.core_loss_W10_1k])
        return float(np.interp(freq_hz, freqs, losses))


# --- Material instances from report ---

SMCO28 = PermanentMagnet(
    name="SmCo28",
    residual_flux_density=1.07,
    coercive_force=820_000,
    max_energy_density=219_350,
    relative_recoil_permeability=1.03842,
    remanence=1.05,
    max_working_temp=300.0,
    curie_temp=785.0,        # midpoint of 750-820 degC range
)

JNEX900 = CoreMaterial(
    name="10JNEX900",
    lamination_thickness=0.10,
    dc_max_relative_permeability=23_000,
    saturation_magnetization=1.8,
    specific_resistance=0.82,
    core_loss_W10_50=0.5,
    core_loss_W10_400=5.7,
    core_loss_W10_1k=18.7,
    core_loss_W5_2k=13.7,
    core_loss_W2_5k=11.3,
)
