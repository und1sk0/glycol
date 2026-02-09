import datetime


class AircraftMonitor:
    """Detects takeoff and landing events by tracking on_ground transitions."""

    FEET_TO_METERS = 0.3048

    def __init__(
        self,
        filter_mode: str | None = None,
        filter_values: list[str] | None = None,
        ceiling_ft: float | None = 1500,
        icao_to_type: dict[str, str] | None = None,
    ):
        """
        Initialize the aircraft monitor.

        Args:
            filter_mode: Filter mode - "aircraft", "type_group", or None (all traffic)
            filter_values: List of values to filter by (depends on filter_mode)
            ceiling_ft: Maximum altitude in feet to track (None = no ceiling)
            icao_to_type: ICAO24 -> type code mapping for type group filtering
        """
        self.filter_mode = filter_mode
        self.filter_values: list[str] = [
            v.strip().upper() for v in (filter_values or [])
        ]
        self.ceiling_m: float | None = (
            ceiling_ft * self.FEET_TO_METERS if ceiling_ft is not None else None
        )
        self.icao_to_type: dict[str, str] = icao_to_type or {}
        # icao24 -> on_ground (bool)
        self._prev_states: dict[str, bool] = {}

    def set_filter(self, filter_mode: str | None, filter_values: list[str] | None = None):
        """Update the filter configuration."""
        self.filter_mode = filter_mode
        self.filter_values = [v.strip().upper() for v in (filter_values or [])]

    def _matches_filter(self, state: dict) -> bool:
        """Check if an aircraft state matches the current filter."""
        # No filter - all traffic
        if self.filter_mode is None:
            return True

        # Aircraft filter - match by ICAO24, callsign, or tail number
        if self.filter_mode == "aircraft":
            icao24 = (state.get("icao24") or "").upper()
            callsign = (state.get("callsign") or "").upper()
            return icao24 in self.filter_values or callsign in self.filter_values

        # Type group filter - match by aircraft type code
        if self.filter_mode == "type_group":
            # Look up aircraft type code from ICAO24
            icao24 = (state.get("icao24") or "").lower()
            type_code = self.icao_to_type.get(icao24)
            if type_code:
                return type_code.upper() in self.filter_values
            return False

        # Unknown filter mode - default to allow
        return True

    def process_states(self, states: list[dict]) -> list[dict]:
        """Process a batch of state vectors and return detected events.

        Each event is a dict with keys: type, icao24, callsign, timestamp, and
        all other state vector fields.
        """
        events: list[dict] = []
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current: dict[str, bool] = {}

        for state in states:
            if not self._matches_filter(state):
                continue

            if self.ceiling_m is not None:
                alt = state.get("baro_altitude")
                if alt is not None and alt > self.ceiling_m:
                    continue

            icao24 = state.get("icao24", "")
            on_ground = state.get("on_ground", False)
            current[icao24] = on_ground

            if icao24 in self._prev_states:
                was_ground = self._prev_states[icao24]
                if was_ground and not on_ground:
                    events.append(self._make_event("takeoff", state, now))
                elif not was_ground and on_ground:
                    events.append(self._make_event("landing", state, now))
            else:
                # New aircraft in bounding box
                etype = "new_ground" if on_ground else "new_airborne"
                events.append(self._make_event(etype, state, now))

        self._prev_states = current
        return events

    def reset(self):
        """Clear tracked state."""
        self._prev_states.clear()

    @staticmethod
    def _make_event(event_type: str, state: dict, timestamp: str) -> dict:
        return {
            "type": event_type,
            "timestamp": timestamp,
            "icao24": state.get("icao24", ""),
            "callsign": state.get("callsign", ""),
            "latitude": state.get("latitude"),
            "longitude": state.get("longitude"),
            "altitude_m": state.get("baro_altitude"),
            "velocity_ms": state.get("velocity"),
            "heading": state.get("true_track"),
            "vertical_rate": state.get("vertical_rate"),
            "on_ground": state.get("on_ground"),
            "squawk": state.get("squawk"),
            "category": state.get("category"),
            "origin_country": state.get("origin_country"),
        }
