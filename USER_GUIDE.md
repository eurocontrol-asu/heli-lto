# User Guide — foca_heli

A practical guide for using `foca_heli` to compute helicopter emissions and
trajectories per FOCA 2015 guidance.

Version: 0.1.0

---

## Table of contents

1. What this package does
2. What this package does not do
3. Installation
4. Quick start — your first LTO calculation
5. Conceptual background
   - The LTO cycle
   - FOCA helicopter categories
   - What the package computes
6. Command-line reference
7. Library reference
8. Input CSV formats
9. Output formats
10. Worked examples
    - Example A: single helicopter from manual parameters
    - Example B: bulk processing a fleet CSV
    - Example C: airport-placed trajectories for GIS
11. Validation against FOCA 2015
12. Known FOCA PDF inconsistencies
13. Troubleshooting
14. FAQ
15. Contributing

---

## 1. What this package does

`foca_heli` implements the FOCA 2015 helicopter emissions guidance as a
standalone Python library and command-line tool. Given an engine
(identified by max shaft power and number of engines) plus a helicopter
category, it computes:

- **LTO fuel burn** in kilograms per cycle
- **Emissions** of NOx, HC, CO, PM (mass in grams), and CO2 (in grams)
- **Per-mode breakdown** across ground-idle (GI), take-off (TO), and
  approach (AP) phases. The full ground-idle time is treated as a single
  GI mode for emissions purposes; the 80/20 split between
  before-takeoff and after-landing only affects trajectory time-on-ground.
- **LTO trajectories** — 3D flight paths representing the departure and
  arrival profile, exportable as WKT LINESTRING Z or GeoJSON

Reference: Rindlisbacher T., Chabbey L., *"Guidance on the Determination
of Helicopter Emissions"*, Swiss Federal Office of Civil Aviation,
Edition 2, December 2015.

## 2. What this package does not do

To set expectations clearly:

- **No dispersion modelling.** The package produces emission quantities
  and trajectory geometries. It does not run atmospheric dispersion. For
  dispersion use a downstream tool such as AUSTAL2000 or equivalent.
- **No airport layout modelling.** Trajectories are produced in a local
  frame around the helipad; you translate and rotate them to your
  airport's runway or helipad coordinates.
- **No helicopter performance simulation.** Trajectory phase durations
  and power settings come from FOCA Tables 1-4, not from per-airframe
  performance data.
- **No fixed-wing aircraft support.** This is a helicopter-only package.
  For fixed-wing LTO emissions, use tools based on the ICAO Engine
  Emissions Databank.
- **No ground support equipment (GSE), APU, or de-icing emissions.**
  Aircraft engine emissions only.
- **No fuel-flow correction for ambient conditions.** FOCA 2015 does not
  specify an ambient correction for helicopter engines; values are
  treated as ISA sea level. If you need corrections, apply them
  downstream.

## 3. Installation

Requirements: Python 3.10 or newer. No third-party dependencies — pure
standard library.

Install from source:

```
git clone https://github.com/eurocontrol-asu/heli-lto.git
cd foca-heli
pip install -e .
```

Or, once the package is published on PyPI:

```
pip install foca-heli
```

Verify the installation:

```
foca-heli single --category PISTON --max-shp 190 --engines 1
```

You should see a table of emissions for a 190-SHP piston helicopter
broken down by mode.

## 4. Quick start — your first LTO calculation

Suppose you want to know the LTO fuel burn for a Robinson R22 (piston,
single 190-SHP Lycoming O-360).

### From the command line

```
foca-heli single --category PISTON --max-shp 190 --engines 1
```

Output:

```
MODE   POW    TIME   FF/eng    FUEL    NOX     HC      CO        PM     CO2(g)
GI     20%    300    0.00784   2.35    2.35    52.71   2353.36   0.118  7295
TO     95%    240    0.01783   4.28    4.28    55.54   4278.46   0.428  13263
AP     60%    330    0.01278   4.22    16.87   64.29   4216.85   0.169  13072
TOTAL                          10.85   23.50   172.54  10848.67  0.714  33631
```

Units: FF is kg/s per engine; FUEL is kg; gaseous and PM emissions are
in grams; CO2 in grams. The TOTAL row shows LTO totals across all three
modes.

### From Python

```python
from foca_heli import make_strategy, compute_lto

strategy = make_strategy(
    category="PISTON",
    max_shp_per_engine=190,
    number_of_engines=1,
)
result = compute_lto(strategy)

print(f"LTO fuel: {result.fuel_kg:.2f} kg")
print(f"LTO NOx:  {result.nox_g:.2f} g")
print(f"LTO CO:   {result.co_g:.0f} g")
```

## 5. Conceptual background

### The LTO cycle

The Landing-and-Take-Off cycle is a standardized ground-level flight
pattern used to compare aircraft emissions. FOCA 2015 defines the LTO
cycle for helicopters as the combined operations below 3000 ft (914 m)
above ground level:

- **Ground Idle (GI)** — engine running on the ground before take-off or
  after landing
- **Take-off (TO)** — full power climb from the helipad up to 3000 ft AGL
- **Approach (AP)** — descent from 3000 ft AGL to the helipad

The term "cycle" means one take-off plus one landing counted together.
When multiplying by the annual movement count, count each landing or
take-off individually (one LTO cycle = one landing + one take-off, so
divide total movements by 2 before multiplying by per-cycle values).

### FOCA helicopter categories

FOCA 2015 defines four categories with distinct power profiles and
time-in-mode values (Tables 1-4 of the guidance):

| Category | Typical example | MTOM range |
|---|---|---|
| PISTON | Robinson R22, R44 | < 1500 kg |
| SINGLE_TURBOSHAFT | AS350, Bell 206, EC130 | 2000–3000 kg |
| TWIN_TURBOSHAFT_LIGHT | Bo 105, EC135, A109 | ≤ 3400 kg MTOM |
| TWIN_TURBOSHAFT_HEAVY | AW139, S-92, Bell 412, AS332 | > 3400 kg MTOM |

The 3400 kg threshold is the boundary between LIGHT and HEAVY twin
turboshafts and materially affects emission results (typically 10-20%
difference in NOx).

### What the package computes per mode

For each of the three modes (GI, TO, AP):

1. Retrieve time-in-mode and power setting from Tables 1-4 based on
   category
2. Compute fuel flow per engine from the power setting and max SHP using
   FOCA section 3.1 (piston) or 3.2 (turboshaft) polynomials
3. Multiply by time-in-mode and number of engines to get mode fuel mass
4. Compute per-mode emission indices (EI) from lookup tables (piston) or
   polynomials (turboshaft)
5. Multiply fuel mass by EIs to get mode emissions
6. Sum across modes to get LTO totals

## 6. Command-line reference

Three subcommands: `single`, `lto`, `trajectory`.

### `foca-heli single`

Compute LTO for one engine from manual parameters. Prints a
human-readable table to stdout.

```
foca-heli single
    --category {PISTON|SINGLE_TURBOSHAFT|TWIN_TURBOSHAFT_LIGHT|TWIN_TURBOSHAFT_HEAVY}
    --max-shp <float>        shaft horsepower per engine at max rating
    --engines <int>          number of engines (1 or 2)
```

### `foca-heli lto`

Bulk process a CSV file of engines, write an LTO results CSV.

```
foca-heli lto
    --in <path>              input CSV (OLD or NEW schema, auto-detected)
    --out <path>             output CSV of LTO totals
    [--airframe <path>]      override/supplement built-in engine → MTOM lookup
    [--strict]               error on unknown twin-TS engines instead of warning
```

### `foca-heli trajectory`

Build an LTO trajectory for a given category. Output is a table, WKT
LINESTRING Z, or GeoJSON feature.

```
foca-heli trajectory
    --category <category>
    --part {dep|arr|both}    departure, arrival, or both concatenated
    --format {table|wkt|geojson}
    [--origin-x <float>]     x-coordinate of helipad in target CRS (default 0)
    [--origin-y <float>]     y-coordinate of helipad in target CRS (default 0)
    [--heading <float>]      compass heading in degrees (0=north, 90=east)
```

Z values in WKT and GeoJSON are altitudes above ground level in metres.
The CLI does not currently apply a helipad-elevation offset; if you need
absolute MSL altitudes, post-process the output by adding the helipad
elevation to each Z value, or use the library's
`translate_and_rotate(...)` and add an offset programmatically.

## 7. Library reference

Public functions, organized by purpose.

### Building an LTO strategy

```python
from foca_heli import make_strategy

strategy = make_strategy(
    category="TWIN_TURBOSHAFT_HEAVY",
    max_shp_per_engine=1820,
    number_of_engines=2,
)
```

### Computing LTO totals

```python
from foca_heli import compute_lto, lto_to_dict

result = compute_lto(strategy)

# Access totals (units: fuel in kg, gaseous and PM in g, CO2 in g)
result.fuel_kg
result.nox_g
result.hc_g
result.co_g
result.pm_g
result.co2_g

# Access per-mode breakdown — three modes: GI, TO, AP
for mode in result.modes:
    print(mode.mode, mode.power_fraction, mode.time_s,
          mode.fuel_kg, mode.nox_g, mode.co2_g)

# Convert to flat dict for CSV / JSON serialization
as_dict = lto_to_dict(result)
```

Note: per-mode particle number (PM count) is computed internally but
not currently aggregated to the `LtoResult` level. Only PM mass
(`pm_g`) is aggregated. If you need PM number per LTO cycle, sum the
per-engine `pm_number_per_kg × fuel_kg` contributions yourself by
calling the strategy's `compute_mode` method directly.

### Reading/writing CSVs

```python
from foca_heli import read_engines_csv, write_lto_csv, compute_lto, make_strategy

rows = read_engines_csv("engines.csv")
results = []
for row in rows:
    strategy = make_strategy(
        category=row.category,
        max_shp_per_engine=row.max_shp_per_engine,
        number_of_engines=row.number_of_engines,
    )
    result = compute_lto(strategy)
    results.append((row, result))

write_lto_csv("output.csv", results)
```

### Building trajectories

```python
from foca_heli import build_departure, build_arrival, to_wkt_linestring_z, to_geojson_feature

# Local frame: helipad at origin, departure heads toward +x
departure = build_departure("TWIN_TURBOSHAFT_HEAVY")
arrival = build_arrival("TWIN_TURBOSHAFT_HEAVY")

# Access points (attributes are x_m, y_m, z_m for explicit metric units)
for pt in departure:
    print(pt.x_m, pt.y_m, pt.z_m, pt.tas_m_s, pt.mode, pt.t_s)
    # pt.mode is one of "GI", "GR", "HOV", "CL", "CR", "DESC", "FINAL", "TOUCH"

# Export
wkt = to_wkt_linestring_z(departure)
geojson = to_geojson_feature(departure, properties={"phase": "departure"})
```

### Transforming to airport coordinates

```python
from foca_heli import translate_and_rotate

# Place trajectory at helipad (x=500000, y=5000000) with runway heading 270°
placed = translate_and_rotate(
    departure,
    origin_x=500000.0,
    origin_y=5000000.0,
    heading_deg=270.0,
)
wkt = to_wkt_linestring_z(placed)
```

### Airframe MTOM lookup

```python
from foca_heli import lookup_airframe, lookup_mtom_kg, BUILT_IN_AIRFRAME_MTOMS

# Look up MTOM for a known engine
mtom = lookup_mtom_kg("MAKILA 1A1")  # -> 8600.0

# Get full mapping record with citation
mapping = lookup_airframe("MAKILA 1A1")
print(mapping.representative_airframe)  # "Eurocopter AS332L1 Super Puma"
print(mapping.source)                   # citation string

# Iterate over all known mappings
for key, mapping in BUILT_IN_AIRFRAME_MTOMS.items():
    print(key, mapping.mtom_kg, mapping.expected_category)
```

## 8. Input CSV formats

The CSV reader auto-detects two schemas.

### Schema A — NEW (preferred)

Category is explicit, no MTOM lookup needed.

```csv
engine_name,helicopter_category,max_shp_per_engine,number_of_engines
ARRIEL 1D1,SINGLE_TURBOSHAFT,732,1
MAKILA 1A1,TWIN_TURBOSHAFT_HEAVY,1820,2
PW206C,TWIN_TURBOSHAFT_LIGHT,550,2
HIO-360,PISTON,190,1
```

Required columns: `engine_name`, `helicopter_category`, `max_shp_per_engine`,
`number_of_engines`.

Allowed `helicopter_category` values: `PISTON`, `SINGLE_TURBOSHAFT`,
`TWIN_TURBOSHAFT_LIGHT`, `TWIN_TURBOSHAFT_HEAVY`.

### Schema B — OLD (legacy plugin format)

Category is derived from engine type + engine count + MTOM lookup.

```csv
engine_name,engine_type,max_shp_per_engine,number_of_engines
ARRIEL 1D1,TURBOSHAFT,732,1
MAKILA 1A1,TURBOSHAFT,1820,2
HIO-360,PISTON,190,1
```

Required columns: `engine_name`, `engine_type`, `max_shp_per_engine`,
`number_of_engines`.

Derivation rules:

- `PISTON` → PISTON regardless of engine count
- `TURBOSHAFT` and 1 engine → SINGLE_TURBOSHAFT
- `TURBOSHAFT` and ≥2 engines → TWIN_TURBOSHAFT_LIGHT or _HEAVY based on
  MTOM (threshold 3400 kg, ≤ threshold is LIGHT)

For twin-turboshaft rows, MTOM comes from:

1. An optional `--airframe` CSV you pass (columns `engine_name,mtow`)
2. The built-in lookup table in `foca_heli/airframe_mtoms.py` (36 twin-TS
   engines covered, see `AIRFRAME_MTOM_SOURCES.md`)
3. Default fallback to `TWIN_TURBOSHAFT_LIGHT` with a stderr warning

Use `--strict` to error instead of falling back.

### Preparing your own engine CSV

Typical workflow if you're starting from airport movement data:

1. Extract aircraft types and their counts from your movements file
2. For each aircraft type, look up the typical engine model and SHP
   (manufacturer brochures, EASA TCDS, Wikipedia specifications)
3. Enter one row per unique engine; the library processes each row
   independently. The library does not perform fleet-mix weighting — you
   do that downstream by multiplying LTO per-cycle results by your
   movement counts.

Fleet-mix weighting example:

```
Airport X had 1200 helicopter movements last year.
- 400 were AS350 (Arriel 1D1, single turboshaft, 732 SHP)
- 500 were A109 (PW206C, twin turboshaft light, 550 SHP × 2)
- 300 were AW139 (PT6C-67C, twin turboshaft heavy, 1100 SHP × 2)

One LTO cycle = one landing + one take-off = 2 movements.
So the airport had 1200 / 2 = 600 LTO cycles.

Weighted annual fuel burn = (400/2) × fuel_AS350
                          + (500/2) × fuel_A109
                          + (300/2) × fuel_AW139
```

The package gives you the per-cycle values; multiplication is yours.

## 9. Output formats

### LTO results CSV

Columns produced by `foca-heli lto` (always include both totals and
per-mode breakdown):

```
engine_name, helicopter_category, max_shp_per_engine, number_of_engines,

# LTO totals
lto_fuel_kg, lto_nox_g, lto_hc_g, lto_co_g, lto_pm_g, lto_co2_g,

# Per-mode (one block per mode: GI, TO, AP)
gi_power_fraction, gi_time_s, gi_fuel_flow_kg_s_per_engine,
gi_fuel_kg, gi_nox_g, gi_hc_g, gi_co_g, gi_pm_g, gi_co2_g,

to_power_fraction, to_time_s, to_fuel_flow_kg_s_per_engine,
to_fuel_kg, to_nox_g, to_hc_g, to_co_g, to_pm_g, to_co2_g,

ap_power_fraction, ap_time_s, ap_fuel_flow_kg_s_per_engine,
ap_fuel_kg, ap_nox_g, ap_hc_g, ap_co_g, ap_pm_g, ap_co2_g
```

All emissions are in grams, fuel in kg, fuel flow in kg/s, time in
seconds. Power fraction is dimensionless (0 to 1).

### Trajectory WKT

`LINESTRING Z (x1 y1 z1, x2 y2 z2, ...)`

- 2D variant: `LINESTRING (x1 y1, x2 y2, ...)`
- Coordinates in metres in the local helipad frame unless transformed
- Z is altitude above helipad in metres (no MSL offset applied)

Use WKT when importing to PostGIS, QGIS, or any OGC-compliant GIS.

### Trajectory GeoJSON

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[x1, y1, z1], [x2, y2, z2], ...]
  },
  "properties": {
    "category": "TWIN_TURBOSHAFT_HEAVY",
    "phase": "departure",
    "mode_segments": ["TO", "TO", ...]
  }
}
```

GeoJSON is the recommended format for web-based or Leaflet/Mapbox
visualizations.

## 10. Worked examples

### Example A: single helicopter from manual parameters

Compute LTO for an AgustaWestland AW139 (twin turboshaft heavy, two
PT6C-67C engines at 1531 SHP each).

```
foca-heli single --category TWIN_TURBOSHAFT_HEAVY --max-shp 1531 --engines 2
```

Expected output (totals row):

```
TOTAL    70.9    538.4    592.5    752.5    16.0    224049
```

Columns: fuel (kg), NOx (g), HC (g), CO (g), PM (g), CO2 (g).
Fuel ≈ 71 kg per LTO cycle. For 500 LTO cycles/year that's ~35 tonnes
fuel and ~270 kg NOx.

### Example B: bulk processing a fleet CSV

Create `fleet.csv`:

```csv
engine_name,helicopter_category,max_shp_per_engine,number_of_engines
Lycoming O-360,PISTON,180,1
Arriel 1D1,SINGLE_TURBOSHAFT,732,1
PW206C,TWIN_TURBOSHAFT_LIGHT,550,2
Arriel 2C,TWIN_TURBOSHAFT_HEAVY,839,2
PT6C-67C,TWIN_TURBOSHAFT_HEAVY,1531,2
```

Run:

```
foca-heli lto --in fleet.csv --out fleet_lto.csv
```

`fleet_lto.csv` will have one row per engine with total fuel and
emissions. Multiply by your movement counts to get annual totals.

### Example C: airport-placed trajectories for GIS

Your helipad is at UTM 31N coordinates (X=500000, Y=5000000) and the
approach is from the west (inbound heading 090°, outbound 270°).

Build and export the departure trajectory for an AW139:

```
foca-heli trajectory \
    --category TWIN_TURBOSHAFT_HEAVY \
    --part dep \
    --format geojson \
    --origin-x 500000 \
    --origin-y 5000000 \
    --heading 270 \
    > dep.geojson
```

Then the arrival:

```
foca-heli trajectory \
    --category TWIN_TURBOSHAFT_HEAVY \
    --part arr \
    --format geojson \
    --origin-x 500000 \
    --origin-y 5000000 \
    --heading 90 \
    > arr.geojson
```

Load both files into QGIS via Layer → Add Layer → Add Vector Layer.
They'll draw as 3D linestrings you can style by altitude.

## 11. Validation against FOCA 2015

The package is validated against the three worked examples in FOCA
2015's appendices:

| Appendix | Helicopter | Engine | SHP | FOCA fuel | Computed | Delta |
|---|---|---|---:|---:|---:|---:|
| A | AS350B2 | Arriel 1D1 | 732 | 24.7 kg | 25.22 kg | +2.1% |
| B | A109E Power | PW206C | 550 | 36.5 kg | 37.33 kg | +2.3% |
| C | AS332 Super Puma | MAKILA 1A1 | 1820 | 78.4 kg | 77.6 kg | −1.0% |

Per-mode emission indices (NOx, HC, CO, PM) are also within FOCA's
stated formula tolerances. 41 unit tests exercise the formulas,
category derivation, CSV round-trips, and reference data consistency.

Run the tests yourself:

```
python -m tests.test_all
```

## 12. Known FOCA PDF inconsistencies

The FOCA 2015 PDF contains three internal inconsistencies. This package
resolves each explicitly and documents the resolution.

### 12.1 Piston fuel-flow leading coefficient

Section 3.1 body text specifies a leading coefficient of `19e-12`.
Appendix E's fuel-flow plot for piston engines is drawn using
`1.9e-12`. Evaluating both at SHP=300 shows only the `1.9e-12` value
reproduces the plot, suggesting the body text contains a digit-loss
typo.

**Package behaviour:** uses `1.9e-12`.

### 12.2 Appendix C twin-heavy power settings

Table 4 in section 2.4 (the 2015 update) prescribes power settings of
6% (GI), 66% (AP), and 32% (TO) for twin turboshaft heavy helicopters.
Appendix C's MODEL column lists legacy values of 7%/75%/35% from an
earlier edition.

**Package behaviour:** uses Table 4 (6%/66%/32%). Validation against
Appendix C compares to its LEFT (MEAN) column which matches the
Table 4 values within 1%.

### 12.3 Appendix C PM values

Appendix C's tabulated PM mass values are 3-4× lower than what FOCA's
section 3.2 formula predicts at the relevant power settings. The
formula values match Appendix B exactly and match the PM plot in
Appendix F exactly, confirming that the formula is correct and
Appendix C's PM column has a typographical error.

**Package behaviour:** uses the formula.

## 13. Troubleshooting

### "Twin turboshaft row has no MTOM"

Your CSV is in OLD schema and contains a twin-turboshaft engine not in
the built-in lookup. Resolutions:

- **Preferred:** switch to NEW schema with explicit
  `helicopter_category` column.
- **Alternative:** supply `--airframe my_airframes.csv` with columns
  `engine_name,mtow` for the missing engines.
- **Quick fix:** accept the default `TWIN_TURBOSHAFT_LIGHT` fallback
  (warning only, no error). Only valid for engines you know are on
  LIGHT airframes.
- **Strict:** pass `--strict` to force an error instead of falling
  back. Useful in CI pipelines where silent fallbacks are unacceptable.

### Computed fuel doesn't match a helicopter spec sheet

Spec sheets often quote fuel for hover or climb, not LTO. A typical
LTO fuel is 15-30 minutes of operation at a mix of power settings, not
full take-off power. Compare against FOCA Appendix A/B/C if you want
a ground-truth LTO figure.

### The trajectory LINESTRING crosses the helipad

Expected: the departure starts at the helipad (origin), climbs away on
+x axis until 3000 ft AGL. The arrival descends from 3000 ft AGL to
the helipad. With `--part both`, the two are concatenated
departure→arrival with a midpoint at the helipad.

### CO2 looks implausibly low/high

CO2 = 3160 × fuel_kg (Jet-A factor for turboshaft, in grams) or
CO2 = 3100 × fuel_kg (AvGas factor for piston, in grams), by
construction (FOCA standard factors). If the fuel number is correct
then CO2 is correct. If CO2 is wrong, check the fuel.

### Category classifier picks LIGHT when you expect HEAVY

The 3400 kg threshold is exclusive on the LIGHT side: MTOM = 3400 kg
yields LIGHT. If your helicopter is exactly at 3400 kg or you have
new information that its operating MTOM is higher, use NEW schema and
specify `TWIN_TURBOSHAFT_HEAVY` explicitly.

## 14. FAQ

**Q: Why are there separate PISTON and SINGLE_TURBOSHAFT categories?**

A: FOCA 2015 uses different fuel-flow formulas (section 3.1 for piston,
section 3.2 for turboshaft) and different emission index tables.
Category is not a performance grouping; it's an input-data grouping.

**Q: Does the package handle hybrid or electric helicopters?**

A: No. FOCA 2015 predates production hybrid/electric helicopters. The
package scope is conventional piston and turboshaft helicopters with
liquid fuel.

**Q: Can I use this for fixed-wing aircraft?**

A: No. Fixed-wing LTO uses the ICAO Engine Emissions Databank with
different reference modes (idle, approach, climb, take-off in
percentages of maximum continuous thrust). This package is helicopter-
specific.

**Q: How do I cite this package?**

A: Cite the FOCA 2015 reference (Rindlisbacher & Chabbey) as the
methodological source. Optionally cite the package itself:
`foca_heli v0.1.0 (heli-lto), https://github.com/eurocontrol-asu/heli-lto`.

**Q: Is this an official Eurocontrol or FOCA tool?**

A: No. This is an independent implementation of the FOCA 2015
methodology. Neither Eurocontrol nor FOCA endorses this package.
Validation is against FOCA's own published worked examples; see
section 11.

**Q: What ambient conditions are assumed?**

A: ISA sea-level standard conditions. FOCA 2015 does not specify an
ambient correction for helicopter engines.

**Q: How do I aggregate over an airport's annual movements?**

A: Multiply per-cycle LTO values by (annual movements / 2) per engine
type, then sum. The package gives you per-engine-per-LTO; aggregation
is the user's responsibility. See section 8.

## 15. Contributing

Contributions are welcome. The project follows standard GitHub PR
workflow.

### Development setup

```
git clone https://github.com/eurocontrol-asu/heli-lto.git
cd foca-heli
pip install -e .
python -m tests.test_all   # should report 41 tests pass
```

### Before submitting a PR

- Add/update tests for any new functionality
- Run the full test suite (`python -m tests.test_all`)
- If you change emission formulas or data tables, regenerate the
  reference CSVs: `python tools/dump_reference_data.py`
- Update `CHANGELOG.md` with a line describing the change
- Ensure the EUPL-1.2 license header remains intact in `__init__.py`

### Reporting issues

Please include:

- Your Python version
- The CLI command or Python snippet that triggers the issue
- The expected behaviour vs. what actually happened
- If applicable, the input CSV (or a minimal reproducer)

### Scope policy

Accepted contribution types:

- Bug fixes with test coverage
- Performance improvements that don't change numerical results
- Additional engine → airframe MTOM mappings with citations
- Documentation improvements
- Additional worked examples

Out of scope (likely to be declined unless strongly justified):

- Adding methodologies beyond FOCA 2015 (use a separate package)
- Adding ambient corrections (FOCA 2015 doesn't specify them)
- Changing the canonical emission factors without a corresponding FOCA
  errata citation
- Adding third-party dependencies (the pure-stdlib design is deliberate)

---

## Further reading

- FOCA 2015 guidance: https://www.bazl.admin.ch (search "helicopter emissions guidance")
- ICAO CAEP materials on helicopter emissions methodology
- `AIRFRAME_MTOM_SOURCES.md` in this repo for the engine-to-airframe mapping rationale
- `reference_data/README.md` for the CSV dumps of embedded FOCA reference data
