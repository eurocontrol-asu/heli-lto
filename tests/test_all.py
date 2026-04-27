"""
Tests for the standalone foca_heli package.

Covers:
  - Round 1 validations (Appendix A/B/C, formula correctness)
  - Round 2 validations (negative tests, edge cases, polynomial selection)
  - Round 3 additions (CSV IO round-trip, trajectory generation)

Run from the standalone/ directory:
    python -m tests.test_all
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from foca_heli import (
    GI_ARRIVAL_FRACTION, GI_DEPARTURE_FRACTION, PROFILES,
    TRAJECTORY_PARAMS, build_arrival, build_departure,
    compute_lto, derive_category, lto_to_dict,
    make_strategy, read_engines_csv,
    to_geojson_feature, to_wkt_linestring_z,
    translate_and_rotate, write_lto_csv,
)
from foca_heli import formulas as F


# ===========================================================================
# Formula-level tests
# ===========================================================================

class AppendixAValidation(unittest.TestCase):
    """AS350B2 / Arriel 1D1, 732 SHP, single engine. FOCA Appendix A."""

    def test_full_lto(self):
        s = make_strategy(
            category="SINGLE_TURBOSHAFT",
            max_shp_per_engine=732,
            number_of_engines=1,
        )
        r = compute_lto(s)
        self.assertAlmostEqual(r.fuel_kg,  24.7, delta=24.7 * 0.05)
        self.assertAlmostEqual(r.nox_g, 145.8, delta=145.8 * 0.05)
        self.assertAlmostEqual(r.hc_g,  269.4, delta=269.4 * 0.05)
        self.assertAlmostEqual(r.co_g,  343.2, delta=343.2 * 0.05)
        self.assertAlmostEqual(r.pm_g,    4.6, delta=4.6 * 0.10)
        # CO2 = fuel × 3.16 kg/kg × 1000 g/kg (Jet-A factor for turboshaft)
        self.assertAlmostEqual(r.co2_g, r.fuel_kg * 3160.0, delta=1.0)


class AppendixBValidation(unittest.TestCase):
    """A109 / PW206C, 550 SHP, twin light. FOCA Appendix B."""

    def test_full_lto(self):
        s = make_strategy(
            category="TWIN_TURBOSHAFT_LIGHT",
            max_shp_per_engine=550,
            number_of_engines=2,
        )
        r = compute_lto(s)
        self.assertAlmostEqual(r.fuel_kg,   36.5, delta=36.5 * 0.05)
        self.assertAlmostEqual(r.nox_g,    166.8, delta=166.8 * 0.05)
        self.assertAlmostEqual(r.hc_g,     823.7, delta=823.7 * 0.05)
        self.assertAlmostEqual(r.co_g,    1074.0, delta=1074.0 * 0.05)
        self.assertAlmostEqual(r.pm_g,       5.9, delta=5.9 * 0.10)
        self.assertAlmostEqual(r.co2_g, r.fuel_kg * 3160.0, delta=1.0)


class AppendixCValidation(unittest.TestCase):
    """AS332 / MAKILA 1A1, 1820 SHP, twin heavy.

    Against Appendix C LEFT column (CRUISE and LTO MEAN), which uses
    Table 4 power settings. See PDF: two side-by-side total tables.
    """

    def test_full_lto(self):
        s = make_strategy(
            category="TWIN_TURBOSHAFT_HEAVY",
            max_shp_per_engine=1820,
            number_of_engines=2,
        )
        r = compute_lto(s)
        self.assertAlmostEqual(r.fuel_kg,  78.4, delta=78.4 * 0.02)
        self.assertAlmostEqual(r.nox_g,   663.6, delta=663.6 * 0.02)
        self.assertAlmostEqual(r.hc_g,    541.9, delta=541.9 * 0.02)
        self.assertAlmostEqual(r.co_g,    685.1, delta=685.1 * 0.03)
        self.assertAlmostEqual(r.co2_g, r.fuel_kg * 3160.0, delta=1.0)


class PistonFuelFlowValidation(unittest.TestCase):
    """Piston FF polynomial sanity at SHP=300 per Appendix E plot."""

    def test_ff_at_300(self):
        self.assertAlmostEqual(F.piston_fuel_flow_kg_s(300), 0.030, delta=0.003)


class TurboshaftBreakpointContinuity(unittest.TestCase):
    """FF polynomials should not jump wildly at 600 and 1000 SHP boundaries."""

    def test_600_boundary(self):
        ff_low  = F.turboshaft_fuel_flow_kg_s(max_shp=600,  mode_shp=600)
        ff_high = F.turboshaft_fuel_flow_kg_s(max_shp=601,  mode_shp=600)
        self.assertAlmostEqual(ff_high, ff_low, delta=ff_low * 0.15)

    def test_1000_boundary(self):
        ff_low  = F.turboshaft_fuel_flow_kg_s(max_shp=1000, mode_shp=1000)
        ff_high = F.turboshaft_fuel_flow_kg_s(max_shp=1001, mode_shp=1000)
        self.assertAlmostEqual(ff_high, ff_low, delta=ff_low * 0.15)


class NegativeTests(unittest.TestCase):
    """Invalid inputs should raise."""

    def test_piston_nox_non_tabulated_power(self):
        with self.assertRaises(KeyError):
            F.piston_ei_nox_g_kg(0.55)

    def test_piston_pm_non_tabulated_power(self):
        with self.assertRaises(KeyError):
            F.piston_ei_pm_g_kg(0.10)

    def test_turboshaft_particle_size_bad_category(self):
        with self.assertRaises(ValueError):
            F.turboshaft_mean_particle_size_nm("INVALID", 0.65)

    def test_derive_category_twin_no_mtom(self):
        with self.assertRaises(ValueError):
            derive_category("TURBOSHAFT", 2, None)

    def test_derive_category_unknown_engine_type(self):
        with self.assertRaises(ValueError):
            derive_category("ROCKET", 1, None)

    def test_strategy_zero_shp(self):
        with self.assertRaises(ValueError):
            make_strategy(
                category="PISTON",
                max_shp_per_engine=0,
                number_of_engines=1,
            )

    def test_strategy_zero_engines(self):
        with self.assertRaises(ValueError):
            make_strategy(
                category="PISTON",
                max_shp_per_engine=131,
                number_of_engines=0,
            )


class GiSplitConsistency(unittest.TestCase):
    """dep half + arr half = full LTO."""

    def test_fuel_matches(self):
        self.assertAlmostEqual(
            GI_DEPARTURE_FRACTION + GI_ARRIVAL_FRACTION, 1.0, places=9,
        )

    def test_split_sums_to_whole(self):
        # Not an assertion about the code — just a sanity check of the constants
        full_gi_time = PROFILES["SINGLE_TURBOSHAFT"].gi_time_min
        dep_t = full_gi_time * GI_DEPARTURE_FRACTION
        arr_t = full_gi_time * GI_ARRIVAL_FRACTION
        self.assertAlmostEqual(dep_t + arr_t, full_gi_time, places=9)


class EngineCountScaling(unittest.TestCase):
    """n_engines multiplier applied correctly."""

    def test_twin_equals_twice_single(self):
        one = compute_lto(make_strategy(
            category="TWIN_TURBOSHAFT_LIGHT",
            max_shp_per_engine=550, number_of_engines=1,
        ))
        two = compute_lto(make_strategy(
            category="TWIN_TURBOSHAFT_LIGHT",
            max_shp_per_engine=550, number_of_engines=2,
        ))
        for field in ("fuel_kg", "nox_g", "hc_g", "co_g", "pm_g", "co2_g"):
            self.assertAlmostEqual(
                getattr(two, field), 2 * getattr(one, field), places=9,
            )


class DeriveCategoryLogic(unittest.TestCase):
    def test_piston(self):
        self.assertEqual(derive_category("PISTON", 1, None), "PISTON")
        self.assertEqual(derive_category("piston", 1, None), "PISTON")

    def test_single_turboshaft(self):
        self.assertEqual(
            derive_category("TURBOSHAFT", 1, None), "SINGLE_TURBOSHAFT"
        )

    def test_twin_light(self):
        self.assertEqual(
            derive_category("TURBOSHAFT", 2, 2500), "TWIN_TURBOSHAFT_LIGHT"
        )
        self.assertEqual(
            derive_category("TURBOSHAFT", 2, 3400), "TWIN_TURBOSHAFT_LIGHT"
        )

    def test_twin_heavy(self):
        self.assertEqual(
            derive_category("TURBOSHAFT", 2, 3401), "TWIN_TURBOSHAFT_HEAVY"
        )
        self.assertEqual(
            derive_category("TURBOSHAFT", 2, 8600), "TWIN_TURBOSHAFT_HEAVY"
        )


# ===========================================================================
# CSV IO tests
# ===========================================================================

class CsvIoRoundTrip(unittest.TestCase):
    """Read an engine CSV and write LTO CSV; verify column set + values."""

    def _write_new_schema(self, path: str):
        with open(path, "w", newline="") as fp:
            w = csv.writer(fp)
            w.writerow([
                "engine_name", "helicopter_category",
                "max_shp_per_engine", "number_of_engines",
            ])
            w.writerow(["ARRIEL1D1", "SINGLE_TURBOSHAFT", 732, 1])
            w.writerow(["PW206C", "TWIN_TURBOSHAFT_LIGHT", 550, 2])
            w.writerow(["HIO-360", "PISTON", 190, 1])

    def test_new_schema(self):
        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "eng.csv")
            self._write_new_schema(in_path)
            rows = read_engines_csv(in_path)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].category, "SINGLE_TURBOSHAFT")
            self.assertEqual(rows[1].number_of_engines, 2)
            self.assertEqual(rows[2].category, "PISTON")

    def test_old_schema_requires_mtom_for_twin_in_strict_mode(self):
        """Twin turboshaft in OLD schema raises under --strict when unknown."""
        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "eng.csv")
            with open(in_path, "w", newline="") as fp:
                w = csv.writer(fp)
                w.writerow([
                    "engine_name", "engine_type",
                    "max_shp_per_engine", "number_of_engines",
                ])
                # Use a made-up engine name not in the built-in lookup
                w.writerow(["FAKE_ENGINE_X123", "TURBOSHAFT", 550, 2])

            with self.assertRaises(ValueError):
                read_engines_csv(in_path, strict=True, use_built_in_mtoms=False)

    def test_old_schema_defaults_to_light_for_twin_in_lenient_mode(self):
        """Default mode (non-strict) falls back to TWIN_TURBOSHAFT_LIGHT."""
        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "eng.csv")
            with open(in_path, "w", newline="") as fp:
                w = csv.writer(fp)
                w.writerow([
                    "engine_name", "engine_type",
                    "max_shp_per_engine", "number_of_engines",
                ])
                w.writerow(["FAKE_ENGINE_X123", "TURBOSHAFT", 550, 2])

            # Should not raise; should emit stderr warning
            import io as _io
            import contextlib
            stderr_buf = _io.StringIO()
            with contextlib.redirect_stderr(stderr_buf):
                rows = read_engines_csv(
                    in_path, strict=False, use_built_in_mtoms=False,
                )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].category, "TWIN_TURBOSHAFT_LIGHT")
            self.assertIn("WARNING", stderr_buf.getvalue())

    def test_built_in_mtom_lookup_resolves_known_engines(self):
        """With built-in lookup enabled (default), known engines get correct MTOM."""
        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "eng.csv")
            with open(in_path, "w", newline="") as fp:
                w = csv.writer(fp)
                w.writerow([
                    "engine_name", "engine_type",
                    "max_shp_per_engine", "number_of_engines",
                ])
                # PW206C is in the lookup (A109E Power, 2850 kg -> LIGHT)
                w.writerow(["PW206C", "TURBOSHAFT", 550, 2])
                # MAKILA 1A1 is in the lookup (AS332L1, 8600 kg -> HEAVY)
                w.writerow(["MAKILA 1A1", "TURBOSHAFT", 1820, 2])

            rows = read_engines_csv(in_path, use_built_in_mtoms=True)
            self.assertEqual(len(rows), 2)
            # PW206C -> 2850 kg -> LIGHT
            self.assertEqual(rows[0].mtom_kg, 2850.0)
            self.assertEqual(rows[0].category, "TWIN_TURBOSHAFT_LIGHT")
            # MAKILA 1A1 -> 8600 kg -> HEAVY
            self.assertEqual(rows[1].mtom_kg, 8600.0)
            self.assertEqual(rows[1].category, "TWIN_TURBOSHAFT_HEAVY")

    def test_lto_output_csv(self):
        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "eng.csv")
            out_path = os.path.join(td, "lto.csv")
            self._write_new_schema(in_path)
            rows = read_engines_csv(in_path)
            out_rows = []
            for r in rows:
                s = make_strategy(
                    category=r.category,
                    max_shp_per_engine=r.max_shp_per_engine,
                    number_of_engines=r.number_of_engines,
                )
                out_rows.append((r, lto_to_dict(compute_lto(s))))
            write_lto_csv(out_path, out_rows)
            # Read back and check columns + a sample value
            with open(out_path, newline="") as fp:
                reader = csv.DictReader(fp)
                rows_read = list(reader)
            self.assertEqual(len(rows_read), 3)
            self.assertIn("lto_fuel_kg", reader.fieldnames)
            self.assertIn("gi_fuel_kg", reader.fieldnames)
            self.assertIn("to_fuel_kg", reader.fieldnames)
            self.assertIn("ap_fuel_kg", reader.fieldnames)
            # AS350 first row: fuel should be ~25 kg
            fuel = float(rows_read[0]["lto_fuel_kg"])
            self.assertAlmostEqual(fuel, 25.0, delta=1.0)


# ===========================================================================
# Trajectory tests
# ===========================================================================

class DepartureTrajectoryTests(unittest.TestCase):
    def test_single_turboshaft_shape(self):
        """AS350B2-style departure: GI→HOV→CL→CR, reach 3000 ft."""
        pts = build_departure("SINGLE_TURBOSHAFT")
        self.assertGreaterEqual(len(pts), 4)
        # First points are at origin at 0 altitude
        self.assertEqual(pts[0].x_m, 0.0)
        self.assertEqual(pts[0].z_m, 0.0)
        # Must reach the LTO ceiling (914.4 m) at some point
        max_z = max(p.z_m for p in pts)
        self.assertAlmostEqual(max_z, 914.4, delta=1.0)
        # Last point: time should equal GI_dep + hover + TO time
        # = 4*60 + 18 + 3*60 = 438 s
        self.assertAlmostEqual(pts[-1].t_s, 4*60 + 18 + 3*60, delta=0.1)

    def test_all_categories_build(self):
        """All four categories build departures without error."""
        for cat in ("PISTON", "SINGLE_TURBOSHAFT",
                    "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY"):
            pts = build_departure(cat)
            self.assertGreater(len(pts), 0)
            # Max altitude should be at or below LTO ceiling
            max_z = max(p.z_m for p in pts)
            self.assertLessEqual(max_z, 914.4 + 1e-6)


class ArrivalTrajectoryTests(unittest.TestCase):
    def test_single_turboshaft_shape(self):
        """Arrival: starts at ceiling, ends at origin."""
        pts = build_arrival("SINGLE_TURBOSHAFT")
        self.assertGreaterEqual(len(pts), 4)
        # First point at LTO ceiling
        self.assertAlmostEqual(pts[0].z_m, 914.4, delta=1.0)
        # Last point at origin, z=0
        self.assertEqual(pts[-1].x_m, 0.0)
        self.assertEqual(pts[-1].z_m, 0.0)
        # Total time: AP + hover + GI_arr = 5.5*60 + 18 + 60 = 408 s
        self.assertAlmostEqual(pts[-1].t_s, 5.5*60 + 18 + 60, delta=0.1)

    def test_all_categories_build(self):
        for cat in ("PISTON", "SINGLE_TURBOSHAFT",
                    "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY"):
            pts = build_arrival(cat)
            self.assertGreater(len(pts), 0)
            # Should reach origin
            self.assertEqual(pts[-1].x_m, 0.0)
            self.assertEqual(pts[-1].z_m, 0.0)

    def test_total_time_matches_profile(self):
        """Trajectory time should match AP + hover + GI_arr exactly."""
        for cat in ("PISTON", "SINGLE_TURBOSHAFT",
                    "TWIN_TURBOSHAFT_LIGHT", "TWIN_TURBOSHAFT_HEAVY"):
            pts = build_arrival(cat)
            profile = PROFILES[cat]
            expected_t = (
                profile.ap_time_min * 60 + 18
                + profile.gi_time_min * 60 * GI_ARRIVAL_FRACTION
            )
            self.assertAlmostEqual(pts[-1].t_s, expected_t, delta=0.5)


class TransformTests(unittest.TestCase):
    def test_identity_transform(self):
        """Zero origin, zero heading should leave points unchanged in x+z.

        Note: rotation logic treats +y input as a lateral component.
        With all y=0 in source trajectories, identity transform at
        heading=0 means new_y = x, new_x = y = 0. This is because
        heading 0 = north, and the source +x axis is along-track.
        We verify the logical behavior rather than literal identity.
        """
        pts = build_departure("SINGLE_TURBOSHAFT")
        trans = translate_and_rotate(pts, 0, 0, heading_deg=0)
        # Total geographic extent should be preserved (geometric invariant)
        original_max_dist = max(
            (p.x_m**2 + p.y_m**2)**0.5 for p in pts
        )
        new_max_dist = max(
            (p.x_m**2 + p.y_m**2)**0.5 for p in trans
        )
        self.assertAlmostEqual(original_max_dist, new_max_dist, delta=0.01)

    def test_translation(self):
        """Translation adds origin offset to all points."""
        pts = build_departure("PISTON")
        trans = translate_and_rotate(pts, 1000, 2000, heading_deg=0)
        # Every transformed point should be offset relative to origin
        for orig, t in zip(pts, trans):
            # At heading=0: new_x = sin(0)*x + cos(0)*y + 1000 = y + 1000
            # new_y = cos(0)*x - sin(0)*y + 2000 = x + 2000
            self.assertAlmostEqual(t.x_m - orig.y_m, 1000, delta=0.01)
            self.assertAlmostEqual(t.y_m - orig.x_m, 2000, delta=0.01)

    def test_rotation_90_degrees(self):
        """Heading 90 (east) means +x local maps to +x world (east)."""
        pts = [
            # Use simple test points instead of a full trajectory
        ]
        from foca_heli import TrajectoryPoint
        pts = [
            TrajectoryPoint(0.0, 0.0, 0.0, 0.0, "X", 0.0),
            TrajectoryPoint(100.0, 0.0, 0.0, 0.0, "X", 1.0),
        ]
        trans = translate_and_rotate(pts, 0, 0, heading_deg=90)
        # At heading 90: cos(90)=0, sin(90)=1
        # new_x = sin(90)*100 + cos(90)*0 + 0 = 100
        # new_y = cos(90)*100 - sin(90)*0 + 0 = 0
        self.assertAlmostEqual(trans[1].x_m, 100.0, delta=0.01)
        self.assertAlmostEqual(trans[1].y_m, 0.0, delta=0.01)


class WktExportTests(unittest.TestCase):
    def test_wkt_z_format(self):
        pts = build_departure("SINGLE_TURBOSHAFT")
        wkt = to_wkt_linestring_z(pts)
        self.assertTrue(wkt.startswith("LINESTRING Z ("))
        self.assertTrue(wkt.endswith(")"))
        # Contains the expected number of coordinate triples
        coord_segment = wkt[len("LINESTRING Z ("):-1]
        coords = coord_segment.split(", ")
        self.assertEqual(len(coords), len(pts))


class GeoJsonExportTests(unittest.TestCase):
    def test_feature_shape(self):
        pts = build_departure("PISTON")
        feat = to_geojson_feature(pts, properties={"category": "PISTON"})
        self.assertEqual(feat["type"], "Feature")
        self.assertEqual(feat["geometry"]["type"], "LineString")
        coords = feat["geometry"]["coordinates"]
        self.assertEqual(len(coords), len(pts))
        self.assertEqual(len(coords[0]), 3)  # x, y, z
        self.assertEqual(feat["properties"]["category"], "PISTON")

    def test_feature_serializable(self):
        """GeoJSON feature must be JSON-serializable."""
        pts = build_departure("TWIN_TURBOSHAFT_HEAVY")
        feat = to_geojson_feature(pts)
        s = json.dumps(feat)
        self.assertIn("LineString", s)


class TrajectoryParamsTests(unittest.TestCase):
    """All four categories have sensible parameter values."""

    def test_all_positive(self):
        for cat, params in TRAJECTORY_PARAMS.items():
            self.assertGreater(params.climb_roc_fpm, 0, f"{cat} climb_roc")
            self.assertGreater(params.climb_tas_kt, 0, f"{cat} climb_tas")
            self.assertGreater(params.cruise_tas_kt, 0, f"{cat} cruise_tas")
            self.assertGreater(
                params.approach_tas_initial_kt, 0, f"{cat} ap_tas_init"
            )
            self.assertGreater(
                params.approach_rod_initial_fpm, 0, f"{cat} ap_rod_init"
            )
            self.assertGreater(
                params.approach_start_nm, 0, f"{cat} ap_start_nm"
            )

    def test_heavier_categories_faster(self):
        """Heavier categories should have higher cruise TAS."""
        p = TRAJECTORY_PARAMS["PISTON"]
        s = TRAJECTORY_PARAMS["SINGLE_TURBOSHAFT"]
        tl = TRAJECTORY_PARAMS["TWIN_TURBOSHAFT_LIGHT"]
        self.assertLess(p.cruise_tas_kt, s.cruise_tas_kt)
        self.assertLess(s.cruise_tas_kt, tl.cruise_tas_kt)


class ReferenceCsvSyncTests(unittest.TestCase):
    """Verify reference_data/ CSVs are in sync with Python source of truth.

    These CSVs are generated by tools/dump_reference_data.py and documented
    as OUTPUTS not INPUTS. The library never reads them. But if they drift
    out of sync with the Python source, the documentation becomes misleading,
    so this test flags it.
    """

    def _ref_path(self, name):
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(here, "..", "reference_data", name)

    def test_operational_profiles_match(self):
        """CSV operational profiles must match PROFILES dict."""
        from foca_heli import PROFILES
        path = self._ref_path("operational_profiles.csv")
        if not os.path.exists(path):
            self.skipTest("reference_data/ not present; run dump_reference_data.py")
        with open(path, newline="") as fp:
            rows = list(csv.DictReader(fp))
        self.assertEqual(len(rows), len(PROFILES))
        for row in rows:
            cat = row["helicopter_category"]
            self.assertIn(cat, PROFILES)
            p = PROFILES[cat]
            self.assertAlmostEqual(float(row["gi_time_min"]), p.gi_time_min)
            self.assertAlmostEqual(float(row["to_time_min"]), p.to_time_min)
            self.assertAlmostEqual(float(row["ap_time_min"]), p.ap_time_min)
            self.assertAlmostEqual(float(row["gi_power_fraction"]), p.gi_power)
            self.assertAlmostEqual(float(row["to_power_fraction"]), p.to_power)
            self.assertAlmostEqual(float(row["ap_power_fraction"]), p.ap_power)
            self.assertAlmostEqual(float(row["mean_power_fraction"]), p.mean_power)

    def test_trajectory_params_match(self):
        """CSV trajectory params must match TRAJECTORY_PARAMS dict."""
        from foca_heli import TRAJECTORY_PARAMS
        path = self._ref_path("trajectory_params.csv")
        if not os.path.exists(path):
            self.skipTest("reference_data/ not present; run dump_reference_data.py")
        with open(path, newline="") as fp:
            rows = list(csv.DictReader(fp))
        self.assertEqual(len(rows), len(TRAJECTORY_PARAMS))
        for row in rows:
            cat = row["helicopter_category"]
            self.assertIn(cat, TRAJECTORY_PARAMS)
            p = TRAJECTORY_PARAMS[cat]
            self.assertAlmostEqual(float(row["climb_roc_fpm"]), p.climb_roc_fpm)
            self.assertAlmostEqual(float(row["cruise_tas_kt"]), p.cruise_tas_kt)

    def test_airframe_mtoms_match(self):
        """CSV airframe MTOMs must match the baked-in dict."""
        from foca_heli import built_in_mtom_dict
        path = self._ref_path("airframe_mtoms.csv")
        if not os.path.exists(path):
            self.skipTest("reference_data/ not present; run dump_reference_data.py")
        with open(path, newline="") as fp:
            rows = list(csv.DictReader(fp))
        built_in = built_in_mtom_dict()
        self.assertEqual(len(rows), len(built_in))
        for row in rows:
            name = row["engine_name"]
            self.assertIn(name, built_in)
            self.assertAlmostEqual(float(row["mtow"]), built_in[name])


if __name__ == "__main__":
    unittest.main(verbosity=2)
