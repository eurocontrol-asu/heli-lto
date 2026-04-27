"""Factory: build a strategy from engine + airframe attributes."""

from typing import Optional

from foca_heli.operational_profiles import (
    PROFILES, HelicopterCategory, derive_category,
)
from foca_heli.strategies import (
    HelicopterEmissionStrategy, PistonStrategy, TurboshaftStrategy,
)


def make_strategy(
    *,
    category: Optional[HelicopterCategory] = None,
    engine_type: Optional[str] = None,
    max_shp_per_engine: float,
    number_of_engines: int,
    mtom_kg: Optional[float] = None,
) -> HelicopterEmissionStrategy:
    """Build a strategy from engine + airframe attributes.

    Either `category` (preferred) or `engine_type` must be provided.
    If both are given, `category` wins.

    `mtom_kg` is required for twin turboshaft helicopters when category
    is not explicitly given (to choose LIGHT vs HEAVY); ignored otherwise.
    """
    if category is None:
        if engine_type is None:
            raise ValueError("Must provide either `category` or `engine_type`.")
        category = derive_category(engine_type, number_of_engines, mtom_kg)

    profile = PROFILES[category]

    if category == "PISTON":
        return PistonStrategy(
            max_shp_per_engine=max_shp_per_engine,
            number_of_engines=number_of_engines,
            profile=profile,
        )
    return TurboshaftStrategy(
        max_shp_per_engine=max_shp_per_engine,
        number_of_engines=number_of_engines,
        profile=profile,
        category=category,
    )
