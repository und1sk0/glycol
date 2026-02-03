import time
import requests

from glycol.auth import OpenSkyAuth

STATES_URL = "https://opensky-network.org/api/states/all"

# Field indices in the OpenSky state vector array
_FIELDS = [
    "icao24",          # 0
    "callsign",        # 1
    "origin_country",  # 2
    "time_position",   # 3
    "last_contact",    # 4
    "longitude",       # 5
    "latitude",        # 6
    "baro_altitude",   # 7
    "on_ground",       # 8
    "velocity",        # 9
    "true_track",      # 10
    "vertical_rate",   # 11
    "sensors",         # 12
    "geo_altitude",    # 13
    "squawk",          # 14
    "spi",             # 15
    "position_source", # 16
    "category",        # 17  (extended mode only)
]


def _parse_state(raw: list) -> dict:
    """Convert an index-based state vector into a named dict."""
    d = {}
    for i, name in enumerate(_FIELDS):
        d[name] = raw[i] if i < len(raw) else None
    # Normalize callsign whitespace
    if d.get("callsign"):
        d["callsign"] = d["callsign"].strip()
    return d


class OpenSkyClient:
    """Wraps the OpenSky Network REST API for state vector queries."""

    def __init__(self, auth: OpenSkyAuth):
        self.auth = auth
        self.rate_limit_remaining: int | None = None
        self._backoff_until: float = 0.0

    def get_states(
        self,
        bbox: tuple[float, float, float, float],
        icao24_filter: list[str] | None = None,
        extended: bool = True,
    ) -> list[dict]:
        """Fetch state vectors within a bounding box.

        *bbox* is (lamin, lamax, lomin, lomax).
        Returns a list of dicts, one per aircraft.
        """
        # Respect backoff
        now = time.time()
        if now < self._backoff_until:
            return []

        lamin, lamax, lomin, lomax = bbox
        params: dict = {
            "lamin": lamin,
            "lamax": lamax,
            "lomin": lomin,
            "lomax": lomax,
            "extended": 1 if extended else 0,
        }
        if icao24_filter:
            # The API accepts multiple icao24 params
            params["icao24"] = icao24_filter

        headers = self.auth.get_headers()

        try:
            resp = requests.get(
                STATES_URL, params=params, headers=headers, timeout=15
            )

            # Track rate limits
            rl = resp.headers.get("X-Rate-Limit-Remaining")
            if rl is not None:
                self.rate_limit_remaining = int(rl)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 10))
                self._backoff_until = time.time() + retry_after
                return []

            if resp.status_code == 401:
                # Token may have expired; force re-auth and retry once
                self.auth.authenticate()
                headers = self.auth.get_headers()
                resp = requests.get(
                    STATES_URL, params=params, headers=headers, timeout=15
                )

            resp.raise_for_status()
            data = resp.json()

            states_raw = data.get("states") or []
            return [_parse_state(s) for s in states_raw]

        except requests.RequestException:
            return []
