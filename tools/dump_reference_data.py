"""
Dump all FOCA 2015 reference data embedded in foca_heli as CSVs.

Produces:
  piston_ei_tables.csv          Tables 5, 6, 7 (piston EI by power setting)
  turboshaft_particle_size.csv  Table 8 (turboshaft particle size by category + power)
  operational_profiles.csv      Tables 1-4 (times + power settings per category)
  formula_coefficients.csv      All polynomial coefficients and scaling factors
  trajectory_params.csv         Per-category trajectory parameters (flight-manual-sourced)
  airframe_mtoms.csv            Engine → airframe MTOM lookup (37 twin-TS + references)

These are informational dumps. The authoritative source is the Python
code in foca_heli/. Editing these CSVs does NOT change library behavior —
they are outputs, not inputs.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from foca_heli import formulas as F
from foca_heli.operational_profiles import PROFILES, GI_DEPARTURE_FRACTION, GI_ARRIVAL_FRACTION, TWIN_MTOM_THRESHOLD_KG
from foca_heli.trajectory import TRAJECTORY_PARAMS, LTO_CEILING_FT, HOVER_ALT_FT, HOVER_DURATION_S
from foca_heli.airframe_mtoms import (
    TWIN_TURBOSHAFT_MAPPINGS,
    SINGLE_TURBOSHAFT_MAPPINGS,
    PISTON_MAPPINGS,
)


OUT = os.path.join(os.path.dirname(__file__), "..", "reference_data")
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Piston EI tables (5, 6, 7)
# ---------------------------------------------------------------------------

def dump_piston_ei_tables():
    path = os.path.join(OUT, "piston_ei_tables.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "power_fraction", "mode_name",
            "ei_nox_g_kg", "ei_pm_g_kg", "mean_particle_size_nm",
            "source_foca_2015",
        ])
        modes = {
            0.20: "GI (ground idle)",
            0.60: "AP (approach)",
            0.90: "MEAN / CRUISE",
            0.95: "TO (take-off)",
        }
        for power, name in sorted(modes.items()):
            try: nox = F._PISTON_NOX_BY_POWER[power]
            except KeyError: nox = ""
            try: pm = F._PISTON_PM_BY_POWER[power]
            except KeyError: pm = ""
            try: size = F._PISTON_MEAN_PARTICLE_SIZE_NM[power]
            except KeyError: size = ""
            w.writerow([power, name, nox, pm, size,
                        "FOCA 2015 Tables 5, 6, 7"])
    return path


# ---------------------------------------------------------------------------
# 2. Turboshaft particle size (Table 8)
# ---------------------------------------------------------------------------

def dump_turboshaft_particle_size():
    path = os.path.join(OUT, "turboshaft_particle_size.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "helicopter_category", "power_fraction",
            "mean_particle_size_nm", "source_foca_2015",
        ])
        for cat, table in F._TURBOSHAFT_PARTICLE_SIZE_NM.items():
            for power, size in sorted(table.items()):
                w.writerow([cat, power, size, "FOCA 2015 Table 8"])
    return path


# ---------------------------------------------------------------------------
# 3. Operational profiles (Tables 1-4)
# ---------------------------------------------------------------------------

def dump_operational_profiles():
    path = os.path.join(OUT, "operational_profiles.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "helicopter_category",
            "gi_time_min", "to_time_min", "ap_time_min",
            "gi_power_fraction", "to_power_fraction",
            "ap_power_fraction", "mean_power_fraction",
            "source_foca_2015",
        ])
        source_map = {
            "PISTON":                "Table 1",
            "SINGLE_TURBOSHAFT":     "Table 2",
            "TWIN_TURBOSHAFT_LIGHT": "Table 3",
            "TWIN_TURBOSHAFT_HEAVY": "Table 4",
        }
        for cat, p in PROFILES.items():
            w.writerow([
                cat, p.gi_time_min, p.to_time_min, p.ap_time_min,
                p.gi_power, p.to_power, p.ap_power, p.mean_power,
                f"FOCA 2015 {source_map[cat]}",
            ])
    return path


# ---------------------------------------------------------------------------
# 4. Formula coefficients
# ---------------------------------------------------------------------------

def dump_formula_coefficients():
    path = os.path.join(OUT, "formula_coefficients.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "pollutant", "engine_type", "regime", "form",
            "a5", "a4", "a3", "a2", "a1", "a0",
            "source_foca_2015", "notes",
        ])

        # --- Fuel flow polynomials (output in kg/s, input SHP) ---
        # Piston (section 3.1): FF = 1.9e-12·S^4 - 1e-9·S^3 + 2.6e-7·S^2 + 4e-5·S + 0.006
        w.writerow([
            "FF", "piston", "all", "polynomial(shp)",
            "", "1.9e-12", "-1.0e-9", "2.6e-7", "4.0e-5", "0.006",
            "section 3.1 (Appendix E plot)",
            "Body text says 19e-12 but Appendix E plot shows 1.9e-12; "
            "1.9e-12 is correct per sanity check at SHP=300",
        ])
        # Turboshaft <=600 SHP
        w.writerow([
            "FF", "turboshaft", "max_shp<=600", "polynomial(mode_shp)",
            "2.197e-15", "-4.4441e-12", "3.4208e-9", "-1.2138e-6",
            "2.414e-4", "0.004583",
            "section 3.2", "polynomial selected by MAX SHP",
        ])
        # Turboshaft 601..1000 SHP
        w.writerow([
            "FF", "turboshaft", "600<max_shp<=1000", "polynomial(mode_shp)",
            "3.3158e-16", "-1.0175e-12", "1.1627e-9", "-5.9528e-7",
            "1.8168e-4", "0.0062945",
            "section 3.2", "polynomial selected by MAX SHP",
        ])
        # Turboshaft >1000 SHP (5th order)
        w.writerow([
            "FF", "turboshaft", "max_shp>1000", "polynomial(mode_shp)",
            "4.0539e-18", "-3.16298e-14", "9.2087e-11", "-1.2156e-7",
            "1.1476e-4", "0.01256",
            "section 3.2", "polynomial selected by MAX SHP",
        ])

        # --- EI NOx turboshaft (power form) ---
        w.writerow([
            "EI_NOx", "turboshaft", "all", "power_law: a*shp^b",
            "", "", "", "", "0.2113", "b=0.5677",
            "section 3.2", "EI_NOx = 0.2113 * SHP^0.5677 (g/kg)",
        ])

        # --- EI HC turboshaft ---
        w.writerow([
            "EI_HC", "turboshaft", "all", "power_law: a*shp^b",
            "", "", "", "", "3819", "b=-1.0801",
            "section 3.2", "EI_HC = 3819 * SHP^(-1.0801) (g/kg)",
        ])

        # --- EI CO turboshaft ---
        w.writerow([
            "EI_CO", "turboshaft", "all", "power_law: a*shp^b",
            "", "", "", "", "5660", "b=-1.11",
            "section 3.2", "EI_CO = 5660 * SHP^(-1.11) (g/kg)",
        ])

        # --- EI PM turboshaft (quadratic) ---
        w.writerow([
            "EI_PM_nvol", "turboshaft", "all", "polynomial(mode_shp)",
            "", "", "", "-4.8e-8", "2.3664e-4", "0.1056",
            "section 3.2", "EI_PM_nonvolatile (g/kg)",
        ])

        # --- EI HC piston (power form) ---
        w.writerow([
            "EI_HC", "piston", "all", "power_law: a*shp^b",
            "", "", "", "", "80", "b=-0.35",
            "section 3.1", "EI_HC = 80 * SHP^(-0.35) (g/kg)",
        ])

        # --- EI CO piston (constant) ---
        w.writerow([
            "EI_CO", "piston", "all", "constant",
            "", "", "", "", "", "1000",
            "section 3.1", "Flat approximation, 1000 g/kg across power settings",
        ])

        # --- PM number formula (both) ---
        w.writerow([
            "PM_number", "both", "all",
            "EI_PM / ((pi/6) * D^3 * exp(4.5*1.8^2))",
            "", "", "", "", "", "",
            "sections 3.1, 3.2",
            "Lognormal size distribution, GSD=1.8. D in nm gives PM# per kg fuel",
        ])

        # --- CO2 emission factors ---
        w.writerow([
            "CO2", "piston", "AvGas", "linear: factor*fuel_kg",
            "", "", "", "", "", "3.10",
            "standard",
            "CO2_kg = 3.10 * fuel_kg (AvGas combustion)",
        ])
        w.writerow([
            "CO2", "turboshaft", "Jet-A", "linear: factor*fuel_kg",
            "", "", "", "", "", "3.16",
            "standard",
            "CO2_kg = 3.16 * fuel_kg (Jet-A combustion)",
        ])
    return path


# ---------------------------------------------------------------------------
# 5. Trajectory parameters
# ---------------------------------------------------------------------------

def dump_trajectory_params():
    path = os.path.join(OUT, "trajectory_params.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "helicopter_category",
            "climb_roc_fpm", "climb_tas_kt",
            "cruise_tas_kt",
            "approach_tas_initial_kt", "approach_tas_final_kt",
            "approach_rod_initial_fpm", "approach_rod_final_fpm",
            "approach_start_nm",
            "source_notes",
        ])
        source_notes = {
            "PISTON": "FAA Part 141 R22 training syllabus: 500 fpm at 60 kt",
            "SINGLE_TURBOSHAFT": "FOCA 2015 Appendix A (AS350B2 direct)",
            "TWIN_TURBOSHAFT_LIGHT":
                "Extrapolated from AS350B2 baseline scaled for twin-light "
                "class (A109E airliners.net, AeroCorner)",
            "TWIN_TURBOSHAFT_HEAVY":
                "Eurocopter 2006 Technical Data PDF: AS332L1 at 8000 kg ISA SL "
                "(ROC 1920 fpm at 70 kt, rec cruise 139 kt)",
        }
        for cat, p in TRAJECTORY_PARAMS.items():
            w.writerow([
                cat, p.climb_roc_fpm, p.climb_tas_kt, p.cruise_tas_kt,
                p.approach_tas_initial_kt, p.approach_tas_final_kt,
                p.approach_rod_initial_fpm, p.approach_rod_final_fpm,
                p.approach_start_nm, source_notes[cat],
            ])
    return path


# ---------------------------------------------------------------------------
# 6. Airframe MTOMs (already dumped separately but include for completeness)
# ---------------------------------------------------------------------------

def dump_airframe_mtoms():
    path = os.path.join(OUT, "airframe_mtoms.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow([
            "engine_name", "mtow", "representative_airframe",
            "expected_category", "source",
        ])
        for m in TWIN_TURBOSHAFT_MAPPINGS + SINGLE_TURBOSHAFT_MAPPINGS + PISTON_MAPPINGS:
            w.writerow([
                m.engine_name, m.mtom_kg, m.representative_airframe,
                m.expected_category or "", m.source,
            ])
    return path


# ---------------------------------------------------------------------------
# 7. Global constants (single-row CSV for reference)
# ---------------------------------------------------------------------------

def dump_global_constants():
    path = os.path.join(OUT, "global_constants.csv")
    with open(path, "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["constant", "value", "unit", "source"])
        w.writerow(["TWIN_MTOM_THRESHOLD", TWIN_MTOM_THRESHOLD_KG, "kg",
                    "FOCA 2015 section 2.4 (LIGHT vs HEAVY split)"])
        w.writerow(["GI_DEPARTURE_FRACTION", GI_DEPARTURE_FRACTION, "-",
                    "FOCA 2015 Appendix A worked example (4 min / 5 min)"])
        w.writerow(["GI_ARRIVAL_FRACTION", GI_ARRIVAL_FRACTION, "-",
                    "FOCA 2015 Appendix A worked example (1 min / 5 min)"])
        w.writerow(["LTO_CEILING_FT", LTO_CEILING_FT, "ft",
                    "ICAO LTO definition (3000 ft AGL)"])
        w.writerow(["HOVER_ALT_FT", HOVER_ALT_FT, "ft",
                    "FOCA IGE hover altitude"])
        w.writerow(["HOVER_DURATION_S", HOVER_DURATION_S, "s",
                    "FOCA 2015 Appendix A (18 s)"])
        w.writerow(["CO2_FACTOR_AVGAS", F.CO2_FACTOR_AVGAS, "kg CO2 per kg fuel",
                    "AvGas standard"])
        w.writerow(["CO2_FACTOR_JET", F.CO2_FACTOR_JET, "kg CO2 per kg fuel",
                    "Jet-A standard"])
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    paths = [
        dump_piston_ei_tables(),
        dump_turboshaft_particle_size(),
        dump_operational_profiles(),
        dump_formula_coefficients(),
        dump_trajectory_params(),
        dump_airframe_mtoms(),
        dump_global_constants(),
    ]
    for p in paths:
        size = os.path.getsize(p)
        with open(p) as fp:
            n_rows = sum(1 for _ in fp) - 1  # minus header
        print(f"  {os.path.basename(p):40s}  {n_rows:3d} rows  {size:5d} bytes")


if __name__ == "__main__":
    main()
