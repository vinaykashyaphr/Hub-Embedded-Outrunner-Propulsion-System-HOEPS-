"""
MPSE — Magneto Propulsive Solar Engine
Design and analysis pipeline.

Runs the complete analytical design sequence:
  1. Motor analytical sizing (magnetic circuit method)
  1b. Motor performance estimation (copper + core losses)
  2. Ducted propeller BEM design
  2b. Blade geometry plots
  3. CFD results comparison

Reference: Vinay Kashyap H R et al., KSCST Ref: 44S_BE_2684, 2020-21.
"""

from motor.materials import SMCO28, JNEX900
from motor.sizing import MotorSpec, MotorSizer
from motor.performance import MotorPerformanceEstimator
from propeller.bem import PropellerSpec, BEMDesigner
from propeller.geometry import plot_all
from cfd.comparison import compare_configurations


import os
print("Running from:", os.getcwd())


def main():
    print("\n" + "=" * 55)
    print("  MAGNETO PROPULSIVE SOLAR ENGINE")
    print("  Analytical Design Pipeline")
    print("=" * 55 + "\n")

    # --- Step 1: Motor sizing ---
    print("[ 1 ] MOTOR ANALYTICAL SIZING")
    print(f"      Magnet  : {SMCO28.name}  (Br = {SMCO28.residual_flux_density} T)")
    print(f"      Core    : {JNEX900.name}  (W10/50 = {JNEX900.core_loss_W10_50} W/kg)\n")

    spec = MotorSpec(
        rated_power_w=13_000,
        rated_speed_rpm=2300,
        target_efficiency=0.85,
    )
    sizer = MotorSizer(spec)
    geom = sizer.size()
    sizer.report(geom)

    f_elec = geom.electrical_frequency_hz(spec.rated_speed_rpm)
    core_loss = JNEX900.core_loss_at(f_elec)
    print(f"\n  Electrical frequency  : {f_elec:.1f} Hz")
    print(f"  Core loss at {f_elec:.0f} Hz : {core_loss:.2f} W/kg\n")

    # --- Step 1b: Performance estimation ---
    print("[ 1b ] MOTOR PERFORMANCE ESTIMATION")
    estimator = MotorPerformanceEstimator(
        geometry=geom,
        core_material=JNEX900,
        rated_power_w=spec.rated_power_w,
        rated_speed_rpm=spec.rated_speed_rpm,
    )
    perf = estimator.estimate()
    print()
    perf.print_performance()

    # --- Step 2: Propeller BEM design ---
    print("\n[ 2 ] PROPELLER BEM DESIGN")
    prop_spec = PropellerSpec(
        required_power_w=12_000,
        rated_speed_rpm=2260,
        tip_radius_m=0.5,
        hub_radius_m=0.13,
        freestream_velocity_ms=40.0,
        air_density_kgm3=1.23,
        num_blades=5,
        design_cl=0.7,
    )
    designer = BEMDesigner(prop_spec)
    blade = designer.design()
    print()
    blade.print_geometry_table()

    # --- Step 2b: Blade geometry plots ---
    print("\n[ 2b ] GENERATING BLADE GEOMETRY PLOTS")
    plot_all(blade, output_dir="plots")

    # --- Step 3: CFD comparison ---
    print("\n[ 3 ] CFD CONFIGURATION COMPARISON")
    metrics = compare_configurations()
    print()
    metrics.print_comparison()

    print("\nPipeline complete.\n")


if __name__ == "__main__":
    main()
