"""
Command-line interface for foca_heli.

Usage:
    python -m foca_heli.cli lto --in ENGINES.csv --out LTO.csv
                                [--airframe AIRFRAME.csv]

    python -m foca_heli.cli single --category SINGLE_TURBOSHAFT
                                   --max-shp 732 --engines 1

    python -m foca_heli.cli trajectory --category SINGLE_TURBOSHAFT
                                       [--part dep|arr|both]
                                       [--format wkt|geojson]
                                       [--origin-x 0 --origin-y 0]
                                       [--heading 0]
"""

import argparse
import json
import sys
from typing import Optional

from foca_heli.csv_io import (
    load_airframe_mtoms, read_engines_csv, write_lto_csv,
)
from foca_heli.factory import make_strategy
from foca_heli.lto import compute_lto, lto_to_dict
from foca_heli.operational_profiles import HelicopterCategory
from foca_heli.trajectory import (
    build_arrival, build_departure,
    to_geojson_feature, to_wkt_linestring_z,
    translate_and_rotate,
)


VALID_CATEGORIES = {
    "PISTON",
    "SINGLE_TURBOSHAFT",
    "TWIN_TURBOSHAFT_LIGHT",
    "TWIN_TURBOSHAFT_HEAVY",
}


def cmd_lto(args: argparse.Namespace) -> int:
    """Bulk LTO: read engines CSV, write LTO CSV."""
    airframe_mtoms = None
    if args.airframe:
        airframe_mtoms = load_airframe_mtoms(args.airframe)
        sys.stderr.write(
            f"Loaded {len(airframe_mtoms)} airframe MTOM entries\n"
        )

    engines = read_engines_csv(
        args.input,
        airframe_mtoms=airframe_mtoms,
        strict=args.strict,
    )
    sys.stderr.write(f"Read {len(engines)} engines from {args.input}\n")

    out_rows = []
    for row in engines:
        strategy = make_strategy(
            category=row.category,
            max_shp_per_engine=row.max_shp_per_engine,
            number_of_engines=row.number_of_engines,
            mtom_kg=row.mtom_kg,
        )
        result = compute_lto(strategy)
        out_rows.append((row, lto_to_dict(result)))

    write_lto_csv(args.output, out_rows)
    sys.stderr.write(f"Wrote {len(out_rows)} rows to {args.output}\n")
    return 0


def cmd_single(args: argparse.Namespace) -> int:
    """Single-engine LTO computation, printed to stdout."""
    _validate_category(args.category)
    strategy = make_strategy(
        category=args.category,
        max_shp_per_engine=args.max_shp,
        number_of_engines=args.engines,
    )
    result = compute_lto(strategy)

    # Pretty-print
    print(f"Category:            {args.category}")
    print(f"Max SHP per engine:  {args.max_shp}")
    print(f"Number of engines:   {args.engines}")
    print()
    print(f"{'Mode':6s} {'Power':>6s} {'Time':>6s} {'FF/eng':>10s} "
          f"{'Fuel':>9s} {'NOx':>9s} {'HC':>9s} {'CO':>9s} {'PM':>9s} {'CO2':>10s}")
    print(f"{'':6s} {'':>6s} {'(s)':>6s} {'(kg/s)':>10s} "
          f"{'(kg)':>9s} {'(g)':>9s} {'(g)':>9s} {'(g)':>9s} {'(g)':>9s} {'(g)':>10s}")
    for m in result.modes:
        print(
            f"{m.mode:6s} {m.power_fraction*100:>5.0f}% {m.time_s:>6.0f} "
            f"{m.fuel_flow_kg_s_per_engine:>10.5f} "
            f"{m.fuel_kg:>9.2f} {m.nox_g:>9.2f} {m.hc_g:>9.2f} "
            f"{m.co_g:>9.2f} {m.pm_g:>9.3f} {m.co2_g:>10.0f}"
        )
    print()
    print(f"{'TOTAL':6s} {'':>6s} {'':>6s} {'':>10s} "
          f"{result.fuel_kg:>9.2f} {result.nox_g:>9.2f} {result.hc_g:>9.2f} "
          f"{result.co_g:>9.2f} {result.pm_g:>9.3f} {result.co2_g:>10.0f}")
    return 0


def cmd_trajectory(args: argparse.Namespace) -> int:
    """Build a trajectory and emit WKT or GeoJSON."""
    _validate_category(args.category)

    parts: list[tuple[str, list]] = []
    if args.part in ("dep", "both"):
        parts.append(("departure", build_departure(args.category)))
    if args.part in ("arr", "both"):
        parts.append(("arrival", build_arrival(args.category)))

    # Apply transforms
    transformed = []
    for label, points in parts:
        rotated = translate_and_rotate(
            points,
            origin_x_m=args.origin_x,
            origin_y_m=args.origin_y,
            heading_deg=args.heading,
        )
        transformed.append((label, rotated))

    if args.format == "wkt":
        for label, pts in transformed:
            print(f"-- {label} ({args.category})")
            print(to_wkt_linestring_z(pts))
            print()
    elif args.format == "geojson":
        features = []
        for label, pts in transformed:
            features.append(to_geojson_feature(pts, properties={
                "category": args.category,
                "phase": label,
                "heading_deg": args.heading,
                "origin_x_m": args.origin_x,
                "origin_y_m": args.origin_y,
            }))
        fc = {"type": "FeatureCollection", "features": features}
        print(json.dumps(fc, indent=2))
    else:  # table
        for label, pts in transformed:
            print(f"-- {label} ({args.category})")
            print(f"{'mode':6s} {'t (s)':>7s} {'x (m)':>10s} {'y (m)':>10s} "
                  f"{'z (m)':>8s} {'TAS':>8s}")
            for p in pts:
                print(f"{p.mode:6s} {p.t_s:>7.1f} {p.x_m:>10.2f} {p.y_m:>10.2f} "
                      f"{p.z_m:>8.2f} {p.tas_m_s:>8.2f}")
            print()

    return 0


def _validate_category(category: str) -> None:
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category {category!r}. Must be one of: {sorted(VALID_CATEGORIES)}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foca_heli",
        description=(
            "FOCA 2015 helicopter emissions calculator. "
            "Computes LTO mass emissions and per-category trajectories."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # lto subcommand
    p_lto = sub.add_parser("lto", help="Bulk LTO from CSV")
    p_lto.add_argument("--in", dest="input", required=True,
                       help="Input engines CSV (auto-detects schema)")
    p_lto.add_argument("--out", dest="output", required=True,
                       help="Output LTO results CSV")
    p_lto.add_argument("--airframe", dest="airframe", default=None,
                       help="Optional airframe CSV for MTOM lookup "
                            "(needed for OLD-schema twin turboshaft rows)")
    p_lto.add_argument("--strict", action="store_true",
                       help="Raise on twin turboshaft rows without MTOM "
                            "(default: warn and fall back to LIGHT)")
    p_lto.set_defaults(func=cmd_lto)

    # single subcommand
    p_single = sub.add_parser("single", help="Single engine LTO")
    p_single.add_argument("--category", required=True,
                          choices=sorted(VALID_CATEGORIES))
    p_single.add_argument("--max-shp", type=float, required=True,
                          help="Max SHP per engine")
    p_single.add_argument("--engines", type=int, default=1,
                          help="Number of engines (default 1)")
    p_single.set_defaults(func=cmd_single)

    # trajectory subcommand
    p_traj = sub.add_parser("trajectory", help="Build a trajectory")
    p_traj.add_argument("--category", required=True,
                        choices=sorted(VALID_CATEGORIES))
    p_traj.add_argument("--part", choices=["dep", "arr", "both"],
                        default="both")
    p_traj.add_argument("--format", choices=["wkt", "geojson", "table"],
                        default="table")
    p_traj.add_argument("--origin-x", type=float, default=0.0,
                        dest="origin_x")
    p_traj.add_argument("--origin-y", type=float, default=0.0,
                        dest="origin_y")
    p_traj.add_argument("--heading", type=float, default=0.0,
                        help="Compass heading in degrees (0=north, 90=east)")
    p_traj.set_defaults(func=cmd_trajectory)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
