"""
Engine-name to airframe MTOM lookup for helicopter category classification.

Used when the source CSV doesn't specify helicopter_category explicitly
and the engine is a twin turboshaft (LIGHT vs HEAVY depends on MTOM per
FOCA 2015 section 2.4, threshold 3400 kg).

For each engine name we record a representative airframe and its MTOM.
When an engine powers multiple airframes with different MTOMs, we choose
the most common/representative configuration and note alternatives.

All MTOMs verified from authoritative sources (manufacturer data sheets,
EASA TCDS, SKYbrary, Wikipedia airframe specs). See AIRFRAME_MTOM_SOURCES.md
for the full citation list.

Format: engine_name (uppercase, as found in default_helicopter_engine_ei.csv)
  -> (representative_airframe, mtom_kg, source_summary)

Notes:
- Engine names match the *exact* spelling found in the plugin's
  default_helicopter_engine_ei.csv. Spaces and hyphens matter.
- When the CSV has both "ARRIEL 1D1" (with space) and "ARRIEL1K1" (no space),
  we preserve both. The lookup is case-insensitive with whitespace
  normalized.
- Piston and single-turboshaft entries are included for completeness but
  don't affect FOCA category classification (single turboshaft is its own
  category regardless of weight).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AirframeMapping:
    """One engine → representative airframe mapping."""
    engine_name: str
    representative_airframe: str
    mtom_kg: float
    source: str
    # Category the derived FOCA classification gives (for reference only;
    # the classifier derives this at runtime using MTOM + n_engines).
    expected_category: Optional[str] = None


# ---------------------------------------------------------------------------
# TWIN TURBOSHAFT — the category that actually needs MTOM for classification
# ---------------------------------------------------------------------------

TWIN_TURBOSHAFT_MAPPINGS: list[AirframeMapping] = [
    # --- Turbomeca/Safran Arriel 1 series (twin variants) ---
    AirframeMapping(
        "ARRIEL 1A1", "SA365C1 Dauphin 2", 3400.0,
        "Wikipedia AS365 Dauphin: SA365C with Arriel 1A1, 3400 kg MTOW; "
        "EASA TCDS E.073 confirms Arriel 1A1 for twin-engine use",
        "TWIN_TURBOSHAFT_LIGHT",  # right at threshold, tie goes to LIGHT
    ),
    AirframeMapping(
        "ARRIEL 1A2", "SA365C2 Dauphin 2", 3400.0,
        "Wikipedia AS365 Dauphin: SA365C2 with Arriel 1A2; same airframe "
        "family as SA365C1 (3400 kg)",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "ARRIEL 1C", "SA365N Dauphin 2", 3850.0,
        "Wikipedia AS365 Dauphin: SA365N (initial) with 660 shp Arriel 1C, "
        "MTOW 3850 kg (later raised to 4000 kg)",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "ARRIEL 1C1", "AS365N1 Dauphin 2", 4100.0,
        "Wikipedia AS365 Dauphin: AS365N1 with 705 shp Arriel 1C1, MTOW 4100 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "ARRIEL 1D1", "AS355N Twin Squirrel", 2600.0,
        "Arriel 1D1 at 712 SHP in twin config goes on AS355N Ecureuil 2 / "
        "Twin Squirrel (airframe CSV: AS-355 = 2600 kg). Note: also used as "
        "single on AS350B2 at 732 SHP (different row in CSV)",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "ARRIEL 1E2", "MBB-BK 117 C1 / EC145", 3585.0,
        "FAA AD 2009-12-51 and StandardAero: Arriel 1E2 on Eurocopter "
        "Deutschland MBB-BK117-C1. Helicopter Specs: BK117-C1/C2 MTOW 3350-3585 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    # ARRIEL1K1 appears without space in CSV
    AirframeMapping(
        "ARRIEL1K1", "Agusta A109K2", 2720.0,
        "TAR 15/21B/3 Aviation.govt.nz: Arriel 1K1 is used on Agusta A109K2; "
        "A109K2 MTOW 2720 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),

    # --- Turbomeca/Safran Arriel 2 series ---
    AirframeMapping(
        "ARRIEL 2C", "AS365 N3 Dauphin 2", 4300.0,
        "Wikipedia AS365 Dauphin: AS365 N3 with 851 shp Arriel 2C, MTOW 4300 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "ARRIEL 2C1", "EC155 B", 4800.0,
        "Globalmilitary.net EC155 B: Arriel 2C1, MTOW 4800 kg "
        "(Dauphin N3 family derivative)",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "ARRIEL 2C2", "EC155 B1 / HH-65C", 4950.0,
        "Wikipedia EC155: B1 with Arriel 2C2, MTOW 4950 kg. Also HH-65C "
        "(Arriel 2C2-CG) at 4300 kg; we use the civilian EC155 B1 value",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "ARRIEL 2S1", "Sikorsky S-76C+", 5307.0,
        "Wikipedia S-76: S-76C+ with Arriel 2S1 + FADEC, MTOW 5307 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),

    # --- Turbomeca/Safran Arrius series ---
    AirframeMapping(
        "ARRIUS 1A", "AS355 F Ecureuil 2 / EC135 early prototype", 2540.0,
        "EASA TCDS E.080: Arrius 1/1A1 for twin-engines helicopters. "
        "Arrius 1A was used on early EC355 (AS355 F2) derivatives; AS355 MTOW ~2540 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "ARRIUS 2B1", "EC135 T1", 2720.0,
        "Wikipedia EC135: T1 with 435 kW (583 shp) Arrius 2B1, initial MTOW 2630 kg, "
        "later 2720 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "ARRIUS 2B2", "EC135 T2 / T2+", 2910.0,
        "Wikipedia/Skybrary EC135: T2 and T2+ with Arriel 2B2, MTOW 2910-2950 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "ARRIUS 2K", "Agusta A109 Power / AW109 Power", 2850.0,
        "Safran: Arrius 2K2 drives the AW109 Power. AW109 Power MTOW 2850 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),

    # --- Pratt & Whitney PW200 series ---
    AirframeMapping(
        "PW206A", "Agusta A109 Power (early)", 2850.0,
        "P&W PW200 page: PW206A for Agusta A109. A109 Power MTOW 2850 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "PW206C", "Agusta A109 E Power", 2850.0,
        "P&W PW200 page: PW206C for Leonardo A109E Power. Confirmed by "
        "FOCA 2015 Appendix B validation (A109E, PW206C, 2850 kg MTOW)",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "PW207C", "Leonardo A109 Grand / AW109 Nexus", 3175.0,
        "P&W PW200 page: PW207C for Leonardo A109 Grand and AW109 Nexus. "
        "A109 Grand MTOW 3175 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),

    # --- Pratt & Whitney PT6 series ---
    AirframeMapping(
        "PT6B-36A", "Sikorsky S-76B", 5307.0,
        "Wikipedia S-76: S-76B with PT6B-36A or PT6B-36B, MTOW 5307 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "PT6C-67C", "AgustaWestland AW139", 6400.0,
        "Wikipedia/SKYbrary AW139: two PT6C-67C, MTOW 6400 kg (original) "
        "or 6800/7000 kg (uprated). We use 6400 kg as the baseline",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "PT6T-3", "Bell 212 Twin Huey", 5080.0,
        "Wikipedia/SKYbrary Bell 212: PT6T-3 Twin-Pac (two power sections, "
        "combined 1800 shp), MTOW 5080 kg. Note: the heli CSV lists PT6T-3 "
        "with n_engines=2 treating each power section as one engine",
        "TWIN_TURBOSHAFT_HEAVY",
    ),

    # --- Allison/Rolls-Royce DDA 250 series (twin variants on Bo 105 family) ---
    AirframeMapping(
        "DDA250-C20", "MBB Bo 105 C (initial)", 2300.0,
        "Wikipedia Bo 105: Bo 105C with Allison 250-C20, MTOW ~2300 kg "
        "(later raised to 2400 kg)",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "DDA250-C20B", "MBB Bo 105 CB / CBS", 2500.0,
        "Wikipedia/SKYbrary Bo 105: Bo 105CB/CBS with 420 shp Allison 250-C20B, "
        "MTOW 2500 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "DDA250-C20F", "MBB Bo 105 CBS", 2500.0,
        "Bo 105 variant; DDA250-C20F is a minor subvariant on Bo 105 family. "
        "MTOW 2500 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "DDA250-C20R", "MBB Bo 105 LS A1 (Canada)", 2500.0,
        "Bo 105 variant with C20R variant of Allison 250. MTOW 2500 kg "
        "(LS A1); later LS A3 Superlifter was 2850 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "DDA250-C20R/1", "MBB Bo 105 LS A3", 2600.0,
        "Wikipedia Bo 105: LS A3 (1986) with DDA250-C20R variants, MTOW 2600 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),
    AirframeMapping(
        "DDA250-C30S", "Sikorsky S-76A (original)", 5307.0,
        "Wikipedia S-76: Original S-76A used Allison 250-C30 engines; "
        "DDA250-C30S is the 650-shp twin subvariant. S-76 MTOW 5307 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "DDA250-C40B", "MD Explorer 900 (early)", 2835.0,
        "DDA 250-C40B at 715 SHP — used in MD Explorer 900 early variants "
        "before switchover to PW207E. MD 900 MTOW 2835 kg",
        "TWIN_TURBOSHAFT_LIGHT",
    ),

    # --- Honeywell/Lycoming LTS101 series ---
    AirframeMapping(
        "LTS101-750B.1", "Aerospatiale HH-65A Dolphin", 4000.0,
        "Wikipedia HH-65 Dolphin: 734 shp LTS101-750B-2 twin; original "
        "HH-65A MTOW 4000 kg (8900 lb)",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "LTS101-750C.1", "MBB-BK 117 A3/A4", 3350.0,
        "BK-117 B2 with LTS101-750B.1: 3350 kg MTOW (generalequipment.info "
        "BK-117 specifications)",
        "TWIN_TURBOSHAFT_LIGHT",
    ),

    # --- Turbomeca MAKILA series ---
    AirframeMapping(
        "MAKILA 1A1", "Eurocopter AS332L1 Super Puma", 8600.0,
        "Eurocopter Technical Data Brochure 2006: AS332L1 Super Puma with "
        "Makila 1A1 engines, MTOW 8600 kg at 8000 kg typical performance data",
        "TWIN_TURBOSHAFT_HEAVY",
    ),

    # --- General Electric T700 / CT7 series ---
    AirframeMapping(
        "T700-GE-700", "Sikorsky UH-60A Black Hawk", 9185.0,
        "Wikipedia UH-60A: T700-GE-700, 1622 shp each, MTOW 20,250 lb = 9185 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "GE CT7-8A", "Sikorsky S-92", 12000.0,
        "SKYbrary/Wikipedia S-92: two CT7-8A at 2520 shp each, MTOW 12000 kg "
        "(some brochures cite 12,835 kg / 28,300 lb)",
        "TWIN_TURBOSHAFT_HEAVY",
    ),

    # --- Klimov TV series (Soviet) ---
    AirframeMapping(
        "TV2-117", "Mil Mi-8 (original)", 12000.0,
        "National Interest/Mi-8 specs: TV2-117 original engine, Mi-8 MTOW 12000 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
    AirframeMapping(
        "TV3-117VMA", "Mil Mi-17 / Mi-171", 13000.0,
        "SKYbrary/Wikipedia Mi-17: TV3-117VM turboshafts, MTOW 13000 kg",
        "TWIN_TURBOSHAFT_HEAVY",
    ),

    # --- General Electric T64 series ---
    AirframeMapping(
        "T 64-GE-7", "Sikorsky HH-53B / CH-53 Sea Stallion", 19050.0,
        "PaveCave/Wikipedia: T64-GE-7 at 3925 shp was upgrade engine for HH-53B "
        "(twin). CH-53A/D MTOW 19,050-21,000 kg. Note: the heli CSV also shows "
        "this engine with n=3 which corresponds to CH-53D variants or "
        "treatment anomaly — both classify as HEAVY",
        "TWIN_TURBOSHAFT_HEAVY",
    ),
]


# ---------------------------------------------------------------------------
# SINGLE TURBOSHAFT — for reference only, no classification impact
# ---------------------------------------------------------------------------

SINGLE_TURBOSHAFT_MAPPINGS: list[AirframeMapping] = [
    AirframeMapping(
        "ARRIEL 1B", "AS350B Squirrel", 2100.0,
        "Wikipedia AS350: AS350B with Arriel 1B, MTOW 2100 kg",
        "SINGLE_TURBOSHAFT",
    ),
    AirframeMapping(
        "ARRIEL 1D", "AS350B1 Squirrel", 2100.0,
        "Wikipedia AS350: AS350B1 with Arriel 1D, MTOW 2100 kg",
        "SINGLE_TURBOSHAFT",
    ),
    # ARRIEL 1D1 intentionally omitted here: the twin-engine AS355N variant
    # (at 712 SHP) is listed in TWIN_TURBOSHAFT_MAPPINGS above with MTOM
    # 2600 kg. The single-engine AS350B2 variant (at 732 SHP) would map to
    # 2250 kg, but single-turboshaft classification doesn't depend on MTOM,
    # so listing it here would create a normalize-collision in the lookup
    # dict and corrupt the twin-engine row. See AIRFRAME_MTOM_SOURCES.md.
    #
    # Many more single-TS engines could be added here. Since they don't
    # affect classification, we leave them unmapped — the category
    # derivation already knows that n_engines=1 + TURBOSHAFT = SINGLE.
]


# ---------------------------------------------------------------------------
# PISTON — for reference only, no classification impact
# ---------------------------------------------------------------------------

PISTON_MAPPINGS: list[AirframeMapping] = [
    AirframeMapping(
        "HIO-360", "Robinson R22 / Enstrom F-28", 620.0,
        "FAA Part 141 training manuals: R22 with HIO-360 (190 hp), MTOW 620 kg",
        "PISTON",
    ),
    AirframeMapping(
        "HIO-540", "Robinson R44 Astro", 1089.0,
        "Wikipedia R44: HIO-540 (245 hp), MTOW 1089 kg (2400 lb)",
        "PISTON",
    ),
    # Others left unmapped; piston is its own category regardless of MTOM.
]


# ---------------------------------------------------------------------------
# Master lookup dict — normalized keys
# ---------------------------------------------------------------------------

def _normalize_engine_name(name: str) -> str:
    """Normalize for dictionary lookup: uppercase, collapse whitespace."""
    return " ".join(name.upper().split())


def _build_lookup() -> dict[str, AirframeMapping]:
    out: dict[str, AirframeMapping] = {}
    for mapping in (
        TWIN_TURBOSHAFT_MAPPINGS
        + SINGLE_TURBOSHAFT_MAPPINGS
        + PISTON_MAPPINGS
    ):
        key = _normalize_engine_name(mapping.engine_name)
        out[key] = mapping
    return out


BUILT_IN_AIRFRAME_MTOMS: dict[str, AirframeMapping] = _build_lookup()


def lookup_mtom_kg(engine_name: str) -> Optional[float]:
    """Look up a built-in MTOM for an engine name. Returns None if unknown."""
    key = _normalize_engine_name(engine_name)
    mapping = BUILT_IN_AIRFRAME_MTOMS.get(key)
    return mapping.mtom_kg if mapping else None


def lookup_airframe(engine_name: str) -> Optional[AirframeMapping]:
    """Look up the full AirframeMapping for an engine name. Returns None if unknown."""
    key = _normalize_engine_name(engine_name)
    return BUILT_IN_AIRFRAME_MTOMS.get(key)


def built_in_mtom_dict() -> dict[str, float]:
    """Return a simple engine_name -> mtom_kg dict usable by csv_io."""
    return {
        mapping.engine_name: mapping.mtom_kg
        for mapping in BUILT_IN_AIRFRAME_MTOMS.values()
    }
