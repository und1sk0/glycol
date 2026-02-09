import json
import math
from pathlib import Path

# ICAO code -> (latitude, longitude, name)
_DATA_FILE = Path(__file__).resolve().parent / "data" / "us_airports.json"


def _load_airports() -> dict[str, tuple[float, float, str]]:
    with open(_DATA_FILE) as f:
        raw = json.load(f)
    return {code: (v[0], v[1], v[2]) for code, v in raw.items()}


AIRPORTS: dict[str, tuple[float, float, str]] = _load_airports()


NM_TO_DEG_LAT = 1.0 / 60.0  # 1 nautical mile ≈ 1/60 degree latitude


def get_bounding_box(
    icao_code: str,
    radius_nm: float = 5.0,
    lat: float | None = None,
    lon: float | None = None,
) -> tuple[float, float, float, float] | None:
    """Return (lamin, lamax, lomin, lomax) for the given airport and radius.

    If the ICAO code is in the known dict, its coordinates are used.
    Otherwise, *lat* and *lon* must be supplied.
    Returns None when coordinates cannot be determined.
    """
    if icao_code.upper() in AIRPORTS:
        lat, lon, _ = AIRPORTS[icao_code.upper()]
    if lat is None or lon is None:
        return None

    dlat = radius_nm * NM_TO_DEG_LAT
    # Longitude degrees per NM varies with latitude
    dlon = radius_nm * NM_TO_DEG_LAT / math.cos(math.radians(lat))

    return (lat - dlat, lat + dlat, lon - dlon, lon + dlon)


def airport_name(icao_code: str) -> str:
    """Return the human-readable name, or the code itself if unknown."""
    entry = AIRPORTS.get(icao_code.upper())
    return entry[2] if entry else icao_code.upper()
