"""
Strategy classes: Piston and Turboshaft emission calculation.

Each strategy is stateless per-movement: it holds engine parameters
and produces per-mode emissions on demand.
"""

import abc
from dataclasses import dataclass
from typing import Literal

from foca_heli import formulas
from foca_heli.operational_profiles import OperationalProfile


@dataclass(frozen=True)
class ModeEmissions:
    """Per-mode emission factors and fuel flow. Per single engine."""
    fuel_flow_kg_s: float
    ei_nox_g_kg: float
    ei_hc_g_kg: float
    ei_co_g_kg: float
    ei_pm_g_kg: float
    pm_number_per_kg: float
    co2_g_kg: float


class HelicopterEmissionStrategy(abc.ABC):
    """Abstract strategy: per-mode emissions for one helicopter type."""

    def __init__(
        self,
        max_shp_per_engine: float,
        number_of_engines: int,
        profile: OperationalProfile,
    ):
        if max_shp_per_engine <= 0:
            raise ValueError(f"max_shp_per_engine must be positive, got {max_shp_per_engine!r}")
        if number_of_engines < 1:
            raise ValueError(f"number_of_engines must be >= 1, got {number_of_engines!r}")
        self._max_shp = float(max_shp_per_engine)
        self._n_engines = int(number_of_engines)
        self._profile = profile

    @property
    def max_shp_per_engine(self) -> float: return self._max_shp

    @property
    def number_of_engines(self) -> int: return self._n_engines

    @property
    def profile(self) -> OperationalProfile: return self._profile

    def gi(self) -> ModeEmissions: return self.compute_mode(self._profile.gi_power)
    def take_off(self) -> ModeEmissions: return self.compute_mode(self._profile.to_power)
    def approach(self) -> ModeEmissions: return self.compute_mode(self._profile.ap_power)
    def mean(self) -> ModeEmissions: return self.compute_mode(self._profile.mean_power)

    @abc.abstractmethod
    def compute_mode(self, power_fraction: float) -> ModeEmissions:
        raise NotImplementedError


class PistonStrategy(HelicopterEmissionStrategy):
    """Piston helicopter emissions per FOCA 2015 section 3.1."""

    def compute_mode(self, power_fraction: float) -> ModeEmissions:
        mode_shp = self._max_shp * power_fraction
        ff     = formulas.piston_fuel_flow_kg_s(mode_shp)
        ei_nox = formulas.piston_ei_nox_g_kg(power_fraction)
        ei_hc  = formulas.piston_ei_hc_g_kg(mode_shp)
        ei_co  = formulas.piston_ei_co_g_kg(mode_shp)
        ei_pm  = formulas.piston_ei_pm_g_kg(power_fraction)
        d_nm   = formulas.piston_mean_particle_size_nm(power_fraction)
        pm_n   = formulas.pm_number_per_kg(ei_pm, d_nm)
        co2    = formulas.CO2_FACTOR_AVGAS * 1000.0   # g CO2 per kg fuel
        return ModeEmissions(ff, ei_nox, ei_hc, ei_co, ei_pm, pm_n, co2)


TurboshaftCategory = Literal[
    "SINGLE_TURBOSHAFT", "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY",
]


class TurboshaftStrategy(HelicopterEmissionStrategy):
    """Turboshaft helicopter emissions per FOCA 2015 section 3.2."""

    def __init__(
        self,
        max_shp_per_engine: float,
        number_of_engines: int,
        profile: OperationalProfile,
        category: TurboshaftCategory,
    ):
        super().__init__(max_shp_per_engine, number_of_engines, profile)
        if category not in (
            "SINGLE_TURBOSHAFT", "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY",
        ):
            raise ValueError(f"Invalid turboshaft category: {category!r}")
        self._category = category

    @property
    def category(self) -> TurboshaftCategory: return self._category

    def compute_mode(self, power_fraction: float) -> ModeEmissions:
        mode_shp = self._max_shp * power_fraction
        ff     = formulas.turboshaft_fuel_flow_kg_s(self._max_shp, mode_shp)
        ei_nox = formulas.turboshaft_ei_nox_g_kg(mode_shp)
        ei_hc  = formulas.turboshaft_ei_hc_g_kg(mode_shp)
        ei_co  = formulas.turboshaft_ei_co_g_kg(mode_shp)
        ei_pm  = formulas.turboshaft_ei_pm_nvol_g_kg(mode_shp)
        d_nm   = formulas.turboshaft_mean_particle_size_nm(self._category, power_fraction)
        pm_n   = formulas.pm_number_per_kg(ei_pm, d_nm)
        co2    = formulas.CO2_FACTOR_JET * 1000.0   # g CO2 per kg fuel
        return ModeEmissions(ff, ei_nox, ei_hc, ei_co, ei_pm, pm_n, co2)
