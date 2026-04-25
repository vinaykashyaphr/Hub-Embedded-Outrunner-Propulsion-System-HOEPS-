"""
CFD simulation results for shafted vs motor-embedded propeller configurations.

Data from SolidWorks Flow Simulation analysis described in Chapter 6.2
of the MPSE report. Results stored as structured data for comparison
and plotting without requiring re-simulation.

Reference: Magneto Propulsive Solar Engine, Vinay Kashyap H R et al.,
           KSCST Ref: 44S_BE_2684, KIT Mangalore, 2020-21.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CFDConditions:
    """Freestream conditions for CFD simulation — Tables 6.2 and 6.4."""
    turbulence_intensity: float     # fraction e.g. 0.15 = 15%
    turbulence_length_m: float      # m
    angular_velocity_rad_s: float   # rad/s
    freestream_velocity_ms: float   # m/s
    air_density_kgm3: float         # kg/m^3


@dataclass(frozen=True)
class CFDResult:
    """Performance result for one propeller configuration."""
    configuration: str              # "Shafted" or "Motor-Embedded"
    mean_torque_nm: float           # Nm — demanded torque
    total_thrust_n: float           # N
    exit_velocity_ms: float         # m/s


# Freestream conditions — identical for both configurations
SIMULATION_CONDITIONS = CFDConditions(
    turbulence_intensity=0.15,
    turbulence_length_m=0.8,
    angular_velocity_rad_s=900.0,
    freestream_velocity_ms=40.0,
    air_density_kgm3=1.23,
)

# Table 6.3 — Shaft driven propeller results
SHAFTED_RESULT = CFDResult(
    configuration="Shafted",
    mean_torque_nm=43.0,
    total_thrust_n=201.9,
    exit_velocity_ms=27.1,
)

# Table 6.5 — Motor-embedded (shaftless) propeller results
MOTOR_EMBEDDED_RESULT = CFDResult(
    configuration="Motor-Embedded",
    mean_torque_nm=41.4,
    total_thrust_n=309.5,
    exit_velocity_ms=30.8,
)
