import math

# ICAO code -> (latitude, longitude, name)
AIRPORTS: dict[str, tuple[float, float, str]] = {
    # Major US commercial
    "KATL": (33.6407, -84.4277, "Hartsfield-Jackson Atlanta"),
    "KBOS": (42.3656, -71.0096, "Boston Logan"),
    "KDEN": (39.8561, -104.6737, "Denver International"),
    "KDFW": (32.8998, -97.0403, "Dallas/Fort Worth"),
    "KDTW": (42.2124, -83.3534, "Detroit Metropolitan"),
    "KEWR": (40.6895, -74.1745, "Newark Liberty"),
    "KIAH": (29.9902, -95.3368, "Houston Intercontinental"),
    "KJFK": (40.6413, -73.7781, "John F. Kennedy"),
    "KLAX": (33.9416, -118.4085, "Los Angeles International"),
    "KLGA": (40.7769, -73.8740, "LaGuardia"),
    "KMCO": (28.4312, -81.3081, "Orlando International"),
    "KMIA": (25.7959, -80.2870, "Miami International"),
    "KMSP": (44.8848, -93.2223, "Minneapolis-Saint Paul"),
    "KORD": (41.9742, -87.9073, "Chicago O'Hare"),
    "KPHL": (39.8744, -75.2424, "Philadelphia International"),
    "KPHX": (33.4373, -112.0078, "Phoenix Sky Harbor"),
    "KSEA": (47.4502, -122.3088, "Seattle-Tacoma"),
    "KSFO": (37.6213, -122.3790, "San Francisco International"),
    "KSLC": (40.7899, -111.9791, "Salt Lake City"),
    "KTPA": (27.9755, -82.5332, "Tampa International"),
    "KDCA": (38.8512, -77.0402, "Ronald Reagan Washington"),
    "KIAD": (38.9531, -77.4565, "Washington Dulles"),
    "KLAS": (36.0840, -115.1537, "Las Vegas McCarran"),
    "KSAN": (32.7338, -117.1933, "San Diego International"),
    "KSTL": (38.7487, -90.3700, "St. Louis Lambert"),
    "KCLT": (35.2140, -80.9431, "Charlotte Douglas"),
    "KBWI": (39.1754, -76.6684, "Baltimore/Washington"),
    "KMDW": (41.7868, -87.7522, "Chicago Midway"),
    "KFLL": (26.0742, -80.1506, "Fort Lauderdale-Hollywood"),
    "KAUS": (30.1975, -97.6664, "Austin-Bergstrom"),
    "KSJC": (37.3626, -121.9290, "San Jose International"),
    "KOAK": (37.7213, -122.2208, "Oakland International"),
    "KPDX": (45.5898, -122.5951, "Portland International"),
    "KRDU": (35.8776, -78.7875, "Raleigh-Durham"),
    "KBNA": (36.1263, -86.6774, "Nashville International"),
    # Notable military / government
    "KNUQ": (37.4161, -122.0490, "Moffett Federal Airfield"),
    "KFFO": (39.8261, -84.0483, "Wright-Patterson AFB"),
    "KADW": (38.8108, -76.8670, "Joint Base Andrews"),
    "KLFI": (37.0830, -76.3605, "Langley AFB"),
    "KEDW": (34.9054, -117.8839, "Edwards AFB"),
    "KNKX": (32.8684, -117.1426, "MCAS Miramar"),
    "KNGP": (27.6926, -97.2911, "NAS Corpus Christi"),
    "KNZY": (32.6992, -117.2153, "NAS North Island"),
    "KBLV": (38.5452, -89.8352, "Scott AFB / MidAmerica"),
    "KWRI": (40.0156, -74.5936, "Joint Base McGuire-Dix"),
    "KDOV": (39.1301, -75.4660, "Dover AFB"),
    "KNTU": (36.8206, -76.0335, "NAS Oceana"),
    "KOFF": (41.1183, -95.9125, "Offutt AFB"),
    "KTIK": (35.4147, -97.3866, "Tinker AFB"),
    "KSKF": (29.3842, -98.5811, "Lackland AFB / Kelly Field"),
    # European
    "EGLL": (51.4700, -0.4543, "London Heathrow"),
    "LFPG": (49.0097, 2.5479, "Paris Charles de Gaulle"),
    "EDDF": (50.0379, 8.5622, "Frankfurt"),
    "EHAM": (52.3105, 4.7683, "Amsterdam Schiphol"),
    "LEMD": (40.4983, -3.5676, "Madrid Barajas"),
    # Asia-Pacific
    "RJTT": (35.5533, 139.7811, "Tokyo Haneda"),
    "VHHH": (22.3080, 113.9185, "Hong Kong International"),
    "WSSS": (1.3644, 103.9915, "Singapore Changi"),
    "YSSY": (-33.9461, 151.1772, "Sydney Kingsford Smith"),
}


NM_TO_DEG_LAT = 1.0 / 60.0  # 1 nautical mile ≈ 1/60 degree latitude


def get_bounding_box(
    icao_code: str,
    radius_nm: float = 5.0,
    lat: float | None = None,
    lon: float | None = None,
) -> tuple[float, float, float, float] | None:
    """Return (lamin, lamax, lomin, lomax) for the given airport and radius.

    If the ICAO code is in the known dict, its coordinates are used.
    Otherwise, *lat* and *lon* must be supplied.
    Returns None when coordinates cannot be determined.
    """
    if icao_code.upper() in AIRPORTS:
        lat, lon, _ = AIRPORTS[icao_code.upper()]
    if lat is None or lon is None:
        return None

    dlat = radius_nm * NM_TO_DEG_LAT
    # Longitude degrees per NM varies with latitude
    dlon = radius_nm * NM_TO_DEG_LAT / math.cos(math.radians(lat))

    return (lat - dlat, lat + dlat, lon - dlon, lon + dlon)


def airport_name(icao_code: str) -> str:
    """Return the human-readable name, or the code itself if unknown."""
    entry = AIRPORTS.get(icao_code.upper())
    return entry[2] if entry else icao_code.upper()
