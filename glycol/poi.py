"""
Planes of Interest (POI) database management.

Manages a JSON database of aircraft to track, with details like
tail number, ICAO24 address, make/model, and notes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PlaneOfInterest:
    """Represents a single plane of interest."""

    def __init__(
        self,
        tailnumber: str,
        name: str = "",
        icao24: str = "",
        make_model: str = "",
        notes: str = ""
    ):
        self.tailnumber = tailnumber.upper()  # Tail numbers typically uppercase
        self.name = name
        self.icao24 = icao24.lower() if icao24 else ""  # ICAO24 addresses are case-insensitive
        self.make_model = make_model
        self.notes = notes

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "tailnumber": self.tailnumber,
            "icao24": self.icao24,
            "make_model": self.make_model,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PlaneOfInterest":
        """Create from dictionary."""
        return cls(
            tailnumber=data.get("tailnumber", ""),
            name=data.get("name", ""),
            icao24=data.get("icao24", ""),
            make_model=data.get("make_model", ""),
            notes=data.get("notes", "")
        )

    def __repr__(self):
        return f"PlaneOfInterest(name={self.name}, icao24={self.icao24}, tailnumber={self.tailnumber})"


class POIDatabase:
    """Manages the planes of interest database."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        """
        Initialize the POI database.

        Args:
            db_path: Path to the JSON database file. If None, uses default location.
            data_dir: Directory containing data files. If provided, db_path is relative to this.
        """
        if db_path is None:
            if data_dir is None:
                # Default to glycol/data/planes_of_interest.json
                data_dir = Path(__file__).parent / "data"
            db_path = Path(data_dir) / "planes_of_interest.json"
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        self.planes: List[PlaneOfInterest] = []
        self._ensure_db_exists()
        self.load()

    def _ensure_db_exists(self):
        """Create the database file if it doesn't exist."""
        if not self.db_path.exists():
            logger.info(f"Creating planes of interest database at {self.db_path}")
            self.db_path.write_text("[]")

    def load(self):
        """Load planes from the database file."""
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self.planes = [PlaneOfInterest.from_dict(p) for p in data]
                logger.info(f"Loaded {len(self.planes)} planes of interest")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing POI database: {e}")
            self.planes = []
        except Exception as e:
            logger.error(f"Error loading POI database: {e}")
            self.planes = []

    def save(self):
        """Save planes to the database file."""
        try:
            data = [p.to_dict() for p in self.planes]
            with open(self.db_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.planes)} planes of interest")
        except Exception as e:
            logger.error(f"Error saving POI database: {e}")

    def add(self, plane: PlaneOfInterest) -> bool:
        """
        Add a plane to the database.

        Args:
            plane: The plane to add.

        Returns:
            True if added, False if already exists.
        """
        if self.get_by_tailnumber(plane.tailnumber):
            logger.warning(f"Plane with tail number {plane.tailnumber} already exists")
            return False

        self.planes.append(plane)
        self.save()
        logger.info(f"Added plane: {plane}")
        return True

    def get_by_icao24(self, icao24: str) -> Optional[PlaneOfInterest]:
        """Get a plane by its ICAO24 address."""
        icao24 = icao24.lower()
        for plane in self.planes:
            if plane.icao24 == icao24:
                return plane
        return None

    def get_by_tailnumber(self, tailnumber: str) -> Optional[PlaneOfInterest]:
        """Get a plane by its tail number."""
        tailnumber = tailnumber.upper()
        for plane in self.planes:
            if plane.tailnumber == tailnumber:
                return plane
        return None

    def update(self, icao24: str, **kwargs) -> bool:
        """
        Update a plane's details.

        Args:
            icao24: ICAO24 address of the plane to update.
            **kwargs: Fields to update (tailnumber, make_model, notes).

        Returns:
            True if updated, False if not found.
        """
        plane = self.get_by_icao24(icao24)
        if not plane:
            logger.warning(f"Plane with ICAO24 {icao24} not found")
            return False

        for key, value in kwargs.items():
            if hasattr(plane, key):
                setattr(plane, key, value)

        self.save()
        logger.info(f"Updated plane: {plane}")
        return True

    def remove(self, icao24: str) -> bool:
        """
        Remove a plane from the database.

        Args:
            icao24: ICAO24 address of the plane to remove.

        Returns:
            True if removed, False if not found.
        """
        plane = self.get_by_icao24(icao24)
        if not plane:
            logger.warning(f"Plane with ICAO24 {icao24} not found")
            return False

        self.planes.remove(plane)
        self.save()
        logger.info(f"Removed plane: {plane}")
        return True

    def list_all(self) -> List[PlaneOfInterest]:
        """Get all planes in the database."""
        return self.planes.copy()

    def get_icao24_list(self) -> List[str]:
        """Get a list of all ICAO24 addresses."""
        return [p.icao24 for p in self.planes]

    def get_tailnumber_list(self) -> List[str]:
        """Get a list of all tail numbers."""
        return [p.tailnumber for p in self.planes if p.tailnumber]
