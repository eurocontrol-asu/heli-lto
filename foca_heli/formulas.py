"""
FOCA 2015 helicopter emission formulas.

Reference:
    Rindlisbacher T., Chabbey L., "Guidance on the Determination of
    Helicopter Emissions", FOCA, Edition 2, December 2015.
    Ref: COO.2207.111.2.2015750.

All functions are pure: they take SHP and return fuel flow (kg/s) or
emission indices (g/kg). Stdlib only.

Two SHP parameter conventions appear in the guidance:
    max_shp:  maximum shaft horse power of the engine. Used ONLY to
              select which fuel-flow polynomial to apply (turboshaft
              breakpoints at 600 SHP and 1000 SHP).
    mode_shp: shaft horse power at the operating power setting,
              i.e. max_shp * power_fraction. This is what is plugged
              into every fuel-flow and EI formula.

Sign convention: SHP is in horsepower, not kW. FOCA's formulas were
fitted in HP. 1 SHP = 0.7457 kW.

Documented PDF inconsistencies (resolved in favor of the body text):
  - Piston FF leading coefficient: body text says 19e-12, Appendix E
    plot renders 1.9e-12. We use 1.9e-12 (Appendix E is correct, verified
    by sanity-check at SHP=300).
  - Appendix C twin-heavy power settings use legacy 2009-era values
    (7%/75%/35%) while Table 4 prescribes 6%/66%/32% per the 2015 update.
    We use Table 4 (see operational_profiles.py).
  - Appendix C PM column values are 3-4x lower than section 3.2's PM
    formula predicts. The formula matches Appendix B exactly and the
    Appendix F plot exactly. We use the formula.
"""

import math
from typing import Literal

# ---------------------------------------------------------------------------
# Piston engines (section 3.1)
# ---------------------------------------------------------------------------

def piston_fuel_flow_kg_s(mode_shp: float) -> float:
    """Fuel flow for a piston helicopter engine at the given shaft power.

    Source: FOCA 2015 section 3.1 polynomial, rendered per Appendix E:

        FF = 1.9e-12 * SHP^4 - 1.0e-9  * SHP^3
           + 2.6e-7  * SHP^2 + 4.0e-5  * SHP + 0.006

    Returns kg/s.
    """
    s = float(mode_shp)
    return (
        1.9e-12 * s**4
        - 1.0e-9 * s**3
        + 2.6e-7 * s**2
        + 4.0e-5 * s
        + 0.006
    )


# Piston EIs are tabulated per-power-setting (not a continuous function).
# Source: Tables 5 (NOx), 6 (PM), 7 (mean particle size).

_PISTON_NOX_BY_POWER = {
    0.20: 1.0,   # GI
    0.95: 1.0,   # TO
    0.60: 4.0,   # AP
    0.90: 2.0,   # CRUISE / mean
}

_PISTON_PM_BY_POWER = {
    0.20: 0.05,  # GI
    0.95: 0.10,  # TO
    0.60: 0.04,  # AP
    0.90: 0.07,  # CRUISE / mean
}

_PISTON_MEAN_PARTICLE_SIZE_NM = {
    0.20: 18.9,
    0.60: 29.2,
    0.95: 40.3,
    0.90: 39.3,
}


def piston_ei_nox_g_kg(power_fraction: float) -> float:
    """EI NOx (g/kg) for a piston engine. Source: Table 5.

    Power must be one of the four tabulated values (0.20, 0.60, 0.90, 0.95).
    The guidance does not provide a continuous function.
    """
    return _lookup_or_raise(_PISTON_NOX_BY_POWER, power_fraction, "piston NOx")


def piston_ei_hc_g_kg(mode_shp: float) -> float:
    """EI HC (g/kg) for a piston engine. Source: section 3.1.

        EI_HC ≈ 80 * SHP^(-0.35)
    """
    return 80.0 * (float(mode_shp) ** -0.35)


def piston_ei_co_g_kg(mode_shp: float) -> float:
    """EI CO (g/kg) for a piston engine. Source: section 3.1.

    Constant 1000 g/kg across all power settings. (The guidance treats
    piston CO as a flat approximation; see Appendix E plot.)
    """
    _ = mode_shp  # signature symmetry with turboshaft equivalent
    return 1000.0


def piston_ei_pm_g_kg(power_fraction: float) -> float:
    """EI PM non-volatile (g/kg) for a piston engine. Source: Table 6."""
    return _lookup_or_raise(_PISTON_PM_BY_POWER, power_fraction, "piston PM")


def piston_mean_particle_size_nm(power_fraction: float) -> float:
    """Mean nvPM particle size (nm) for piston engines. Source: Table 7."""
    return _lookup_or_raise(
        _PISTON_MEAN_PARTICLE_SIZE_NM, power_fraction, "piston particle size"
    )


# ---------------------------------------------------------------------------
# Turboshaft engines (section 3.2)
# ---------------------------------------------------------------------------

def turboshaft_fuel_flow_kg_s(max_shp: float, mode_shp: float) -> float:
    """Fuel flow (kg/s) for a turboshaft engine.

    Polynomial selected by MAX SHP, then evaluated at MODE SHP.
    Breakpoints: <=600, 601..1000, >1000.
    Source: FOCA 2015 section 3.2.
    """
    if max_shp > 1000.0:
        return _turboshaft_ff_above_1000(mode_shp)
    if max_shp > 600.0:
        return _turboshaft_ff_600_to_1000(mode_shp)
    return _turboshaft_ff_up_to_600(mode_shp)


def _turboshaft_ff_above_1000(s: float) -> float:
    s = float(s)
    return (
        4.0539e-18 * s**5
        - 3.16298e-14 * s**4
        + 9.2087e-11 * s**3
        - 1.2156e-7 * s**2
        + 1.1476e-4 * s
        + 0.01256
    )


def _turboshaft_ff_600_to_1000(s: float) -> float:
    s = float(s)
    return (
        3.3158e-16 * s**5
        - 1.0175e-12 * s**4
        + 1.1627e-9 * s**3
        - 5.9528e-7 * s**2
        + 1.8168e-4 * s
        + 0.0062945
    )


def _turboshaft_ff_up_to_600(s: float) -> float:
    s = float(s)
    return (
        2.197e-15 * s**5
        - 4.4441e-12 * s**4
        + 3.4208e-9 * s**3
        - 1.2138e-6 * s**2
        + 2.414e-4 * s
        + 0.004583
    )


def turboshaft_ei_nox_g_kg(mode_shp: float) -> float:
    """EI NOx (g/kg) for a turboshaft engine. Source: section 3.2.

        EI_NOx ≈ 0.2113 * SHP^0.5677
    """
    return 0.2113 * (float(mode_shp) ** 0.5677)


def turboshaft_ei_hc_g_kg(mode_shp: float) -> float:
    """EI HC (g/kg) for a turboshaft engine. Source: section 3.2.

        EI_HC ≈ 3819 * SHP^(-1.0801)
    """
    return 3819.0 * (float(mode_shp) ** -1.0801)


def turboshaft_ei_co_g_kg(mode_shp: float) -> float:
    """EI CO (g/kg) for a turboshaft engine. Source: section 3.2.

        EI_CO ≈ 5660 * SHP^(-1.11)
    """
    return 5660.0 * (float(mode_shp) ** -1.11)


def turboshaft_ei_pm_nvol_g_kg(mode_shp: float) -> float:
    """EI PM non-volatile mass (g/kg) for a turboshaft engine. Source: section 3.2.

        EI_PM ≈ -4.8e-8 * SHP^2 + 2.3664e-4 * SHP + 0.1056
    """
    s = float(mode_shp)
    return -4.8e-8 * s**2 + 2.3664e-4 * s + 0.1056


# Mean particle size lookup (Table 8), keyed by category and power setting.
_TURBOSHAFT_PARTICLE_SIZE_NM = {
    "TWIN_TURBOSHAFT_LIGHT": {
        0.07: 20.0, 0.38: 21.8, 0.78: 35.8, 0.65: 31.1,
    },
    "SINGLE_TURBOSHAFT": {
        0.13: 19.1, 0.46: 24.2, 0.87: 38.5, 0.80: 36.5,
    },
    "TWIN_TURBOSHAFT_HEAVY": {
        0.06: 20.2, 0.32: 20.4, 0.66: 31.5, 0.62: 30.0,
    },
}


def turboshaft_mean_particle_size_nm(
    category: Literal[
        "SINGLE_TURBOSHAFT", "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY"
    ],
    power_fraction: float,
) -> float:
    """Mean nvPM particle size (nm) for a turboshaft engine. Source: Table 8."""
    if category not in _TURBOSHAFT_PARTICLE_SIZE_NM:
        raise ValueError(f"Unknown turboshaft category: {category!r}")
    return _lookup_or_raise(
        _TURBOSHAFT_PARTICLE_SIZE_NM[category],
        power_fraction,
        f"{category} particle size",
    )


# ---------------------------------------------------------------------------
# PM number (both engine types)
# ---------------------------------------------------------------------------

_PM_LOGNORMAL_FACTOR = math.exp(4.5 * 1.8**2)


def pm_number_per_kg(ei_pm_g_kg: float, mean_particle_size_nm: float) -> float:
    """PM number per kg fuel.

    Source: PM number formula in sections 3.1 and 3.2.

        PM# = EI_PM / ( (pi/6) * D^3 * exp(4.5 * 1.8^2) )
    """
    d = float(mean_particle_size_nm)
    if d <= 0:
        return 0.0
    volume_term = (math.pi / 6.0) * (d**3) * _PM_LOGNORMAL_FACTOR
    return float(ei_pm_g_kg) / volume_term


# ---------------------------------------------------------------------------
# CO2 factors (by fuel type)
# ---------------------------------------------------------------------------

CO2_FACTOR_AVGAS = 3.10   # kg CO2 per kg AvGas (piston)
CO2_FACTOR_JET = 3.16     # kg CO2 per kg Jet-A (turboshaft)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lookup_or_raise(table: dict, key: float, label: str) -> float:
    """Look up a power setting in an EI table, with float tolerance."""
    for k, v in table.items():
        if abs(k - key) < 1e-6:
            return v
    raise KeyError(
        f"No {label} value tabulated for power fraction {key!r}. "
        f"Available: {sorted(table.keys())}"
    )
