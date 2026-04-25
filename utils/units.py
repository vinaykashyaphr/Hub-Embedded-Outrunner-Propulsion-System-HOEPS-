"""Physical constants and unit conversion utilities."""

import math

# Air properties at ISA sea level
RHO_ISA_SL = 1.225          # kg/m^3
TEMP_ISA_SL_K = 288.15      # K
PRESSURE_ISA_SL = 101325.0  # Pa

# Magnetic permeability
MU_0 = 4.0 * math.pi * 1e-7  # H/m — free space permeability


def rpm_to_rad_s(rpm: float) -> float:
    return (math.pi / 30.0) * rpm

def rad_s_to_rpm(omega: float) -> float:
    return (30.0 / math.pi) * omega

def mm_to_m(mm: float) -> float:
    return mm * 1e-3

def m_to_mm(m: float) -> float:
    return m * 1e3

def kw_to_w(kw: float) -> float:
    return kw * 1e3

def w_to_kw(w: float) -> float:
    return w * 1e-3
