"""
Full LTO emissions calculation.

Per FOCA 2015 section 4.1:

    LTO_Fuel = 60 * (GI_t * GI_FF + TO_t * TO_FF + AP_t * AP_FF) * n_engines

    LTO_Pollutant = 60 * (GI_t * GI_FF * GI_EI
                        + TO_t * TO_FF * TO_EI
                        + AP_t * AP_FF * AP_EI) * n_engines

Times in minutes (converted to seconds by the ×60 factor), fuel flow
in kg/s, EI in g/kg, so pollutant is in g.

This module produces dict output, not plugin Emission objects. That
makes it usable anywhere — notebooks, scripts, CSV pipelines — with
no plugin dependency.
"""

from dataclasses import dataclass, asdict

from foca_heli.strategies import HelicopterEmissionStrategy, ModeEmissions


@dataclass(frozen=True)
class ModeResult:
    """Totals for one mode (GI, TO, or AP) of a full LTO.

    Per-mode values are summed across n_engines. Units in field names.
    """
    mode: str                      # "GI" | "TO" | "AP"
    power_fraction: float
    time_s: float
    fuel_flow_kg_s_per_engine: float
    fuel_kg: float
    nox_g: float
    hc_g: float
    co_g: float
    pm_g: float
    co2_g: float


@dataclass(frozen=True)
class LtoResult:
    """Full-LTO totals plus per-mode breakdown."""
    fuel_kg: float
    nox_g: float
    hc_g: float
    co_g: float
    pm_g: float
    co2_g: float
    modes: list[ModeResult]


def compute_lto(strategy: HelicopterEmissionStrategy) -> LtoResult:
    """Compute full-LTO totals for a helicopter.

    A full LTO = one departure + one arrival rotation, with GI covering
    both halves (5 min total in the 2015 edition).
    """
    profile = strategy.profile
    n = strategy.number_of_engines

    gi = _mode_result("GI", profile.gi_power, profile.gi_time_min, strategy.gi(), n)
    to = _mode_result("TO", profile.to_power, profile.to_time_min, strategy.take_off(), n)
    ap = _mode_result("AP", profile.ap_power, profile.ap_time_min, strategy.approach(), n)

    return LtoResult(
        fuel_kg=gi.fuel_kg + to.fuel_kg + ap.fuel_kg,
        nox_g  =gi.nox_g   + to.nox_g   + ap.nox_g,
        hc_g   =gi.hc_g    + to.hc_g    + ap.hc_g,
        co_g   =gi.co_g    + to.co_g    + ap.co_g,
        pm_g   =gi.pm_g    + to.pm_g    + ap.pm_g,
        co2_g  =gi.co2_g   + to.co2_g   + ap.co2_g,
        modes=[gi, to, ap],
    )


def _mode_result(
    name: str,
    power_fraction: float,
    time_min: float,
    em: ModeEmissions,
    n_engines: int,
) -> ModeResult:
    time_s = time_min * 60.0
    fuel_per_eng = em.fuel_flow_kg_s * time_s
    fuel_total = fuel_per_eng * n_engines
    return ModeResult(
        mode=name,
        power_fraction=power_fraction,
        time_s=time_s,
        fuel_flow_kg_s_per_engine=em.fuel_flow_kg_s,
        fuel_kg=fuel_total,
        nox_g =fuel_total * em.ei_nox_g_kg,
        hc_g  =fuel_total * em.ei_hc_g_kg,
        co_g  =fuel_total * em.ei_co_g_kg,
        pm_g  =fuel_total * em.ei_pm_g_kg,
        co2_g =fuel_total * em.co2_g_kg,
    )


def lto_to_dict(result: LtoResult) -> dict:
    """Flatten an LtoResult for JSON/CSV output.

    Mode breakdown columns are prefixed with the mode name:
    gi_fuel_kg, gi_nox_g, ..., to_fuel_kg, ..., ap_pm_g, etc.
    """
    d = {
        "lto_fuel_kg": result.fuel_kg,
        "lto_nox_g":   result.nox_g,
        "lto_hc_g":    result.hc_g,
        "lto_co_g":    result.co_g,
        "lto_pm_g":    result.pm_g,
        "lto_co2_g":   result.co2_g,
    }
    for m in result.modes:
        md = asdict(m)
        prefix = m.mode.lower()
        # keep prefix consistent, strip the mode field from dict
        md.pop("mode")
        for k, v in md.items():
            d[f"{prefix}_{k}"] = v
    return d
