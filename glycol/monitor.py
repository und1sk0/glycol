import datetime


class AircraftMonitor:
    """Detects takeoff and landing events by tracking on_ground transitions."""

    # Filter modes
    MODE_A = "A"  # Filter by ICAO24 addresses or callsign/tail numbers
    MODE_B = "B"  # Filter by aircraft category codes
    MODE_C = "C"  # All traffic

    FEET_TO_METERS = 0.3048

    def __init__(
        self,
        mode: str = "C",
        filter_values: list[str] | None = None,
        ceiling_ft: float | None = 1500,
    ):
        self.mode = mode.upper()
        self.filter_values: list[str] = [
            v.strip().upper() for v in (filter_values or [])
        ]
        self.ceiling_m: float | None = (
            ceiling_ft * self.FEET_TO_METERS if ceiling_ft is not None else None
        )
        # icao24 -> on_ground (bool)
        self._prev_states: dict[str, bool] = {}

    def set_filter(self, mode: str, filter_values: list[str] | None = None):
        self.mode = mode.upper()
        self.filter_values = [v.strip().upper() for v in (filter_values or [])]

    def _matches_filter(self, state: dict) -> bool:
        if self.mode == self.MODE_C:
            return True
        if self.mode == self.MODE_A:
            icao24 = (state.get("icao24") or "").upper()
            callsign = (state.get("callsign") or "").upper()
            return icao24 in self.filter_values or callsign in self.filter_values
        if self.mode == self.MODE_B:
            cat = state.get("category")
            if cat is not None:
                return str(cat) in self.filter_values
            return False
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
