# Glycol

Real-time airport flight monitor built on the [OpenSky Network](https://opensky-network.org/) API. Glycol tracks aircraft around configured airports, detects takeoff and landing events, and logs them for review or CSV export.

## Features

- Monitor aircraft state vectors within a 5 NM radius of 2000+ US airports
- Automatic detection of takeoff and landing events
- Three filtering options:
  - **Aircraft filter** (`--aircraft`) - Filter by ICAO24 address or tail number
  - **Type group filter** (`--group`) - Filter by aircraft type group name (passenger, cargo, etc.)
  - **All traffic** (default) - Monitor all traffic
- **Two interfaces available:**
  - **Web Interface** - Modern browser-based UI with real-time updates
  - **Desktop GUI** - Tkinter GUI for standalone desktop use
- **Clickable ICAO24 links** - Double-click aircraft or click event log links to view on ADSB-Exchange
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

### Web Interface (Recommended)

For a modern browser-based experience with real-time updates:

```bash
# Quick start
./start_web.sh

# Or manually
python web_server.py
```

Then open your browser to `http://127.0.0.1:8666`

See [WEB_README.md](WEB_README.md) for detailed web interface documentation.

## Deployment

### Docker

Run Glycol in a container with Docker or Docker Compose:

```bash
# Build the image
docker build -t glycol-web:2.1.1 .

# Run with Docker
docker run -d \
  --name glycol-web \
  -p 8666:8666 \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  glycol-web:2.1.1

# Or use Docker Compose
docker compose up -d
```

See [DOCKER.md](DOCKER.md) for comprehensive Docker deployment documentation.

### Kubernetes

Deploy to Kubernetes using Helm (recommended) or raw manifests:

```bash
# Using Helm
helm install glycol ./charts/glycol \
  --set credentials.clientId=YOUR_CLIENT_ID \
  --set credentials.clientSecret=YOUR_CLIENT_SECRET

# Using kubectl
kubectl apply -f k8s/

# Access via port-forward
kubectl port-forward -n glycol svc/glycol 8666:8666
```

See [charts/glycol/README.md](charts/glycol/README.md) for Helm documentation or [k8s/README.md](k8s/README.md) for kubectl deployment.

### Desktop GUI

For a traditional desktop application:

#### Running in Foreground

```bash
# Launch with defaults (select airport in the GUI)
python -m glycol

# Specify an airport
python -m glycol --airport KSFO

# Filter by ICAO24 addresses or tail numbers
python -m glycol --airport KJFK --aircraft "A1B2C3,N456CD"

# Filter by aircraft type group
python -m glycol --airport KORD --group "passenger"

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
- **Filter** - Choose between All Traffic, Aircraft, or Type Group
- **Value** - Comma-separated ICAO24/tail numbers for Aircraft filter, or type group name for Type Group filter
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

## Database Management

Glycol includes an interactive database manager for tracking planes of interest and aircraft type groups. Run `python manage.py` without arguments to enter interactive mode, or use CLI commands for scripting.

### Interactive Mode

```bash
# Launch interactive menu
python manage.py

# Or explicitly
python manage.py --interactive
```

The interactive menu provides guided workflows for:
- **Planes of Interest (POI)** - Track specific aircraft with custom metadata
- **Type Groups** - Organize aircraft types into categories (passenger, cargo, military, etc.)
- **Aircraft Glossary** - Browse and search the database of 100+ aircraft type codes

### Planes of Interest (POI)

Track specific aircraft with custom metadata. Supports multiple categories for organizing different collections.

```bash
# CLI commands
python manage.py poi list                    # List all tracked planes
python manage.py poi categories              # List POI categories
python manage.py --category example poi list # Use specific category
python manage.py poi add N12345 --name "My Plane" --icao24 abc123 \
  --model "Cessna 172" --notes "Friend's plane"
python manage.py poi get N12345              # Get plane details
```

Database: `glycol/data/planes_of_interest.json`
- **tailnumber** (required) - Aircraft registration
- **name** (optional) - Aircraft name/identifier
- **icao24** (optional) - ICAO24 hex address
- **make_model** (optional) - Aircraft type
- **notes** (optional) - Additional information

### Type Groups

Pre-populated type groups of aircraft type codes for filtering operations:

```bash
# CLI commands
python manage.py groups list                 # List all type groups
python manage.py groups view passenger       # View passenger aircraft type codes
python manage.py groups view military_fighter # View military fighter type codes
```

**Available type groups:**
- **passenger** - Commercial airliners (A380, 777, 737, A320, etc.)
- **cargo** - Freighter aircraft (747F, 777F, MD-11F, etc.)
- **military_fighter** - Fighter aircraft (F-16, F-15, F-18, F-22, F-35, etc.)
- **military_transport** - Military transports (C-130, C-17, KC-135, etc.)
- **coast_guard** - Coast Guard aircraft
- **business_jet** - Corporate jets (Gulfstream, Falcon, Citation, etc.)
- **general_aviation** - GA aircraft (Cessna, Piper, Cirrus, etc.)
- **helicopter** - Rotary-wing aircraft

### Aircraft Glossary

Searchable database of 100+ aircraft type codes with make, model, and notes:

```bash
# CLI commands
python manage.py glossary list               # List all aircraft types
python manage.py glossary get B77W           # Get specific type
python manage.py glossary search "737"       # Search by keyword
```

**Example entries:**
- **B77W** - Boeing 777-300ER (Long-range wide-body twin-engine)
- **A388** - Airbus A380-800 (Double-deck wide-body)
- **F22** - Lockheed Martin F-22 Raptor (Stealth air superiority fighter)

Database: `glycol/data/type_groups.json`

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
  groups.py              # Aircraft type groups and glossary management
  data/
    us_airports.json          # Airport database (2000+ US airports)
    planes_of_interest.json   # POI database
    type_groups.json          # Aircraft type groups and glossary

glycol.sh     # Background launcher script
manage.py     # Interactive database manager (POI, type groups, glossary)
logs/         # Application logs (JSON format)
```
