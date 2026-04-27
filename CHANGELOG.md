# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Initial release

### Fixed pre-release

- **CO2 calculation**: per-mode CO2 was being multiplied by fuel-flow rate
  in addition to the kg/kg fuel-burn factor, yielding values ~3% of
  correct. Fixed in `strategies.py` so the per-mode `co2_g_kg` field
  contains the constant CO2-per-kg-fuel ratio (3160 for Jet-A, 3100 for
  AvGas) as the field name implies. Regression assertions added to all
  three appendix validation tests.

### Added

- Full LTO emissions calculation per FOCA 2015 sections 3.1 (piston) and
  3.2 (turboshaft), covering fuel, NOx, HC, CO, PM (mass + number), CO2
- Four FOCA categories: piston, single turboshaft, twin turboshaft light,
  twin turboshaft heavy
- Per-mode emission breakdown (GI, TO, AP) — full GI time treated as a
  single mode for emissions; trajectory builders separately apply the
  80% GI-before-takeoff and 20% GI-after-landing split to ground time
- Per-category LTO trajectory generator with departure + arrival phases,
  reaching the 3000 ft AGL LTO ceiling
- WKT (LINESTRING Z) and GeoJSON (LineString) trajectory export
- Origin translation + heading rotation transforms for placing
  trajectories at real airports
- Auto-detecting CSV reader supporting both legacy plugin schema
  (`engine_type`) and proposed new schema (`helicopter_category`)
- Built-in engine-name → airframe MTOM lookup covering 36 twin-turboshaft
  engine variants with cited sources for category classification
- `--strict` CLI flag to error on unknown twin turboshaft engines instead
  of defaulting to LIGHT
- CLI with three subcommands: `single`, `lto`, `trajectory`
- 41 unit tests covering formula correctness, category derivation, CSV
  round-trips, trajectory shape, and reference-data synchronization
- Reference data CSV dumps (`reference_data/`) for audit/inspection,
  regenerated from Python source via `tools/dump_reference_data.py`

### Documented FOCA PDF inconsistencies (resolved)

- Piston fuel-flow leading coefficient: body text `19e-12` vs Appendix E
  plot `1.9e-12` — use Appendix E value (verified at SHP=300)
- Appendix C twin-heavy power settings: Table 4 (2015) `6%/66%/32%` vs
  Appendix C MODEL column legacy `7%/75%/35%` — use Table 4
- Appendix C PM values 3-4x below formula prediction — use the formula
  (matches Appendix B and F plot exactly)

### Validation

| Appendix | Helicopter | Target fuel | Computed | Delta |
|---|---|---:|---:|---:|
| A | AS350B2 | 24.7 kg | 25.22 kg | +2.1% |
| B | A109 | 36.5 kg | 37.33 kg | +2.3% |
| C | AS332 | 78.4 kg | 77.6 kg | −1.0% |
