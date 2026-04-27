"""
foca_heli: standalone FOCA 2015 helicopter emissions library.

Licensed under the European Union Public Licence v. 1.2 (EUPL-1.2)
with certain amendments described in the AMENDMENT_TO_EUPL_license.md
file in the project root, reflecting EUROCONTROL's status as an
international organisation.

You may obtain a copy of the Licence at:

    https://joinup.ec.europa.eu/software/page/eupl

Unless required by applicable law or agreed to in writing, software
distributed under the Licence is distributed on an "AS IS" basis,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the Licence for the specific language governing
permissions and limitations under the Licence.

Public API:
    make_strategy          Build a strategy from engine attributes
    compute_lto            Compute full-LTO emissions for a strategy
    build_departure        Build departure trajectory for a category
    build_arrival          Build arrival trajectory for a category
    translate_and_rotate   Apply origin + heading transform to a trajectory
    to_wkt_linestring_z    Export trajectory as 3D WKT
    to_geojson_feature     Export trajectory as GeoJSON Feature
    read_engines_csv       Read input CSV (auto-detects schema)
    write_lto_csv          Write output CSV
"""

from foca_heli.airframe_mtoms import (
    AirframeMapping,
    BUILT_IN_AIRFRAME_MTOMS,
    built_in_mtom_dict,
    lookup_airframe,
    lookup_mtom_kg,
)
from foca_heli.csv_io import (
    EngineRow, detect_schema, load_airframe_mtoms,
    read_engines_csv, write_lto_csv,
)
from foca_heli.factory import make_strategy
from foca_heli.lto import LtoResult, ModeResult, compute_lto, lto_to_dict
from foca_heli.operational_profiles import (
    GI_ARRIVAL_FRACTION,
    GI_DEPARTURE_FRACTION,
    PROFILES,
    TWIN_MTOM_THRESHOLD_KG,
    HelicopterCategory,
    OperationalProfile,
    derive_category,
)
from foca_heli.strategies import (
    HelicopterEmissionStrategy, ModeEmissions,
    PistonStrategy, TurboshaftStrategy,
)
from foca_heli.trajectory import (
    TRAJECTORY_PARAMS, TrajectoryParams, TrajectoryPoint,
    build_arrival, build_departure,
    to_geojson_feature, to_wkt_linestring_2d, to_wkt_linestring_z,
    translate_and_rotate,
)

__all__ = [
    # LTO
    "compute_lto", "LtoResult", "ModeResult", "lto_to_dict",
    # Strategies
    "make_strategy", "HelicopterEmissionStrategy", "ModeEmissions",
    "PistonStrategy", "TurboshaftStrategy",
    # Profiles
    "PROFILES", "OperationalProfile", "HelicopterCategory",
    "derive_category", "TWIN_MTOM_THRESHOLD_KG",
    "GI_DEPARTURE_FRACTION", "GI_ARRIVAL_FRACTION",
    # Trajectories
    "TRAJECTORY_PARAMS", "TrajectoryParams", "TrajectoryPoint",
    "build_departure", "build_arrival", "translate_and_rotate",
    "to_wkt_linestring_2d", "to_wkt_linestring_z", "to_geojson_feature",
    # IO
    "EngineRow", "detect_schema", "load_airframe_mtoms",
    "read_engines_csv", "write_lto_csv",
    # Airframe lookup
    "AirframeMapping", "BUILT_IN_AIRFRAME_MTOMS", "built_in_mtom_dict",
    "lookup_airframe", "lookup_mtom_kg",
]
