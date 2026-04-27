"""
Operational profiles per helicopter category.

Source: FOCA 2015 guidance, Tables 1 (piston), 2 (single turboshaft),
3 (twin turboshaft light), 4 (twin turboshaft heavy).
"""

from dataclasses import dataclass
from typing import Literal, Optional

HelicopterCategory = Literal[
    "PISTON",
    "SINGLE_TURBOSHAFT",
    "TWIN_TURBOSHAFT_LIGHT",
    "TWIN_TURBOSHAFT_HEAVY",
]


@dataclass(frozen=True)
class OperationalProfile:
    """Times in mode and power fractions for one helicopter category.

    Times in minutes per full LTO (dep + arr combined).
    Power fractions (0..1) of max SHP per engine.
    """
    gi_time_min: float
    to_time_min: float
    ap_time_min: float

    gi_power: float
    to_power: float
    ap_power: float
    mean_power: float


PROFILES: dict[HelicopterCategory, OperationalProfile] = {
    "PISTON": OperationalProfile(
        gi_time_min=5.0, to_time_min=4.0, ap_time_min=5.5,
        gi_power=0.20, to_power=0.95, ap_power=0.60, mean_power=0.90,
    ),
    "SINGLE_TURBOSHAFT": OperationalProfile(
        gi_time_min=5.0, to_time_min=3.0, ap_time_min=5.5,
        gi_power=0.13, to_power=0.87, ap_power=0.46, mean_power=0.80,
    ),
    "TWIN_TURBOSHAFT_LIGHT": OperationalProfile(
        gi_time_min=5.0, to_time_min=3.0, ap_time_min=5.5,
        gi_power=0.07, to_power=0.78, ap_power=0.38, mean_power=0.65,
    ),
    "TWIN_TURBOSHAFT_HEAVY": OperationalProfile(
        gi_time_min=5.0, to_time_min=3.0, ap_time_min=5.5,
        gi_power=0.06, to_power=0.66, ap_power=0.32, mean_power=0.62,
    ),
}


# ---------------------------------------------------------------------------
# GI split between departure and arrival (per Appendix A: 80/20)
# ---------------------------------------------------------------------------

GI_DEPARTURE_FRACTION = 0.8
GI_ARRIVAL_FRACTION   = 0.2

assert abs(GI_DEPARTURE_FRACTION + GI_ARRIVAL_FRACTION - 1.0) < 1e-9


def gi_time_for_movement(profile: OperationalProfile, is_departure: bool) -> float:
    """Return GI time (minutes) charged to one half-LTO movement."""
    fraction = GI_DEPARTURE_FRACTION if is_departure else GI_ARRIVAL_FRACTION
    return profile.gi_time_min * fraction


# ---------------------------------------------------------------------------
# Category derivation from engine + airframe attributes
# ---------------------------------------------------------------------------

TWIN_MTOM_THRESHOLD_KG = 3400.0  # FOCA 2015 section 2.4


def derive_category(
    engine_type: str,
    number_of_engines: int,
    mtom_kg: Optional[float],
) -> HelicopterCategory:
    """Derive helicopter category from engine_type + n_engines + MTOM.

    Used as a fallback when CSV does not specify category explicitly.
    """
    et = (engine_type or "").upper()
    if et == "PISTON":
        return "PISTON"
    if et != "TURBOSHAFT":
        raise ValueError(f"Unknown engine_type: {engine_type!r}")

    if number_of_engines == 1:
        return "SINGLE_TURBOSHAFT"
    if number_of_engines >= 2:
        if mtom_kg is None:
            raise ValueError(
                "Cannot classify twin turboshaft helicopter without MTOM "
                "(needed to choose LIGHT vs HEAVY at 3.4 t threshold)."
            )
        if mtom_kg <= TWIN_MTOM_THRESHOLD_KG:
            return "TWIN_TURBOSHAFT_LIGHT"
        return "TWIN_TURBOSHAFT_HEAVY"

    raise ValueError(f"Invalid number_of_engines: {number_of_engines!r}")
