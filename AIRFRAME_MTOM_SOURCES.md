# Airframe MTOM Lookup — Source Citations

Documentation for the hand-curated engine → airframe MTOM lookup in
`foca_heli/airframe_mtoms.py`. Each twin-turboshaft engine in the plugin's
`default_helicopter_engine_ei.csv` is mapped to a representative airframe
and that airframe's MTOM. The lookup is needed because FOCA 2015 splits
twin turboshafts into LIGHT (≤3400 kg MTOM) and HEAVY (>3400 kg) categories
with substantially different power-setting profiles.

The heli engine CSV lists 37 unique engine/SHP twin-turboshaft combinations.
The airframe CSV (`default_aircraft.csv`) does not share a join key with
the heli engine CSV (different naming conventions), so this mapping had
to be built manually from aviation authority data sheets, manufacturer
brochures, and encyclopedic sources.

---

## Selection methodology

For each engine, we identified the most common helicopter installation
in civilian service. When an engine powers multiple airframes with
different MTOMs (e.g., Arriel 1C1 goes on both AS365N1 at 4100 kg and
some military variants), we picked the civilian production model that
is most representative of real-world fleet operations.

All quoted MTOMs are maximum takeoff weight in kg, from the cited source.

---

## Twin turboshaft engines (37 unique entries)

### Turbomeca / Safran Arriel 1 series (twin variants)

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| ARRIEL 1A1 | SA365C1 Dauphin 2 | 3400 | Wikipedia Eurocopter AS365 Dauphin; EASA TCDS E.073 |
| ARRIEL 1A2 | SA365C2 Dauphin 2 | 3400 | Wikipedia Eurocopter AS365 Dauphin |
| ARRIEL 1C | SA365N Dauphin 2 (initial) | 3850 | Wikipedia: SA365N with 660 shp Arriel 1C, MTOW 3850 kg (later 4000 kg) |
| ARRIEL 1C1 | AS365N1 Dauphin 2 | 4100 | Wikipedia: AS365N1 with 705 shp Arriel 1C1, MTOW 4100 kg |
| ARRIEL 1D1 (twin, 712 SHP) | AS355N Twin Squirrel | 2600 | Plugin airframe CSV: AS-355 Ecureuil 2; EASA AD notes Arriel 1D1 installation |
| ARRIEL 1E2 | MBB-BK 117 C1 / EC145 | 3585 | FAA AD: Arriel 1E2 on BK117-C1; BK117 B2 specifications |
| ARRIEL1K1 | Agusta A109K2 | 2720 | Aviation.govt.nz TAR 15/21B/3; A109K2 MTOW 2720 kg |

### Turbomeca / Safran Arriel 2 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| ARRIEL 2C | AS365 N3 Dauphin 2 | 4300 | Wikipedia: AS365 N3 with 851 shp Arriel 2C, MTOW 4300 kg |
| ARRIEL 2C1 | EC155 B | 4800 | Globalmilitary.net: EC155 B with Arriel 2C1, MTOW 4800 kg |
| ARRIEL 2C2 | EC155 B1 / HH-65C | 4950 | Wikipedia EC155 B1 / Globalmilitary.net |
| ARRIEL 2S1 | Sikorsky S-76C+ | 5307 | Wikipedia Sikorsky S-76; Lobo Helicopter File |

### Turbomeca / Safran Arrius series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| ARRIUS 1A | AS355 F variant / early EC355 | 2540 | EASA TCDS E.080: Arrius 1/1A1 for twin-engine helicopters; AS355 MTOW |
| ARRIUS 2B1 | EC135 T1 | 2720 | Wikipedia EC135: T1 initial MTOW 2630, later 2720 kg |
| ARRIUS 2B2 | EC135 T2 / T2+ | 2910 | Wikipedia/SKYbrary EC135: T2/T2+ MTOW 2910-2950 kg |
| ARRIUS 2K | AW109 Power | 2850 | Safran: Arrius 2K2 drives AW109 Power |

### Pratt & Whitney Canada PW200 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| PW206A | Agusta A109 Power (early variant) | 2850 | P&W PW200 product page |
| PW206C | Agusta A109 E Power | 2850 | P&W PW200 page; FOCA 2015 Appendix B validation (confirmed match at 36.5 kg LTO fuel) |
| PW207C | Leonardo A109 Grand / AW109 Nexus | 3175 | P&W PW200 product page |

### Pratt & Whitney Canada PT6 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| PT6B-36A | Sikorsky S-76B | 5307 | Wikipedia Sikorsky S-76; S-76B with PT6B-36A/B |
| PT6C-67C | AgustaWestland AW139 | 6400 | Wikipedia/SKYbrary/Leonardo AW139 brochure; baseline MTOW 6400 kg (6800/7000 optional) |
| PT6T-3 | Bell 212 Twin Huey | 5080 | Wikipedia/SKYbrary Bell 212 |

Note on PT6T-3: this is a Twin-Pac design (two power sections combined in
one unit). The heli CSV treats each section as "n_engines=2" at 1800 shp
total combined.

### Allison / Rolls-Royce DDA 250 series (twin variants)

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| DDA250-C20 | MBB Bo 105 C (initial) | 2300 | Wikipedia Bo 105: Bo 105C with Allison 250-C20 |
| DDA250-C20B | MBB Bo 105 CB / CBS | 2500 | Wikipedia/SKYbrary/ResearchGate Bo 105: 420 shp C20B, MTOW 2500 kg |
| DDA250-C20F | MBB Bo 105 CBS | 2500 | Bo 105 family (minor subvariant) |
| DDA250-C20R | MBB Bo 105 LS A1 | 2500 | Wikipedia Bo 105: LS variants |
| DDA250-C20R/1 | MBB Bo 105 LS A3 | 2600 | Wikipedia Bo 105: LS A3 (1986), MTOW 2600 kg |
| DDA250-C30S | Sikorsky S-76A (original) | 5307 | Wikipedia S-76: Original S-76A with Allison 250-C30 series |
| DDA250-C40B | MD Explorer 900 (early) | 2835 | 715 SHP twin variant on MD Explorer 900 |

### Honeywell / Lycoming LTS101 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| LTS101-750B.1 | Aerospatiale HH-65A Dolphin | 4000 | Wikipedia/Naval-Technology: HH-65A with 734 shp LTS101-750B-2, MTOW 4000 kg |
| LTS101-750C.1 | MBB-BK 117 A3/A4 | 3350 | BK-117 B2 specs: LTS101-750-B1 at 700 WPS, MTOW 3350 kg |

### Turbomeca MAKILA series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| MAKILA 1A1 | Eurocopter AS332L1 Super Puma | 8600 | Eurocopter Technical Data brochure 2006 (full PDF fetched); FOCA 2015 Appendix C validation (confirmed match at 78.4 kg LTO fuel) |

### General Electric T700 / CT7 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| T700-GE-700 | Sikorsky UH-60A Black Hawk | 9185 | Wikipedia UH-60A: MTOW 20,250 lb = 9185 kg |
| GE CT7-8A | Sikorsky S-92 | 12000 | SKYbrary/Wikipedia S-92: two CT7-8A at 2520 shp each, MTOW 12,000 kg (Flight Global cites 12,835 kg for specific variants) |

### Klimov TV series (Soviet)

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| TV2-117 | Mil Mi-8 (original) | 12000 | Mi-8 family MTOW; National Interest; aviastar.org |
| TV3-117VMA | Mil Mi-17 / Mi-171 | 13000 | SKYbrary/Wikipedia Mi-17: TV3-117VM, MTOW 13,000 kg |

### General Electric T64 series

| Engine | Airframe | MTOM (kg) | Source |
|---|---|---:|---|
| T 64-GE-7 | Sikorsky HH-53B / CH-53 Sea Stallion | 19050 | Pave Cave USAF MH-53 History: T64-GE-7 at 3925 shp upgrade for HH-53B; aviastar.org CH-53 specs |

The heli CSV also lists T 64-GE-7 with n_engines=3. This classifies as
HEAVY regardless (MTOM × 3 >> 3400 kg threshold), so the categorization
is robust even for this anomalous entry.

---

## Summary statistics

After applying the built-in lookup, the plugin's 86 helicopter engines classify as:

- 11 PISTON
- 34 SINGLE_TURBOSHAFT
- 21 TWIN_TURBOSHAFT_LIGHT
- 20 TWIN_TURBOSHAFT_HEAVY

Before the lookup was built (warning-fallback to LIGHT), the distribution
was 41 LIGHT / 0 HEAVY, meaning roughly half of the twin-turboshaft engines
were being systematically mis-categorized. The HEAVY ones include large
helicopters like AS332, AW139, S-92, UH-60, Bell 212, Mi-17, CH-53 — all
of which would have had their LTO emissions underestimated with LIGHT
power settings.

---

## Sensitivity to MTOM choice

When an engine powers multiple airframes with MTOMs straddling the 3400 kg
threshold, the choice matters. Sensitive cases in this lookup:

- **ARRIEL 1A1** (SA365C1 at exactly 3400 kg): tie goes to LIGHT per
  FOCA's ≤3400 kg convention
- **ARRIEL 1E2** on BK117-C1 (3585 kg, HEAVY) vs EC145 (3585 kg, HEAVY):
  both above threshold, robust

For all other entries the chosen airframe is clearly on one side of the
threshold.

---

## Override with --airframe

Users can supply their own airframe CSV via `--airframe airframes.csv` to
the CLI or `airframe_mtoms=` kwarg to `read_engines_csv()`. User-provided
values override the built-in lookup for any engine present in both.
