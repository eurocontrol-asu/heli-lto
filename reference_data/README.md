# Reference Data (informational dumps)

This directory contains CSV dumps of all the FOCA 2015 reference data
embedded in the `foca_heli` package. **These files are OUTPUTS, not
INPUTS.** Editing them does NOT change library behavior.

The authoritative source for every value here is the Python code in
`foca_heli/`. The CSVs are regenerated from that code by:

```
python tools/dump_reference_data.py
```

## Files

| File | Rows | What it contains |
|---|---:|---|
| `piston_ei_tables.csv` | 4 | FOCA Tables 5-7: piston EI NOx, PM, particle size by power setting |
| `turboshaft_particle_size.csv` | 12 | FOCA Table 8: turboshaft nvPM particle size by category + power |
| `operational_profiles.csv` | 4 | FOCA Tables 1-4: time-in-mode and power settings per helicopter category |
| `formula_coefficients.csv` | 13 | All polynomial coefficients and scaling factors used in `formulas.py` |
| `trajectory_params.csv` | 4 | Per-category flight parameters (climb ROC, TAS, cruise TAS, approach geometry) |
| `airframe_mtoms.csv` | 41 | Engine-name → airframe MTOM lookup with citations (used for twin-TS classification) |
| `global_constants.csv` | 8 | TWIN_MTOM_THRESHOLD, GI_DEP_FRACTION, LTO_CEILING, CO2 factors, etc. |

## Why the data is embedded in Python, not loaded from CSV

1. **Provenance.** Every value traces back to a specific page/table/figure in the FOCA 2015 PDF. Python source code is the right place for that — docstrings live next to the data, and edits are tracked in version control. A CSV is a loose file that someone could edit without a code review.

2. **Type safety.** A typo in a Python dict key fails at import. A typo in a CSV column fails at runtime, possibly with bad numbers instead of an error.

3. **Function data.** The fuel-flow polynomials are functions of SHP, not tables of (input, output) pairs. CSV-izing them would mean either exporting coefficients (what we did here, for inspection only) or pre-computing a grid of values and introducing interpolation error.

4. **No parsing layer.** One less failure mode. The library has zero I/O for reference data — it's all compiled-in constants.

## When to consult these files

- **Audit.** If someone needs to verify our implementation against the FOCA PDF without reading Python, these CSVs are the simplest view.
- **Cross-check.** Compare row counts, tables, and numeric values against the original PDF's appendices.
- **Override.** The `airframe_mtoms.csv` can be edited and passed via `--airframe` flag to replace the built-in lookup for specific engines. None of the other files have this use case — they reflect the standard and shouldn't be edited.

## When NOT to use these files

- Don't parse them in production code. The library's own Python constants are always the source of truth, and they're free (already loaded when you `import foca_heli`).
- Don't treat them as configuration. They're the FOCA 2015 standard; if you need to change a value, you're either fixing a transcription bug (in which case edit the Python and regenerate the CSVs) or creating a new, non-FOCA calculation (in which case you should fork and rename).
