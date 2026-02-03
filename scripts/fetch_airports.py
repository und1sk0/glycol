#!/usr/bin/env python3
"""Fetch US airport data from OurAirports and write glycol/data/us_airports.json."""

import csv
import io
import json
import urllib.request
from pathlib import Path

OURAIRPORTS_CSV_URL = (
    "https://davidmegginson.github.io/ourairports-data/airports.csv"
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "glycol" / "data" / "us_airports.json"


def fetch_airports() -> dict[str, list]:
    """Download the OurAirports CSV and return US airports as a dict.

    Returns dict of ``{ICAO: [lat, lon, name], ...}``.
    """
    print(f"Downloading {OURAIRPORTS_CSV_URL} ...")
    with urllib.request.urlopen(OURAIRPORTS_CSV_URL) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    airports: dict[str, list] = {}
    for row in reader:
        icao = row.get("ident", "").strip()
        country = row.get("iso_country", "").strip()
        # Include US states and territories (separate ISO codes in OurAirports)
        US_CODES = {"US", "GU", "PR", "VI", "AS", "MP"}
        if country not in US_CODES or not icao:
            continue
        try:
            lat = round(float(row["latitude_deg"]), 6)
            lon = round(float(row["longitude_deg"]), 6)
        except (ValueError, KeyError):
            continue
        name = row.get("name", icao).strip()
        airports[icao] = [lat, lon, name]

    return airports


def main() -> None:
    airports = fetch_airports()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(airports, f, separators=(",", ":"))
    print(f"Wrote {len(airports)} US airports to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
