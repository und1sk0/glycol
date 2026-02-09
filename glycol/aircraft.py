import gzip
import json
from pathlib import Path
from urllib.request import Request, urlopen

# ADS-B Exchange Aircraft Database
_DATA_FILE = Path(__file__).resolve().parent / "data" / "basic-ac-db.json.gz"
_URL = "https://downloads.adsbexchange.com/downloads/basic-ac-db.json.gz"


def _ensure_data_file(path: Path, url: str) -> None:
    """Download the aircraft DB if it does not already exist."""
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")

    # Add User-Agent to avoid 403 Forbidden
    req = Request(url, headers={"User-Agent": "Glycol/1.0"})

    with urlopen(req) as r, open(tmp, "wb") as f:
        # stream copy, no full read into memory
        while True:
            chunk = r.read(8192)
            if not chunk:
                break
            f.write(chunk)

    tmp.replace(path)


def load_aircraft_data(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load aircraft database from gzipped NDJSON.

    Returns:
        (REG → ICAO24 mapping, ICAO24 → type code mapping)
    """
    reg_to_icao: dict[str, str] = {}
    icao_to_type: dict[str, str] = {}

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            reg = row.get("reg")
            icao = row.get("icao")
            type_code = row.get("icaotype")

            if isinstance(icao, str):
                icao_lower = icao.lower()

                # Build REG → ICAO24 mapping
                if isinstance(reg, str):
                    reg_to_icao[reg.upper()] = icao_lower

                # Build ICAO24 → type code mapping
                if isinstance(type_code, str) and type_code:
                    icao_to_type[icao_lower] = type_code.upper()

    return reg_to_icao, icao_to_type


# public, module-level constants
_ensure_data_file(_DATA_FILE, _URL)

REG_TO_ICAO24: dict[str, str]
ICAO24_TO_TYPE: dict[str, str]

REG_TO_ICAO24, ICAO24_TO_TYPE = load_aircraft_data(_DATA_FILE)

# Legacy alias for backwards compatibility
AIRCRAFT: dict[str, str] = REG_TO_ICAO24
