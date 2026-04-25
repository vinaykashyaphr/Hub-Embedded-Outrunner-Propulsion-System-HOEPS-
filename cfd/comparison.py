"""
Performance comparison between shafted and motor-embedded configurations.

Computes improvement metrics from CFD results (Table 7.1 of MPSE report).
"""

from dataclasses import dataclass
from cfd.results import CFDResult, SHAFTED_RESULT, MOTOR_EMBEDDED_RESULT


@dataclass
class ComparisonMetrics:
    """Performance delta between motor-embedded and shafted configurations."""
    thrust_improvement_pct: float
    torque_reduction_pct: float
    exit_velocity_improvement_pct: float
    thrust_gain_n: float
    torque_saving_nm: float

    def print_comparison(self) -> None:
        print("=" * 55)
        print("  MPSE Configuration Comparison — Table 7.1")
        print("=" * 55)
        print(f"  {'Metric':<30} {'Shafted':>10} {'Motor-Emb':>10}")
        print("-" * 55)
        s = SHAFTED_RESULT
        m = MOTOR_EMBEDDED_RESULT
        print(f"  {'Mean Torque (Nm)':<30} {s.mean_torque_nm:>10.1f} {m.mean_torque_nm:>10.1f}")
        print(f"  {'Total Thrust (N)':<30} {s.total_thrust_n:>10.1f} {m.total_thrust_n:>10.1f}")
        print(f"  {'Exit Velocity (m/s)':<30} {s.exit_velocity_ms:>10.1f} {m.exit_velocity_ms:>10.1f}")
        print("-" * 55)
        print(f"  Thrust Improvement    : +{self.thrust_improvement_pct:.1f}%  (+{self.thrust_gain_n:.1f} N)")
        print(f"  Torque Reduction      : -{self.torque_reduction_pct:.1f}%  (-{self.torque_saving_nm:.1f} Nm)")
        print("=" * 55)


def compare_configurations(
    baseline: CFDResult = SHAFTED_RESULT,
    improved: CFDResult = MOTOR_EMBEDDED_RESULT,
) -> ComparisonMetrics:
    """Compute improvement metrics from two CFD results."""
    thrust_improvement = (
        (improved.total_thrust_n - baseline.total_thrust_n)
        / baseline.total_thrust_n
    ) * 100.0

    torque_reduction = (
        (baseline.mean_torque_nm - improved.mean_torque_nm)
        / baseline.mean_torque_nm
    ) * 100.0

    exit_vel_improvement = (
        (improved.exit_velocity_ms - baseline.exit_velocity_ms)
        / baseline.exit_velocity_ms
    ) * 100.0

    return ComparisonMetrics(
        thrust_improvement_pct=thrust_improvement,
        torque_reduction_pct=torque_reduction,
        exit_velocity_improvement_pct=exit_vel_improvement,
        thrust_gain_n=improved.total_thrust_n - baseline.total_thrust_n,
        torque_saving_nm=baseline.mean_torque_nm - improved.mean_torque_nm,
    )
