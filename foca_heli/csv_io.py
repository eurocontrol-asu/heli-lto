"""
CSV input/output with schema auto-detection.

Supports two input schemas:
  OLD (existing plugin):
      engine_name, engine_type, max_shp_per_engine, number_of_engines, ...
      (ignored: shp_correction_factor, gi1_*, gi2_*, to_*, ap_* columns —
       these are pre-computed values we replace with SHP-driven formulas)
  NEW (proposed):
      engine_name, helicopter_category, max_shp_per_engine, number_of_engines

Optional airframe lookup:
  When input is OLD schema and has twin-turboshaft rows, we need MTOM to
  classify light vs heavy. If an airframe CSV is provided (with columns
  including engine_name, mtow), we look up MTOM by joining on
  the engine_name. If not, twin turboshaft rows raise during classification.
"""

import csv
import io
from dataclasses import dataclass
from typing import Optional

from foca_heli.operational_profiles import (
    HelicopterCategory, derive_category,
)


SCHEMA_OLD = "OLD"
SCHEMA_NEW = "NEW"


@dataclass
class EngineRow:
    """One engine entry read from a CSV, normalized."""
    engine_name: str
    category: HelicopterCategory
    max_shp_per_engine: float
    number_of_engines: int
    # Optional extras
    mtom_kg: Optional[float] = None
    source_row_index: Optional[int] = None


def detect_schema(fieldnames: list[str]) -> str:
    """Detect which schema a CSV uses based on its column names."""
    fs = {f.lower() for f in fieldnames}
    if "helicopter_category" in fs:
        return SCHEMA_NEW
    if "engine_type" in fs:
        return SCHEMA_OLD
    raise ValueError(
        "CSV does not match a known schema. Expected either "
        "'helicopter_category' (NEW) or 'engine_type' (OLD) column. "
        f"Found: {sorted(fieldnames)}"
    )


def load_airframe_mtoms(path: str) -> dict[str, float]:
    """Load a mapping of engine_name -> MTOM from an airframe CSV.

    Expects columns: engine_name (or engine), mtow.
    Used to classify twin turboshaft helicopters (LIGHT vs HEAVY).
    """
    out: dict[str, float] = {}
    with open(path, newline="") as fp:
        reader = csv.DictReader(fp)
        if reader.fieldnames is None:
            return out
        # Accept both 'engine_name' and 'engine' as the key column
        key_col = None
        for candidate in ("engine_name", "engine"):
            if candidate in reader.fieldnames:
                key_col = candidate
                break
        if key_col is None:
            return out
        mtow_col = None
        for candidate in ("mtow", "mtom_kg", "mtom", "max_takeoff_weight_kg"):
            if candidate in reader.fieldnames:
                mtow_col = candidate
                break
        if mtow_col is None:
            return out

        for row in reader:
            name = (row.get(key_col) or "").strip()
            if not name:
                continue
            try:
                mtow = float(row.get(mtow_col) or "0")
            except (TypeError, ValueError):
                continue
            if mtow > 0:
                out[name] = mtow
    return out


def read_engines_csv(
    path: str,
    airframe_mtoms: Optional[dict[str, float]] = None,
    strict: bool = False,
    use_built_in_mtoms: bool = True,
) -> list[EngineRow]:
    """Read an engine CSV and return normalized EngineRow entries.

    Auto-detects OLD vs NEW schema. For OLD schema with twin turboshaft
    rows, uses `airframe_mtoms` to classify LIGHT vs HEAVY. If that lookup
    fails (or no airframe dict provided) and `use_built_in_mtoms` is True,
    falls back to the package's hand-curated lookup (see airframe_mtoms.py).

    If `strict` is True, twin turboshaft rows without MTOM data raise.
    If False (default), they fall back to TWIN_TURBOSHAFT_LIGHT with a
    warning printed to stderr. The LIGHT default is chosen because (a)
    the LIGHT category covers a wider MTOM range in practice, and (b)
    applying HEAVY power settings to a LIGHT helicopter overestimates
    emissions more than the reverse, so LIGHT is conservative.
    """
    import sys as _sys

    # Merge built-in + user-supplied MTOMs. User-supplied wins on conflict.
    combined_mtoms: dict[str, float] = {}
    if use_built_in_mtoms:
        from foca_heli.airframe_mtoms import built_in_mtom_dict
        combined_mtoms.update(built_in_mtom_dict())
    if airframe_mtoms:
        combined_mtoms.update(airframe_mtoms)

    # Normalize keys for lookup (case-insensitive, whitespace-collapsed)
    def _norm(s: str) -> str:
        return " ".join(s.upper().split())

    normalized_mtoms = {_norm(k): v for k, v in combined_mtoms.items()}

    rows: list[EngineRow] = []
    with open(path, newline="") as fp:
        reader = csv.DictReader(fp)
        if reader.fieldnames is None:
            return rows
        schema = detect_schema(reader.fieldnames)

        for i, row in enumerate(reader, start=1):
            try:
                engine_name = (row.get("engine_name") or "").strip()
                if not engine_name:
                    continue
                max_shp = float(row["max_shp_per_engine"])
                n_eng = int(row["number_of_engines"])

                category: HelicopterCategory
                mtom: Optional[float] = None

                if schema == SCHEMA_NEW:
                    cat_str = (row.get("helicopter_category") or "").strip().upper()
                    if cat_str not in (
                        "PISTON",
                        "SINGLE_TURBOSHAFT",
                        "TWIN_TURBOSHAFT_LIGHT",
                        "TWIN_TURBOSHAFT_HEAVY",
                    ):
                        raise ValueError(
                            f"Invalid helicopter_category {cat_str!r} "
                            f"at row {i}"
                        )
                    category = cat_str  # type: ignore[assignment]
                else:
                    # OLD schema: derive category
                    etype = (row.get("engine_type") or "").strip()
                    if etype.upper() == "TURBOSHAFT" and n_eng >= 2:
                        mtom = normalized_mtoms.get(_norm(engine_name))
                        if mtom is None:
                            if strict:
                                raise ValueError(
                                    f"Twin turboshaft row {i} ({engine_name}) "
                                    "has no MTOM in built-in or user-provided "
                                    "lookup. Provide --airframe or use NEW "
                                    "schema with explicit helicopter_category."
                                )
                            _sys.stderr.write(
                                f"WARNING: row {i} ({engine_name}) is twin "
                                f"turboshaft without MTOM; defaulting to "
                                f"TWIN_TURBOSHAFT_LIGHT\n"
                            )
                            category = "TWIN_TURBOSHAFT_LIGHT"
                        else:
                            category = derive_category(etype, n_eng, mtom)
                    else:
                        category = derive_category(etype, n_eng, mtom)

                rows.append(EngineRow(
                    engine_name=engine_name,
                    category=category,
                    max_shp_per_engine=max_shp,
                    number_of_engines=n_eng,
                    mtom_kg=mtom,
                    source_row_index=i,
                ))
            except Exception as e:
                # Surface parse errors with row context
                raise ValueError(
                    f"Error parsing row {i} of {path!r}: {e}"
                ) from e

    return rows


# ---------------------------------------------------------------------------
# Output writer
# ---------------------------------------------------------------------------

LTO_OUTPUT_COLUMNS = [
    "engine_name",
    "helicopter_category",
    "max_shp_per_engine",
    "number_of_engines",
    # LTO totals
    "lto_fuel_kg",
    "lto_nox_g",
    "lto_hc_g",
    "lto_co_g",
    "lto_pm_g",
    "lto_co2_g",
    # GI mode
    "gi_power_fraction", "gi_time_s",
    "gi_fuel_flow_kg_s_per_engine", "gi_fuel_kg",
    "gi_nox_g", "gi_hc_g", "gi_co_g", "gi_pm_g", "gi_co2_g",
    # TO mode
    "to_power_fraction", "to_time_s",
    "to_fuel_flow_kg_s_per_engine", "to_fuel_kg",
    "to_nox_g", "to_hc_g", "to_co_g", "to_pm_g", "to_co2_g",
    # AP mode
    "ap_power_fraction", "ap_time_s",
    "ap_fuel_flow_kg_s_per_engine", "ap_fuel_kg",
    "ap_nox_g", "ap_hc_g", "ap_co_g", "ap_pm_g", "ap_co2_g",
]


def write_lto_csv(
    path: str,
    rows: list[tuple[EngineRow, dict]],
) -> None:
    """Write per-engine LTO results to CSV.

    rows: list of (EngineRow, lto_dict) tuples where lto_dict comes
    from lto.lto_to_dict(result).
    """
    with open(path, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=LTO_OUTPUT_COLUMNS)
        writer.writeheader()
        for engine, lto_dict in rows:
            out_row = {
                "engine_name": engine.engine_name,
                "helicopter_category": engine.category,
                "max_shp_per_engine": engine.max_shp_per_engine,
                "number_of_engines": engine.number_of_engines,
            }
            out_row.update(lto_dict)
            writer.writerow(out_row)
