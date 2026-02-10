"""
Glycol - Real-time airport flight monitor.

Track aircraft around configured airports, detect takeoff and landing events,
and manage planes of interest with the OpenSky Network API.
"""

__version__ = "1.3.0"
__author__ = "Glycol Project"
__license__ = "MIT"

from glycol.poi import POIDatabase, PlaneOfInterest
from glycol.typegroups import TypeGroupsDatabase, AircraftType

__all__ = [
    "POIDatabase",
    "PlaneOfInterest",
    "TypeGroupsDatabase",
    "AircraftType",
    "__version__",
]
