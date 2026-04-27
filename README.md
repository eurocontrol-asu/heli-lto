# foca_heli

Standalone Python library and CLI for computing helicopter LTO emissions
and per-category trajectories per FOCA 2015 guidance.

Reference: Rindlisbacher T., Chabbey L., "Guidance on the Determination
of Helicopter Emissions", FOCA, Edition 2, December 2015. Ref:
COO.2207.111.2.2015750.

## Scope

- Full LTO mass emissions (fuel, NOx, HC, CO, PM, CO2)
  per single + twin helicopter, split by GI / TO / AP modes
- Per-category LTO trajectories (departure + arrival) with WKT and
  GeoJSON export
- Four FOCA categories: piston, single turboshaft, twin turboshaft light,
  twin turboshaft heavy
- Auto-detecting CSV reader for both the legacy plugin schema
  (`engine_type`) and the proposed new schema (`helicopter_category`)
- Built-in engine-name → airframe MTOM lookup for twin-turboshaft
  category classification (36 engine variants with citations)

**New users start here:** see `USER_GUIDE.md` for a comprehensive walkthrough
with worked examples, input/output format details, and troubleshooting.

## Installation

Pure stdlib, no dependencies. Python 3.10+ (uses `|` union types,
`dataclasses`).

Drop the `foca_heli/` package directory anywhere on `PYTHONPATH`.

## CLI usage

```
# Compute full LTO for a single engine
python -m foca_heli.cli single --category SINGLE_TURBOSHAFT --max-shp 732 --engines 1

# Bulk process a CSV of engines, write results CSV
python -m foca_heli.cli lto --in engines.csv --out lto_results.csv

# Optional override of built-in MTOM lookup
python -m foca_heli.cli lto --in engines.csv --out out.csv --airframe my_airframes.csv

# Strict mode: error on unresolved twin-TS rows instead of defaulting to LIGHT
python -m foca_heli.cli lto --in engines.csv --out out.csv --strict

# Build a trajectory (human-readable table)
python -m foca_heli.cli trajectory --category SINGLE_TURBOSHAFT --part both

# Build a GeoJSON trajectory with origin + heading
python -m foca_heli.cli trajectory --category TWIN_TURBOSHAFT_HEAVY \
    --part both --format geojson --origin-x 500000 --origin-y 5000000 --heading 270

# WKT output for GIS import
python -m foca_heli.cli trajectory --category PISTON --part dep --format wkt
```

## Library usage

```python
from foca_heli import make_strategy, compute_lto, build_departure, to_wkt_linestring_z

# LTO emissions
strategy = make_strategy(
    category="TWIN_TURBOSHAFT_HEAVY",
    max_shp_per_engine=1820,
    number_of_engines=2,
)
result = compute_lto(strategy)
print(f"Fuel: {result.fuel_kg:.1f} kg, NOx: {result.nox_g:.0f} g")
# -> Fuel: 77.6 kg, NOx: 654 g  (matches FOCA Appendix C ≈ 78.4 kg)

# Trajectory
traj = build_departure("TWIN_TURBOSHAFT_HEAVY")
wkt = to_wkt_linestring_z(traj)
```

## Input CSV schemas

Auto-detected at read time.

### OLD schema (plugin legacy)

```
engine_name,engine_type,max_shp_per_engine,number_of_engines,...
ARRIEL 1D1,TURBOSHAFT,732,1,...
MAKILA 1A1,TURBOSHAFT,1820,2,...
```

Twin-turboshaft rows require MTOM to classify LIGHT vs HEAVY. The package
ships with a built-in engine → MTOM lookup (36 twin-TS engines covered,
see `AIRFRAME_MTOM_SOURCES.md`). For unknown engines, pass
`--airframe airframes.csv` with columns `engine_name,mtow`, or use NEW
schema.

### NEW schema (preferred)

```
engine_name,helicopter_category,max_shp_per_engine,number_of_engines
ARRIEL 1D1,SINGLE_TURBOSHAFT,732,1
MAKILA 1A1,TWIN_TURBOSHAFT_HEAVY,1820,2
```

No MTOM lookup needed — category is explicit.

## Validation against FOCA 2015 appendices

| Appendix | Helicopter | Engine | SHP | Target fuel | Computed | Delta |
|---|---|---|---:|---:|---:|---:|
| A | AS350B2 | Arriel 1D1 | 732 | 24.7 kg | 25.22 kg | +2.1% |
| B | A109 | PW206C | 550 | 36.5 kg | 37.33 kg | +2.3% |
| C | AS332 | MAKILA 1A1 | 1820 | 78.4 kg | 77.6 kg | −1.0% |

Per-mode EIs (NOx, HC, CO, PM) all within FOCA's stated formula
tolerances. 38 unit tests pass.

## Package layout

```
foca_heli/
├── __init__.py                 (public API exports)
├── formulas.py                 (FOCA 2015 pure formulas, all polynomials)
├── operational_profiles.py     (Tables 1-4 + GI split + category derivation)
├── strategies.py               (PistonStrategy, TurboshaftStrategy)
├── factory.py                  (make_strategy)
├── lto.py                      (compute_lto → LtoResult dataclass)
├── trajectory.py               (per-category trajectory generator)
├── csv_io.py                   (schema-detecting CSV reader + writer)
├── airframe_mtoms.py           (engine → MTOM lookup with citations)
└── cli.py                      (argparse CLI)
tests/
└── test_all.py                 (38 tests)
AIRFRAME_MTOM_SOURCES.md        (citation document)
README.md                       (this file)
```

## Known FOCA PDF inconsistencies (handled)

1. **Piston fuel-flow coefficient.** Body text says `19e-12`; Appendix E
   plot shows `1.9e-12`. We use `1.9e-12` (matches plot; body text
   digit-loss typo). Verified at SHP=300.

2. **Appendix C twin-heavy power settings.** Table 4 (2015 update)
   prescribes 6%/66%/32% GI/AP/TO; Appendix C MODEL column shows legacy
   7%/75%/35% (2009 values). We use Table 4. Validation compares against
   Appendix C's LEFT (MEAN) column.

3. **Appendix C PM values** are 3-4x below what section 3.2's formula
   predicts. Formula matches Appendix B exactly and Appendix F plot
   exactly. We use the formula.

## License

This software is published under European Union Public Licence v. 1.2
(see `LICENSE`) with certain amendments described in the
`AMENDMENT_TO_EUPL_license.md` file, reflecting EUROCONTROL's status as
an international organisation. The license structure mirrors the
upstream `open_alaqs` project.
