import gzip
import json
from pathlib import Path
from urllib.request import urlopen

# ADS-B Exchange Aircraft Database
_DATA_FILE = Path(__file__).resolve().parent / "data" / "basic-ac-db.json.gz"
_URL = "https://downloads.adsbexchange.com/downloads/basic-ac-db.json.gz"


def _ensure_data_file(path: Path, url: str) -> None:
    """Download the aircraft DB if it does not already exist."""
    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")

    with urlopen(url) as r, open(tmp, "wb") as f:
        # stream copy, no full read into memory
        while True:
            chunk = r.read(8192)
            if not chunk:
                break
            f.write(chunk)

    tmp.replace(path)


def icao24_reg_data(path: Path) -> dict[str, str]:
    """Load REG → ICAO24 mapping from gzipped NDJSON."""
    reg_to_icao: dict[str, str] = {}

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            reg = row.get("reg")
            icao = row.get("icao")

            if isinstance(reg, str) and isinstance(icao, str):
                reg_to_icao[reg.upper()] = icao.lower()

    return reg_to_icao


# public, module-level constant
_ensure_data_file(_DATA_FILE, _URL)

REG_TO_ICAO24: dict[str, str] = icao24_reg_data(_DATA_FILE)
AIRCRAFT: dict[str, str] = icao24_reg_data(_DATA_FILE)
