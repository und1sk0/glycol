"""
Aircraft groups and type code glossary management.

Manages a JSON database of aircraft type groups (passenger, cargo, military, etc.)
and a glossary mapping type codes to their full make/model/notes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AircraftType:
    """Represents a single aircraft type in the glossary."""

    def __init__(self, code: str, make: str = "", model: str = "", notes: str = ""):
        self.code = code.upper()
        self.make = make
        self.model = model
        self.notes = notes

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "make": self.make,
            "model": self.model,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, code: str, data: Dict) -> "AircraftType":
        """Create from dictionary."""
        return cls(
            code=code,
            make=data.get("make", ""),
            model=data.get("model", ""),
            notes=data.get("notes", "")
        )

    def __repr__(self):
        return f"AircraftType(code={self.code}, make={self.make}, model={self.model})"


class GroupsDatabase:
    """Manages the aircraft groups and glossary database."""

    def __init__(self, db_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        """
        Initialize the groups database.

        Args:
            db_path: Path to the JSON database file. If None, uses default location.
            data_dir: Directory containing data files. If provided, db_path is relative to this.
        """
        if db_path is None:
            if data_dir is None:
                # Default to glycol/data/type_groups.json
                data_dir = Path(__file__).parent / "data"
            db_path = Path(data_dir) / "type_groups.json"
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        self.groups: Dict[str, List[str]] = {}
        self.glossary: Dict[str, AircraftType] = {}
        self._ensure_db_exists()
        self.load()

    def _ensure_db_exists(self):
        """Create the database file if it doesn't exist."""
        if not self.db_path.exists():
            logger.info(f"Creating aircraft groups database at {self.db_path}")
            initial_data = {"groups": {}, "glossary": {}}
            self.db_path.write_text(json.dumps(initial_data, indent=2))

    def load(self):
        """Load groups and glossary from the database file."""
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)

            self.groups = data.get("groups", {})

            # Load glossary
            glossary_data = data.get("glossary", {})
            self.glossary = {
                code: AircraftType.from_dict(code, details)
                for code, details in glossary_data.items()
            }

            logger.info(
                f"Loaded {len(self.groups)} groups and {len(self.glossary)} "
                f"aircraft types from glossary"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing groups database: {e}")
            self.groups = {}
            self.glossary = {}
        except Exception as e:
            logger.error(f"Error loading groups database: {e}")
            self.groups = {}
            self.glossary = {}

    def save(self):
        """Save groups and glossary to the database file."""
        try:
            data = {
                "groups": self.groups,
                "glossary": {code: aircraft.to_dict() for code, aircraft in self.glossary.items()}
            }
            with open(self.db_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(
                f"Saved {len(self.groups)} groups and {len(self.glossary)} "
                f"aircraft types to glossary"
            )
        except Exception as e:
            logger.error(f"Error saving groups database: {e}")

    # Group management methods
    def list_groups(self) -> List[str]:
        """Get a list of all group names."""
        return list(self.groups.keys())

    def get_group(self, group_name: str) -> Optional[List[str]]:
        """Get aircraft codes in a group."""
        return self.groups.get(group_name)

    def create_group(self, group_name: str, aircraft_codes: Optional[List[str]] = None) -> bool:
        """
        Create a new group.

        Args:
            group_name: Name of the group to create.
            aircraft_codes: Optional list of aircraft codes to add.

        Returns:
            True if created, False if already exists.
        """
        if group_name in self.groups:
            logger.warning(f"Group '{group_name}' already exists")
            return False

        self.groups[group_name] = aircraft_codes or []
        self.save()
        logger.info(f"Created group: {group_name}")
        return True

    def add_to_group(self, group_name: str, aircraft_code: str) -> bool:
        """
        Add an aircraft code to a group.

        Args:
            group_name: Name of the group.
            aircraft_code: Aircraft type code to add.

        Returns:
            True if added, False if group doesn't exist or code already in group.
        """
        if group_name not in self.groups:
            logger.warning(f"Group '{group_name}' not found")
            return False

        aircraft_code = aircraft_code.upper()
        if aircraft_code in self.groups[group_name]:
            logger.warning(f"Aircraft code {aircraft_code} already in group {group_name}")
            return False

        self.groups[group_name].append(aircraft_code)
        self.save()
        logger.info(f"Added {aircraft_code} to group {group_name}")
        return True

    def remove_from_group(self, group_name: str, aircraft_code: str) -> bool:
        """
        Remove an aircraft code from a group.

        Args:
            group_name: Name of the group.
            aircraft_code: Aircraft type code to remove.

        Returns:
            True if removed, False if group doesn't exist or code not in group.
        """
        if group_name not in self.groups:
            logger.warning(f"Group '{group_name}' not found")
            return False

        aircraft_code = aircraft_code.upper()
        if aircraft_code not in self.groups[group_name]:
            logger.warning(f"Aircraft code {aircraft_code} not in group {group_name}")
            return False

        self.groups[group_name].remove(aircraft_code)
        self.save()
        logger.info(f"Removed {aircraft_code} from group {group_name}")
        return True

    def delete_group(self, group_name: str) -> bool:
        """
        Delete a group.

        Args:
            group_name: Name of the group to delete.

        Returns:
            True if deleted, False if not found.
        """
        if group_name not in self.groups:
            logger.warning(f"Group '{group_name}' not found")
            return False

        del self.groups[group_name]
        self.save()
        logger.info(f"Deleted group: {group_name}")
        return True

    # Glossary management methods
    def get_aircraft_type(self, code: str) -> Optional[AircraftType]:
        """Get an aircraft type from the glossary."""
        return self.glossary.get(code.upper())

    def add_aircraft_type(self, aircraft: AircraftType) -> bool:
        """
        Add an aircraft type to the glossary.

        Args:
            aircraft: The aircraft type to add.

        Returns:
            True if added, False if already exists.
        """
        if aircraft.code in self.glossary:
            logger.warning(f"Aircraft type {aircraft.code} already exists")
            return False

        self.glossary[aircraft.code] = aircraft
        self.save()
        logger.info(f"Added aircraft type: {aircraft.code}")
        return True

    def update_aircraft_type(self, code: str, **kwargs) -> bool:
        """
        Update an aircraft type's details.

        Args:
            code: Aircraft type code to update.
            **kwargs: Fields to update (make, model, notes).

        Returns:
            True if updated, False if not found.
        """
        aircraft = self.get_aircraft_type(code)
        if not aircraft:
            logger.warning(f"Aircraft type {code} not found")
            return False

        for key, value in kwargs.items():
            if hasattr(aircraft, key):
                setattr(aircraft, key, value)

        self.save()
        logger.info(f"Updated aircraft type: {code}")
        return True

    def remove_aircraft_type(self, code: str) -> bool:
        """
        Remove an aircraft type from the glossary.

        Args:
            code: Aircraft type code to remove.

        Returns:
            True if removed, False if not found.
        """
        code = code.upper()
        if code not in self.glossary:
            logger.warning(f"Aircraft type {code} not found")
            return False

        del self.glossary[code]
        self.save()
        logger.info(f"Removed aircraft type: {code}")
        return True

    def list_all_types(self) -> List[AircraftType]:
        """Get all aircraft types in the glossary."""
        return list(self.glossary.values())

    def search_types(self, query: str) -> List[AircraftType]:
        """
        Search for aircraft types by code, make, or model.

        Args:
            query: Search string.

        Returns:
            List of matching aircraft types.
        """
        query = query.lower()
        results = []
        for aircraft in self.glossary.values():
            if (query in aircraft.code.lower() or
                query in aircraft.make.lower() or
                query in aircraft.model.lower() or
                query in aircraft.notes.lower()):
                results.append(aircraft)
        return results
