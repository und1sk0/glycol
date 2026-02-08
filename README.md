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
- **Background launcher** - Run glycol as a background process with automatic logging
- **JSON structured logging** - Machine-readable logs with timestamps and metadata
- **Planes of Interest database** - Track specific aircraft with custom metadata

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

### Credentials

On first launch, Glycol will prompt for your OpenSky Network credentials. You can also create a `glycol/data/credentials.json` file to automatically authenticate:

```json
{
  "clientId": "your-client-id",
  "clientSecret": "your-client-secret"
}
```

If this file exists and has valid credentials, Glycol will use them automatically on startup.

## Usage

### Running in Foreground

```bash
# Launch with defaults (select airport in the GUI)
python -m glycol

# Specify an airport
python -m glycol --airport KSFO

# Filter by ICAO24 addresses or callsigns
python -m glycol --airport KJFK --mode A --filter "A1B2C3,N456CD"

# Filter by aircraft category
python -m glycol --airport KORD --mode B --filter "7"

# Specify custom log file
python -m glycol --airport KSFO --log my-session.log

# Use custom directories for logs and data
python -m glycol --logs-dir /path/to/logs --data-dir /path/to/data
```

### Running in Background

Use the launcher script to run glycol as a background process:

```bash
# Launch in background with auto-generated timestamped log
./glycol.sh --airport KSFO

# Launch with custom log file
./glycol.sh --airport KSFO --log my-session.log

# Stop background process
ps aux | grep "python -m glycol"
kill <PID>
```

The launcher automatically activates the virtual environment and detaches the process from your terminal.

If credentials are not found in `glycol/data/credentials.json`, a dialog will prompt for your OpenSky client ID and client secret. These are used for OAuth2 authentication against the OpenSky API.

### GUI Controls

- **Airport ICAO** - Airport code to monitor (e.g. KSFO, KJFK, KLAX)
- **Mode** - Filter mode (A, B, or C)
- **Filter** - Comma-separated values for modes A and B
- **Poll Interval** - How often to query the API (5-120 seconds, default 10)

The status bar shows authentication state, API rate limit info, and event count. Use the menu to update credentials, save events to CSV, or quit.

## Logging

Glycol uses structured JSON logging for easy parsing and analysis:

- Logs are stored in `logs/` directory
- Default format: `glycol-YYYYMMDD:HH:mm-<random>.log`
- Each log entry is a JSON object with timestamp, level, message, and metadata
- Console output remains human-readable

**Parse logs with jq:**
```bash
# View all ERROR level logs
cat logs/glycol-*.log | jq 'select(.level == "ERROR")'

# Extract just messages
cat logs/glycol-*.log | jq -r '.message'

# Filter by timestamp
cat logs/glycol-*.log | jq 'select(.timestamp > "2026-02-08")'
```

## Planes of Interest

Track specific aircraft with custom metadata using the POI database:

```bash
# List all tracked planes
python manage_poi.py list

# Add a plane (only tail number required)
python manage_poi.py add N12345 --name "My Plane" --icao24 abc123 \
  --model "Cessna 172" --notes "Friend's plane"

# Get plane details
python manage_poi.py get N12345

# Update a plane
python manage_poi.py update N12345 --notes "Updated information"

# Remove a plane
python manage_poi.py remove N12345

# Use custom data directory
python manage_poi.py --data-dir /path/to/data list
```

The database is stored in `glycol/data/planes_of_interest.json` and includes fields for:
- **tailnumber** (required) - Aircraft registration
- **name** (optional) - Aircraft name/identifier
- **icao24** (optional) - ICAO24 hex address
- **make_model** (optional) - Aircraft type
- **notes** (optional) - Additional information

## Supported Airports

Includes 2000+ US airports (commercial, military, GA, and heliports) sourced from the OurAirports dataset. Covers all ICAO-coded airports in the US and territories (GU, PR, VI, AS, MP). See `glycol/data/us_airports.json` for the full list.

## Project Structure

```
glycol/
  __main__.py            # Entry point
  main.py                # CLI argument parsing and logging setup
  api.py                 # OpenSky REST API client
  auth.py                # OAuth2 token management
  monitor.py             # Takeoff/landing event detection
  airports.py            # Airport database and bounding box math
  ui.py                  # Tkinter GUI
  events.py              # Event storage and CSV export
  poi.py                 # Planes of Interest database management
  data/
    us_airports.json     # Airport database

glycol.sh                         # Background launcher script
manage_poi.py                     # CLI for managing planes of interest
logs/                             # Application logs (JSON format)
glycol/data/planes_of_interest.json  # POI database
```
