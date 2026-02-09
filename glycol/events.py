import datetime
import os

import pandas as pd

_COLUMNS = [
    "timestamp",
    "event_type",
    "icao24",
    "callsign",
    "airport",
    "latitude",
    "longitude",
    "altitude_m",
    "velocity_ms",
    "heading",
    "vertical_rate",
    "squawk",
    "category",
    "origin_country",
]


class EventStore:
    """Accumulates takeoff/landing events in a pandas DataFrame."""

    def __init__(self, airport: str = "", logs_dir: str | None = None):
        self.airport = airport.upper()
        self.logs_dir = logs_dir
        self._df = pd.DataFrame(columns=_COLUMNS)

    def record_event(self, event: dict):
        """Append a single event dict (from AircraftMonitor) to the store."""
        row = {
            "timestamp": event.get("timestamp", ""),
            "event_type": event.get("type", ""),
            "icao24": event.get("icao24", ""),
            "callsign": event.get("callsign", ""),
            "airport": self.airport,
            "latitude": event.get("latitude"),
            "longitude": event.get("longitude"),
            "altitude_m": event.get("altitude_m"),
            "velocity_ms": event.get("velocity_ms"),
            "heading": event.get("heading"),
            "vertical_rate": event.get("vertical_rate"),
            "squawk": event.get("squawk"),
            "category": event.get("category"),
            "origin_country": event.get("origin_country"),
        }
        self._df = pd.concat([self._df, pd.DataFrame([row])], ignore_index=True)

    def get_dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def save_csv(self, path: str | None = None) -> str:
        """Write events to CSV. Returns the path written."""
        if path is None:
            date_str = datetime.date.today().isoformat()
            filename = f"glycol_events_{self.airport}_{date_str}.csv"
            if self.logs_dir:
                path = os.path.join(self.logs_dir, filename)
            else:
                path = os.path.join(os.getcwd(), "logs", filename)
        self._df.to_csv(path, index=False)
        return path

    def clear(self):
        self._df = pd.DataFrame(columns=_COLUMNS)

    def __len__(self) -> int:
        return len(self._df)
