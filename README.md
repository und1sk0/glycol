# Glycol

Real-time airport flight monitor built on the [OpenSky Network](https://opensky-network.org/) API. Glycol tracks aircraft around configured airports, detects takeoff and landing events, and logs them for review or CSV export.

## Features

- Monitor aircraft state vectors within a 5 NM radius of 2000+ US airports
- Automatic detection of takeoff and landing events
- Three filtering modes:
  - **Mode A** - Filter by ICAO24 address or callsign
  - **Mode B** - Filter by aircraft category code
  - **Mode C** - Monitor all traffic (default)
- Tkinter GUI with real-time aircraft table and event log
- CSV export of recorded events
- OAuth2 authentication with automatic token refresh
- API rate limit handling with backoff

## Requirements

- Python 3.10+
- An [OpenSky Network](https://opensky-network.org/) account with API credentials (client ID and secret)
- tkinter (included with most Python installations)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Launch with defaults (select airport in the GUI)
python -m glycol

# Specify an airport
python -m glycol --airport KSFO

# Filter by ICAO24 addresses or callsigns
python -m glycol --airport KJFK --mode A --filter "A1B2C3,N456CD"

# Filter by aircraft category
python -m glycol --airport KORD --mode B --filter "7"
```

On launch, a dialog will prompt for your OpenSky client ID and client secret. These are used for OAuth2 authentication against the OpenSky API.

### GUI Controls

- **Airport ICAO** - Airport code to monitor (e.g. KSFO, KJFK, KLAX)
- **Mode** - Filter mode (A, B, or C)
- **Filter** - Comma-separated values for modes A and B
- **Poll Interval** - How often to query the API (5-120 seconds, default 10)

The status bar shows authentication state, API rate limit info, and event count. Use the menu to update credentials, save events to CSV, or quit.

## Supported Airports

Includes 2000+ US airports (commercial, military, GA, and heliports) sourced from the OurAirports dataset. Covers all ICAO-coded airports in the US and territories (GU, PR, VI, AS, MP). See `glycol/data/us_airports.json` for the full list.

## Project Structure

```
glycol/
  __main__.py   # Entry point
  main.py       # CLI argument parsing
  api.py        # OpenSky REST API client
  auth.py       # OAuth2 token management
  monitor.py    # Takeoff/landing event detection
  airports.py   # Airport database and bounding box math
  ui.py         # Tkinter GUI
  events.py     # Event storage and CSV export
  data/         # Airport database (us_airports.json)
```
